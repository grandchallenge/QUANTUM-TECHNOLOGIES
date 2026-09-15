// Exact scalar evaluator for the compact-native C90 semantic DAG.
//
// The evaluator fixes one frozen selector coordinate at a time, follows only
// the selected I-node branches, and evaluates the retained exact semiring DAG
// in topological order. It does not alter the compiled representation. Storage
// is reusable across selectors; reference counts release scalar slots at last
// use. No approximation, pruning of a selected branch, decoder outcome, or
// injected-error information is used.

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

namespace {

constexpr uint32_t NONE = std::numeric_limits<uint32_t>::max();
constexpr uint8_t K_T = 0;
constexpr uint8_t K_I = 1;
constexpr uint8_t K_S = 2;
constexpr uint8_t K_MUL = 3;
constexpr uint8_t K_ADD = 4;
constexpr uint8_t K_MPMUL = 5;
constexpr uint8_t K_MPMIN = 6;
constexpr uint32_t VALUE_CHUNK_BITS = 18; // 262144 x 48 B = 12 MiB/chunk.
constexpr uint32_t VALUE_CHUNK_SIZE = 1U << VALUE_CHUNK_BITS;
constexpr uint32_t VALUE_CHUNK_MASK = VALUE_CHUNK_SIZE - 1U;

#pragma pack(push, 1)
struct Node {
    uint8_t kind;
    uint32_t a;
    uint32_t b;
    uint32_t c;
};
#pragma pack(pop)
static_assert(sizeof(Node) == 13, "packed node must remain 13 bytes");

#pragma pack(push, 1)
struct Header {
    char magic[8];
    uint32_t algebra_id;
    uint64_t count;
    uint32_t root;
};
#pragma pack(pop)
static_assert(sizeof(Header) == 24, "native header size drift");

struct Value {
    std::array<uint64_t, 6> limb{};
};
static_assert(sizeof(Value) == 48, "exact scalar slot size drift");

bool is_binary(uint8_t kind) {
    return kind == K_MUL || kind == K_ADD || kind == K_MPMUL || kind == K_MPMIN;
}

class MappedFile {
public:
    explicit MappedFile(const std::string& path) {
        fd_ = ::open(path.c_str(), O_RDONLY);
        if (fd_ < 0) throw std::runtime_error("cannot open native binary");
        struct stat st{};
        if (::fstat(fd_, &st) != 0) throw std::runtime_error("cannot stat native binary");
        if (st.st_size < static_cast<off_t>(sizeof(Header))) throw std::runtime_error("native binary truncated");
        size_ = static_cast<size_t>(st.st_size);
        data_ = static_cast<const uint8_t*>(::mmap(nullptr, size_, PROT_READ, MAP_PRIVATE, fd_, 0));
        if (data_ == MAP_FAILED) {
            data_ = nullptr;
            throw std::runtime_error("cannot mmap native binary");
        }
    }
    ~MappedFile() {
        if (data_) ::munmap(const_cast<uint8_t*>(data_), size_);
        if (fd_ >= 0) ::close(fd_);
    }
    const uint8_t* data() const { return data_; }
    size_t size() const { return size_; }
private:
    int fd_ = -1;
    const uint8_t* data_ = nullptr;
    size_t size_ = 0;
};

Header read_header(const MappedFile& file) {
    Header h{};
    std::memcpy(&h, file.data(), sizeof(h));
    const char expected[8] = {'Q','T','R','C','9','0','N','1'};
    if (std::memcmp(h.magic, expected, 8) != 0) throw std::runtime_error("native magic drift");
    if (h.algebra_id > 2) throw std::runtime_error("native algebra id drift");
    if (h.count == 0 || h.count > std::numeric_limits<uint32_t>::max()) throw std::runtime_error("native count drift");
    if (h.root >= h.count) throw std::runtime_error("native root drift");
    const uint64_t expected_size = sizeof(Header) + h.count * sizeof(Node);
    if (expected_size != file.size()) throw std::runtime_error("native binary size drift");
    return h;
}

inline Node read_node(const MappedFile& file, uint32_t id) {
    Node n{};
    const size_t offset = sizeof(Header) + static_cast<size_t>(id) * sizeof(Node);
    std::memcpy(&n, file.data() + offset, sizeof(Node));
    return n;
}

struct SelectorRow {
    uint32_t index = 0;
    uint64_t coordinate = 0;
};

std::vector<SelectorRow> read_selectors(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open selector file");
    std::vector<SelectorRow> rows;
    SelectorRow row{};
    while (in >> row.index >> row.coordinate) {
        if (row.coordinate >= (1ULL << 49)) throw std::runtime_error("selector coordinate exceeds frozen rank");
        rows.push_back(row);
    }
    if (rows.empty()) throw std::runtime_error("selector file is empty");
    return rows;
}

inline bool bit_get(const std::vector<uint64_t>& bits, uint32_t id) {
    return (bits[id >> 6] >> (id & 63U)) & 1ULL;
}
inline void bit_set(std::vector<uint64_t>& bits, uint32_t id) {
    bits[id >> 6] |= 1ULL << (id & 63U);
}

class ValuePool {
public:
    uint32_t allocate() {
        if (!free_.empty()) {
            const uint32_t id = free_.back();
            free_.pop_back();
            value(id) = Value{};
            ++live_;
            peak_live_ = std::max<uint64_t>(peak_live_, live_);
            return id;
        }
        const uint32_t id = allocated_++;
        if ((id >> VALUE_CHUNK_BITS) >= chunks_.size()) {
            chunks_.push_back(std::make_unique<Value[]>(VALUE_CHUNK_SIZE));
        }
        value(id) = Value{};
        ++live_;
        peak_live_ = std::max<uint64_t>(peak_live_, live_);
        return id;
    }
    void release(uint32_t id) {
        if (id >= allocated_) throw std::runtime_error("value slot release overflow");
        free_.push_back(id);
        if (live_ == 0) throw std::runtime_error("value pool live underflow");
        --live_;
    }
    Value& value(uint32_t id) {
        if (id >= allocated_ && !(id == allocated_ && (id >> VALUE_CHUNK_BITS) < chunks_.size())) {
            throw std::runtime_error("value slot access overflow");
        }
        return chunks_[id >> VALUE_CHUNK_BITS][id & VALUE_CHUNK_MASK];
    }
    const Value& value(uint32_t id) const {
        if (id >= allocated_) throw std::runtime_error("value slot access overflow");
        return chunks_[id >> VALUE_CHUNK_BITS][id & VALUE_CHUNK_MASK];
    }
    uint64_t live() const { return live_; }
    uint64_t peak_live() const { return peak_live_; }
    uint64_t allocated() const { return allocated_; }
    void reset_peak() { peak_live_ = live_; }
private:
    std::vector<std::unique_ptr<Value[]>> chunks_;
    std::vector<uint32_t> free_;
    uint32_t allocated_ = 0;
    uint64_t live_ = 0;
    uint64_t peak_live_ = 0;
};

void big_add(const Value& x, const Value& y, Value& out) {
    unsigned __int128 carry = 0;
    for (size_t i = 0; i < 6; ++i) {
        const unsigned __int128 cur = static_cast<unsigned __int128>(x.limb[i]) + y.limb[i] + carry;
        out.limb[i] = static_cast<uint64_t>(cur);
        carry = cur >> 64;
    }
    if (carry != 0) throw std::runtime_error("384-bit exact addition overflow");
}

void big_mul(const Value& x, const Value& y, Value& out) {
    std::array<uint64_t, 12> tmp{};
    for (size_t i = 0; i < 6; ++i) {
        unsigned __int128 carry = 0;
        for (size_t j = 0; j < 6; ++j) {
            const size_t k = i + j;
            const unsigned __int128 cur = static_cast<unsigned __int128>(x.limb[i]) * y.limb[j]
                + tmp[k] + carry;
            tmp[k] = static_cast<uint64_t>(cur);
            carry = cur >> 64;
        }
        size_t k = i + 6;
        while (carry != 0 && k < tmp.size()) {
            const unsigned __int128 cur = static_cast<unsigned __int128>(tmp[k]) + carry;
            tmp[k] = static_cast<uint64_t>(cur);
            carry = cur >> 64;
            ++k;
        }
        if (carry != 0) throw std::runtime_error("wide multiplication accumulator overflow");
    }
    for (size_t i = 6; i < 12; ++i) {
        if (tmp[i] != 0) throw std::runtime_error("384-bit exact multiplication overflow");
    }
    for (size_t i = 0; i < 6; ++i) out.limb[i] = tmp[i];
}

int cmp128(uint64_t alo, uint64_t ahi, uint64_t blo, uint64_t bhi) {
    if (ahi < bhi) return -1;
    if (ahi > bhi) return 1;
    if (alo < blo) return -1;
    if (alo > blo) return 1;
    return 0;
}

void add128(uint64_t alo, uint64_t ahi, uint64_t blo, uint64_t bhi, uint64_t& olo, uint64_t& ohi) {
    const unsigned __int128 lo = static_cast<unsigned __int128>(alo) + blo;
    olo = static_cast<uint64_t>(lo);
    const unsigned __int128 hi = static_cast<unsigned __int128>(ahi) + bhi + static_cast<uint64_t>(lo >> 64);
    ohi = static_cast<uint64_t>(hi);
    if ((hi >> 64) != 0) throw std::runtime_error("128-bit min-plus integer overflow");
}

Value terminal_value(uint32_t algebra, uint32_t code) {
    Value out{};
    if (algebra == 0) {
        if (code > 1) throw std::runtime_error("sum-product terminal code drift");
        out.limb[0] = code ? 1 : 9;
    } else if (algebra == 1) {
        if (code > 1) throw std::runtime_error("soft-tropical terminal code drift");
        out.limb[0] = code ? 1 : 2;
    } else {
        if (code == 0) return out;
        const uint32_t qubit = code - 1;
        if (qubit >= 90) throw std::runtime_error("min-plus terminal code drift");
        out.limb[0] = 1; // weight
        if (qubit < 64) {
            out.limb[1] = 1ULL << qubit;
            out.limb[3] = 1ULL << qubit;
        } else {
            out.limb[2] = 1ULL << (qubit - 64);
            out.limb[4] = 1ULL << (qubit - 64);
        }
    }
    return out;
}

void minplus_mul(const Value& x, const Value& y, Value& out) {
    const uint64_t weight = x.limb[0] + y.limb[0];
    if (weight > 90) throw std::runtime_error("min-plus weight overflow");
    out.limb[0] = weight;
    add128(x.limb[1], x.limb[2], y.limb[1], y.limb[2], out.limb[1], out.limb[2]);
    add128(x.limb[3], x.limb[4], y.limb[3], y.limb[4], out.limb[3], out.limb[4]);
    out.limb[5] = 0;
}

void minplus_min(const Value& x, const Value& y, Value& out) {
    bool choose_x = false;
    if (x.limb[0] < y.limb[0]) choose_x = true;
    else if (x.limb[0] == y.limb[0]) {
        choose_x = cmp128(x.limb[1], x.limb[2], y.limb[1], y.limb[2]) <= 0;
    }
    const Value& primary = choose_x ? x : y;
    out.limb[0] = primary.limb[0];
    out.limb[1] = primary.limb[1];
    out.limb[2] = primary.limb[2];
    const bool canonical_x = cmp128(x.limb[3], x.limb[4], y.limb[3], y.limb[4]) <= 0;
    const Value& canonical = canonical_x ? x : y;
    out.limb[3] = canonical.limb[3];
    out.limb[4] = canonical.limb[4];
    out.limb[5] = 0;
}

std::string hex_limbs(const uint64_t* limbs, size_t count) {
    size_t top = count;
    while (top > 0 && limbs[top - 1] == 0) --top;
    if (top == 0) return "0x0";
    std::ostringstream out;
    out << "0x" << std::hex << std::nouppercase << limbs[top - 1];
    for (size_t i = top - 1; i-- > 0;) {
        out << std::setw(16) << std::setfill('0') << limbs[i];
    }
    return out.str();
}

class Evaluator {
public:
    explicit Evaluator(const std::string& path)
        : file_(path), header_(read_header(file_)), count_(static_cast<uint32_t>(header_.count)),
          seen_((static_cast<uint64_t>(count_) + 63ULL) / 64ULL, 0), refs_(count_, 0), slots_(count_, NONE) {
        stack_.reserve(1024);
    }

    const Header& header() const { return header_; }

    Value evaluate(uint64_t coordinate, uint64_t& reachable, uint64_t& peak_live) {
        if (coordinate >= (1ULL << 49)) throw std::runtime_error("selector coordinate exceeds frozen rank");
        if (pool_.live() != 0) throw std::runtime_error("value pool not empty at selector start");
        stack_.clear();
        stack_.push_back(header_.root);
        reachable = 0;

        while (!stack_.empty()) {
            const uint32_t id = stack_.back();
            stack_.pop_back();
            if (bit_get(seen_, id)) continue;
            bit_set(seen_, id);
            ++reachable;
            const Node n = read_node(file_, id);
            if (n.kind == K_T) {
                continue;
            } else if (n.kind == K_I) {
                if (n.a >= 49 || n.b >= id || n.c >= id) throw std::runtime_error("selector node drift");
                const uint32_t child = ((coordinate >> n.a) & 1ULL) ? n.c : n.b;
                ++refs_[child];
                if (!bit_get(seen_, child)) stack_.push_back(child);
            } else if (n.kind == K_S) {
                throw std::runtime_error("temporary stabilizer node retained in final DAG");
            } else if (is_binary(n.kind)) {
                if (n.a >= id || n.b >= id) throw std::runtime_error("binary child order drift");
                ++refs_[n.a];
                ++refs_[n.b];
                if (!bit_get(seen_, n.a)) stack_.push_back(n.a);
                if (!bit_get(seen_, n.b)) stack_.push_back(n.b);
            } else {
                throw std::runtime_error("unknown node kind");
            }
        }

        pool_.reset_peak();
        for (size_t word_index = 0; word_index < seen_.size(); ++word_index) {
            uint64_t word = seen_[word_index];
            while (word != 0) {
                const uint32_t bit = static_cast<uint32_t>(__builtin_ctzll(word));
                const uint64_t raw_id = static_cast<uint64_t>(word_index) * 64ULL + bit;
                if (raw_id >= count_) break;
                const uint32_t id = static_cast<uint32_t>(raw_id);
                const Node n = read_node(file_, id);
                const uint32_t slot = pool_.allocate();
                Value& out = pool_.value(slot);
                if (n.kind == K_T) {
                    out = terminal_value(header_.algebra_id, n.a);
                } else if (n.kind == K_I) {
                    const uint32_t child = ((coordinate >> n.a) & 1ULL) ? n.c : n.b;
                    const uint32_t child_slot = slots_[child];
                    if (child_slot == NONE) throw std::runtime_error("selector child value missing");
                    out = pool_.value(child_slot);
                    release_edge(child);
                } else if (n.kind == K_S) {
                    throw std::runtime_error("temporary stabilizer node reached evaluation");
                } else if (is_binary(n.kind)) {
                    const uint32_t left_slot = slots_[n.a];
                    const uint32_t right_slot = slots_[n.b];
                    if (left_slot == NONE || right_slot == NONE) throw std::runtime_error("binary child value missing");
                    const Value left = pool_.value(left_slot);
                    const Value right = pool_.value(right_slot);
                    if (header_.algebra_id < 2) {
                        if (n.kind == K_MUL) big_mul(left, right, out);
                        else if (n.kind == K_ADD) big_add(left, right, out);
                        else throw std::runtime_error("numeric algebra operation drift");
                    } else {
                        if (n.kind == K_MPMUL) minplus_mul(left, right, out);
                        else if (n.kind == K_MPMIN) minplus_min(left, right, out);
                        else throw std::runtime_error("min-plus algebra operation drift");
                    }
                    release_edge(n.a);
                    release_edge(n.b);
                }
                slots_[id] = slot;
                word &= word - 1;
            }
            seen_[word_index] = 0;
        }

        const uint32_t root_slot = slots_[header_.root];
        if (root_slot == NONE) throw std::runtime_error("root value missing");
        Value result = pool_.value(root_slot);
        if (refs_[header_.root] != 0) throw std::runtime_error("root reference count drift");
        pool_.release(root_slot);
        slots_[header_.root] = NONE;
        if (pool_.live() != 0) throw std::runtime_error("live values remain after selector evaluation");
        peak_live = pool_.peak_live();
        return result;
    }

private:
    void release_edge(uint32_t child) {
        if (refs_[child] == 0) throw std::runtime_error("reference underflow");
        --refs_[child];
        if (refs_[child] == 0) {
            const uint32_t slot = slots_[child];
            if (slot == NONE) throw std::runtime_error("released child slot missing");
            pool_.release(slot);
            slots_[child] = NONE;
        }
    }

    MappedFile file_;
    Header header_{};
    uint32_t count_ = 0;
    std::vector<uint64_t> seen_;
    std::vector<uint32_t> refs_;
    std::vector<uint32_t> slots_;
    std::vector<uint32_t> stack_;
    ValuePool pool_;
};

void print_result(const Header& h, const SelectorRow& row, const Value& value, uint64_t reachable, uint64_t peak_live) {
    std::cout << "{\"status\":\"C90_COMPACT_NATIVE_SELECTOR_EVALUATED\""
              << ",\"algebra_id\":" << h.algebra_id
              << ",\"selector_index\":" << row.index
              << ",\"selector_coordinate\":" << row.coordinate
              << ",\"reachable_nodes\":" << reachable
              << ",\"peak_live_values\":" << peak_live;
    if (h.algebra_id < 2) {
        std::cout << ",\"value_hex\":\"" << hex_limbs(value.limb.data(), 6) << "\"";
    } else {
        std::cout << ",\"minimum_weight\":" << value.limb[0]
                  << ",\"minimum_representative_hex\":\"" << hex_limbs(value.limb.data() + 1, 2) << "\""
                  << ",\"canonical_hex\":\"" << hex_limbs(value.limb.data() + 3, 2) << "\"";
    }
    std::cout << ",\"quality_exposed\":false}" << std::endl;
}

void run(const std::string& native_path, const std::string& selectors_path) {
    Evaluator evaluator(native_path);
    const std::vector<SelectorRow> rows = read_selectors(selectors_path);
    for (const SelectorRow& row : rows) {
        uint64_t reachable = 0;
        uint64_t peak_live = 0;
        const Value value = evaluator.evaluate(row.coordinate, reachable, peak_live);
        print_result(evaluator.header(), row, value, reachable, peak_live);
    }
}

} // namespace

int main(int argc, char** argv) {
    try {
        std::string native_path;
        std::string selectors_path;
        for (int i = 1; i < argc; ++i) {
            const std::string arg = argv[i];
            if (arg == "--native" && i + 1 < argc) native_path = argv[++i];
            else if (arg == "--selectors" && i + 1 < argc) selectors_path = argv[++i];
            else throw std::runtime_error("usage: --native PATH --selectors PATH");
        }
        if (native_path.empty() || selectors_path.empty()) {
            throw std::runtime_error("usage: --native PATH --selectors PATH");
        }
        run(native_path, selectors_path);
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "QTR_C90_NATIVE_EVAL_ERROR: " << e.what() << std::endl;
        return 2;
    }
}
