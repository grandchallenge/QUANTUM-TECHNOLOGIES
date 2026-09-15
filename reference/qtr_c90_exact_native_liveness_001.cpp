// Quality-blind liveness characterization for the compact-native C90 DAG.
//
// This utility does not evaluate decoder quality. It reads the frozen compact
// semantic DAG, follows only selector branches required by a supplied selector
// set, and measures the exact live-node frontier induced by topological
// evaluation. The result is used only to choose an execution batch size for
// semantic validation; it does not alter the scientific representation.

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

namespace {

constexpr uint8_t K_T = 0;
constexpr uint8_t K_I = 1;
constexpr uint8_t K_S = 2;
constexpr uint8_t K_MUL = 3;
constexpr uint8_t K_ADD = 4;
constexpr uint8_t K_MPMUL = 5;
constexpr uint8_t K_MPMIN = 6;

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

Node read_node(const MappedFile& file, uint32_t id) {
    Node n{};
    const size_t offset = sizeof(Header) + static_cast<size_t>(id) * sizeof(Node);
    std::memcpy(&n, file.data() + offset, sizeof(Node));
    return n;
}

std::vector<uint64_t> read_selectors(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open selector file");
    std::vector<uint64_t> selectors;
    uint64_t value = 0;
    while (in >> value) {
        if (value >= (1ULL << 49)) throw std::runtime_error("selector coordinate exceeds frozen rank");
        selectors.push_back(value);
    }
    if (selectors.empty()) throw std::runtime_error("selector file is empty");
    return selectors;
}

inline bool bit_get(const std::vector<uint64_t>& bits, uint32_t id) {
    return (bits[id >> 6] >> (id & 63U)) & 1ULL;
}
inline void bit_set(std::vector<uint64_t>& bits, uint32_t id) {
    bits[id >> 6] |= 1ULL << (id & 63U);
}

struct BranchUse {
    bool low = false;
    bool high = false;
};

std::vector<BranchUse> branch_use(const std::vector<uint64_t>& selectors) {
    std::vector<BranchUse> out(49);
    for (uint32_t p = 0; p < 49; ++p) {
        for (uint64_t coordinate : selectors) {
            if ((coordinate >> p) & 1ULL) out[p].high = true;
            else out[p].low = true;
            if (out[p].low && out[p].high) break;
        }
    }
    return out;
}

void dec_ref(std::vector<uint32_t>& refs, uint32_t child, uint64_t& live) {
    if (refs[child] == 0) throw std::runtime_error("reference underflow");
    --refs[child];
    if (refs[child] == 0) {
        if (live == 0) throw std::runtime_error("live frontier underflow");
        --live;
    }
}

void run(const std::string& native_path, const std::string& selectors_path) {
    MappedFile file(native_path);
    const Header h = read_header(file);
    const uint32_t count = static_cast<uint32_t>(h.count);
    const std::vector<uint64_t> selectors = read_selectors(selectors_path);
    const auto use = branch_use(selectors);

    std::vector<uint64_t> seen((static_cast<uint64_t>(count) + 63ULL) / 64ULL, 0);
    std::vector<uint32_t> refs(count, 0);
    std::vector<uint32_t> stack;
    stack.reserve(1 << 20);
    stack.push_back(h.root);
    uint64_t reachable = 0;
    uint64_t stack_peak = 1;

    while (!stack.empty()) {
        const uint32_t id = stack.back();
        stack.pop_back();
        if (bit_get(seen, id)) continue;
        bit_set(seen, id);
        ++reachable;
        const Node n = read_node(file, id);
        if (n.kind == K_T) {
            // no dependencies
        } else if (n.kind == K_I) {
            if (n.a >= 49 || n.b >= id || n.c >= id) throw std::runtime_error("selector node drift");
            if (use[n.a].low) {
                ++refs[n.b];
                if (!bit_get(seen, n.b)) stack.push_back(n.b);
            }
            if (use[n.a].high) {
                ++refs[n.c];
                if (!bit_get(seen, n.c)) stack.push_back(n.c);
            }
        } else if (n.kind == K_S) {
            throw std::runtime_error("temporary stabilizer node retained in final DAG");
        } else if (is_binary(n.kind)) {
            if (n.a >= id || n.b >= id) throw std::runtime_error("binary child order drift");
            ++refs[n.a];
            ++refs[n.b];
            if (!bit_get(seen, n.a)) stack.push_back(n.a);
            if (!bit_get(seen, n.b)) stack.push_back(n.b);
        } else {
            throw std::runtime_error("unknown node kind");
        }
        stack_peak = std::max<uint64_t>(stack_peak, stack.size());
    }

    uint64_t live = 0;
    uint64_t peak_live = 0;
    uint64_t evaluated = 0;
    for (uint32_t id = 0; id < count; ++id) {
        if (!bit_get(seen, id)) continue;
        const Node n = read_node(file, id);
        ++live;
        ++evaluated;
        peak_live = std::max(peak_live, live);
        if (n.kind == K_I) {
            if (use[n.a].low) dec_ref(refs, n.b, live);
            if (use[n.a].high) dec_ref(refs, n.c, live);
        } else if (is_binary(n.kind)) {
            dec_ref(refs, n.a, live);
            dec_ref(refs, n.b, live);
        }
    }
    if (evaluated != reachable) throw std::runtime_error("reachable/evaluated count drift");
    if (live != 1) throw std::runtime_error("final live frontier must contain only root");

    uint32_t split_parameters = 0;
    for (const auto& item : use) if (item.low && item.high) ++split_parameters;
    std::cout
        << "{\"status\":\"C90_COMPACT_NATIVE_LIVENESS_CHARACTERIZED\""
        << ",\"algebra_id\":" << h.algebra_id
        << ",\"selector_count\":" << selectors.size()
        << ",\"split_selector_parameters\":" << split_parameters
        << ",\"total_nodes\":" << count
        << ",\"reachable_nodes\":" << reachable
        << ",\"peak_live_nodes\":" << peak_live
        << ",\"peak_dfs_stack\":" << stack_peak
        << ",\"quality_exposed\":false}"
        << std::endl;
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
        std::cerr << "QTR_C90_NATIVE_LIVENESS_ERROR: " << e.what() << std::endl;
        return 2;
    }
}
