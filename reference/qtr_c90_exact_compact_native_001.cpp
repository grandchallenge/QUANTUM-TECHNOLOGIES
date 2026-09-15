// Exact compact native hash-cons engine for QTR-C90-EXACT-DECODER-001.
//
// This is a storage/execution backend for the already-frozen shared-symbolic
// compiler. It preserves factor order, protected elimination order, exact
// restriction semantics, commutative operand ordering, selector parameters,
// and final semantic node records. No algebraic rewrite, approximation,
// pruning, reordering, selector enumeration, or quality information is used.

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

constexpr uint32_t NONE = std::numeric_limits<uint32_t>::max();

enum Kind : uint8_t {
    K_T = 0,
    K_I = 1,
    K_S = 2,
    K_MUL = 3,
    K_ADD = 4,
    K_MPMUL = 5,
    K_MPMIN = 6,
};

#pragma pack(push, 1)
struct Node {
    uint8_t kind;
    uint32_t a;
    uint32_t b;
    uint32_t c;
};
#pragma pack(pop)
static_assert(sizeof(Node) == 13, "packed node must remain 13 bytes");

bool node_equal(const Node& x, const Node& y) {
    return x.kind == y.kind && x.a == y.a && x.b == y.b && x.c == y.c;
}

uint64_t mix64(uint64_t x) {
    x += 0x9e3779b97f4a7c15ULL;
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
    return x ^ (x >> 31);
}

uint64_t node_hash(const Node& n) {
    uint64_t h = mix64(static_cast<uint64_t>(n.kind));
    h ^= mix64(static_cast<uint64_t>(n.a) + 0x100000001b3ULL);
    h ^= mix64(static_cast<uint64_t>(n.b) + 0x9e3779b1ULL);
    h ^= mix64(static_cast<uint64_t>(n.c) + 0x85ebca77ULL);
    return mix64(h);
}

bool is_binary(uint8_t kind) {
    return kind == K_MUL || kind == K_ADD || kind == K_MPMUL || kind == K_MPMIN;
}

const char* kind_name(uint8_t kind) {
    switch (kind) {
        case K_T: return "T";
        case K_I: return "I";
        case K_S: return "S";
        case K_MUL: return "MUL";
        case K_ADD: return "ADD";
        case K_MPMUL: return "MPMUL";
        case K_MPMIN: return "MPMIN";
        default: return "?";
    }
}

class Circuit {
public:
    std::vector<Node> nodes;
    std::vector<uint32_t> slots;
    uint64_t created = 0;
    uint64_t reused = 0;
    uint64_t peak_nodes = 0;
    uint64_t stabilizer_nodes = 0;

    Circuit() { reset_table(1024); }

    explicit Circuit(size_t expected_nodes) {
        nodes.reserve(expected_nodes);
        size_t cap = 1024;
        while (cap * 7ULL < std::max<size_t>(1, expected_nodes) * 10ULL) cap <<= 1;
        reset_table(cap);
    }

    uint32_t terminal(uint32_t terminal_code) {
        Node n{K_T, terminal_code, 0, 0};
        return intern(n);
    }

    uint32_t selector_choice(uint32_t parameter, uint32_t low, uint32_t high) {
        if (low == high) return low;
        Node n{K_I, parameter, low, high};
        return intern(n);
    }

    uint32_t stabilizer_choice(uint32_t variable, uint32_t low, uint32_t high) {
        if (low == high) return low;
        Node n{K_S, variable, low, high};
        return intern(n);
    }

    uint32_t binary(uint8_t operation, uint32_t left, uint32_t right) {
        if (!is_binary(operation)) throw std::runtime_error("invalid binary kind");
        if (left > right) std::swap(left, right);
        Node n{operation, left, right, 0};
        return intern(n);
    }

    uint32_t restrict_exact(uint32_t root, uint32_t variable, uint32_t bit) {
        if (bit > 1) throw std::runtime_error("invalid restriction bit");
        const size_t source_size = nodes.size();
        std::vector<uint32_t> memo(source_size, NONE);

        std::function<uint32_t(uint32_t)> visit = [&](uint32_t id) -> uint32_t {
            if (id >= source_size) {
                throw std::runtime_error("restriction traversed newly-created node");
            }
            uint32_t found = memo[id];
            if (found != NONE) return found;
            const Node n = nodes[id];
            uint32_t out = NONE;
            if (n.kind == K_T) {
                out = id;
            } else if (n.kind == K_S) {
                if (n.a == variable) {
                    out = visit(bit ? n.c : n.b);
                } else {
                    const uint32_t low = visit(n.b);
                    const uint32_t high = visit(n.c);
                    out = stabilizer_choice(n.a, low, high);
                }
            } else if (n.kind == K_I) {
                const uint32_t low = visit(n.b);
                const uint32_t high = visit(n.c);
                out = selector_choice(n.a, low, high);
            } else if (is_binary(n.kind)) {
                const uint32_t left = visit(n.a);
                const uint32_t right = visit(n.b);
                out = binary(n.kind, left, right);
            } else {
                throw std::runtime_error("unknown node in restriction");
            }
            memo[id] = out;
            return out;
        };
        return visit(root);
    }

    std::vector<uint32_t> compact(const std::vector<uint32_t>& roots) {
        const size_t old_n = nodes.size();
        std::vector<uint8_t> color(old_n, 0);
        std::vector<uint32_t> order;
        order.reserve(old_n);

        struct Frame { uint32_t id; uint8_t phase; };
        std::vector<Frame> stack;
        stack.reserve(256);

        auto push_root = [&](uint32_t root) {
            if (root >= old_n) throw std::runtime_error("compact root overflow");
            if (color[root] == 2) return;
            stack.push_back({root, 0});
            while (!stack.empty()) {
                Frame& f = stack.back();
                if (f.phase == 0) {
                    if (color[f.id] == 2) { stack.pop_back(); continue; }
                    if (color[f.id] == 1) throw std::runtime_error("cycle in symbolic DAG");
                    color[f.id] = 1;
                    f.phase = 1;
                    const Node n = nodes[f.id];
                    if (n.kind == K_I || n.kind == K_S) {
                        if (color[n.c] == 0) stack.push_back({n.c, 0});
                        if (color[n.b] == 0) stack.push_back({n.b, 0});
                    } else if (is_binary(n.kind)) {
                        if (color[n.b] == 0) stack.push_back({n.b, 0});
                        if (color[n.a] == 0) stack.push_back({n.a, 0});
                    }
                } else {
                    color[f.id] = 2;
                    order.push_back(f.id);
                    stack.pop_back();
                }
            }
        };

        for (uint32_t root : roots) push_root(root);

        std::vector<uint32_t> mapping(old_n, NONE);
        clear_table();
        std::vector<Node> old_nodes;
        old_nodes.swap(nodes);
        std::vector<Node> rebuilt;
        rebuilt.reserve(order.size());
        uint64_t new_s_count = 0;

        for (uint32_t old_id : order) {
            Node n = old_nodes[old_id];
            if (n.kind == K_I || n.kind == K_S) {
                n.b = mapping[n.b];
                n.c = mapping[n.c];
                if (n.b == NONE || n.c == NONE) throw std::runtime_error("compact child remap missing");
                if (n.b == n.c) throw std::runtime_error("unexpected degenerate choice during compact");
                if (n.kind == K_S) ++new_s_count;
            } else if (is_binary(n.kind)) {
                n.a = mapping[n.a];
                n.b = mapping[n.b];
                if (n.a == NONE || n.b == NONE) throw std::runtime_error("compact binary remap missing");
                if (n.a > n.b) std::swap(n.a, n.b);
            }
            if (rebuilt.size() >= static_cast<size_t>(NONE)) {
                throw std::runtime_error("node id exceeds uint32 capacity");
            }
            mapping[old_id] = static_cast<uint32_t>(rebuilt.size());
            rebuilt.push_back(n);
        }

        std::vector<uint32_t> new_roots;
        new_roots.reserve(roots.size());
        for (uint32_t root : roots) {
            if (mapping[root] == NONE) throw std::runtime_error("compact root mapping missing");
            new_roots.push_back(mapping[root]);
        }

        nodes.swap(rebuilt);
        stabilizer_nodes = new_s_count;
        color.clear(); color.shrink_to_fit();
        order.clear(); order.shrink_to_fit();
        mapping.clear(); mapping.shrink_to_fit();
        old_nodes.clear(); old_nodes.shrink_to_fit();
        rebuild_table();
        peak_nodes = std::max<uint64_t>(peak_nodes, nodes.size());
        return new_roots;
    }

    void write_binary(const std::string& path, uint32_t algebra_id, uint32_t root) const {
        if (root >= nodes.size()) throw std::runtime_error("output root overflow");
        std::ofstream out(path, std::ios::binary);
        if (!out) throw std::runtime_error("cannot open output binary");
        const char magic[8] = {'Q','T','R','C','9','0','N','1'};
        out.write(magic, 8);
        const uint64_t count = static_cast<uint64_t>(nodes.size());
        out.write(reinterpret_cast<const char*>(&algebra_id), sizeof(algebra_id));
        out.write(reinterpret_cast<const char*>(&count), sizeof(count));
        out.write(reinterpret_cast<const char*>(&root), sizeof(root));
        if (!nodes.empty()) {
            out.write(reinterpret_cast<const char*>(nodes.data()), static_cast<std::streamsize>(nodes.size() * sizeof(Node)));
        }
        if (!out) throw std::runtime_error("failed while writing output binary");
    }

private:
    void reset_table(size_t capacity) {
        if (capacity < 16) capacity = 16;
        size_t pow2 = 1;
        while (pow2 < capacity) pow2 <<= 1;
        slots.assign(pow2, 0);
    }

    void clear_table() {
        std::vector<uint32_t>().swap(slots);
    }

    void maybe_grow() {
        if (slots.empty()) reset_table(1024);
        if ((nodes.size() + 1ULL) * 10ULL >= slots.size() * 7ULL) {
            const size_t new_cap = slots.size() << 1;
            std::vector<uint32_t> old;
            old.swap(slots);
            slots.assign(new_cap, 0);
            for (uint32_t id = 0; id < nodes.size(); ++id) insert_existing(id);
        }
    }

    void rebuild_table() {
        size_t cap = 16;
        while (cap * 7ULL < std::max<size_t>(1, nodes.size()) * 10ULL) cap <<= 1;
        slots.assign(cap, 0);
        for (uint32_t id = 0; id < nodes.size(); ++id) insert_existing(id);
    }

    void insert_existing(uint32_t id) {
        const Node& n = nodes[id];
        const size_t mask = slots.size() - 1;
        size_t pos = static_cast<size_t>(node_hash(n)) & mask;
        while (slots[pos] != 0) pos = (pos + 1) & mask;
        slots[pos] = id + 1U;
    }

    uint32_t intern(const Node& n) {
        ++created;
        maybe_grow();
        const size_t mask = slots.size() - 1;
        size_t pos = static_cast<size_t>(node_hash(n)) & mask;
        while (true) {
            const uint32_t slot = slots[pos];
            if (slot == 0) {
                if (nodes.size() >= static_cast<size_t>(NONE)) {
                    throw std::runtime_error("node id exceeds uint32 capacity");
                }
                const uint32_t id = static_cast<uint32_t>(nodes.size());
                nodes.push_back(n);
                slots[pos] = id + 1U;
                if (n.kind == K_S) ++stabilizer_nodes;
                peak_nodes = std::max<uint64_t>(peak_nodes, nodes.size());
                return id;
            }
            const uint32_t id = slot - 1U;
            if (node_equal(nodes[id], n)) {
                ++reused;
                return id;
            }
            pos = (pos + 1) & mask;
        }
    }
};

struct Factor {
    uint64_t scope = 0;
    uint32_t root = 0;
};

uint32_t terminal_code(uint32_t algebra, uint32_t qubit, uint32_t bit) {
    if (algebra < 2) return bit ? 1U : 0U;
    return bit ? qubit + 1U : 0U;
}

uint32_t popcount64(uint64_t x) {
#if defined(__GNUG__)
    return static_cast<uint32_t>(__builtin_popcountll(x));
#else
    uint32_t c = 0; while (x) { x &= x - 1; ++c; } return c;
#endif
}

uint32_t build_local_factor(
    Circuit& circuit,
    uint32_t algebra,
    uint32_t qubit,
    std::vector<uint32_t> scope,
    const std::vector<int32_t>& selector_parameter,
    const std::array<uint32_t, 41>& rank
) {
    uint32_t low_terminal = circuit.terminal(terminal_code(algebra, qubit, 0));
    uint32_t high_terminal = circuit.terminal(terminal_code(algebra, qubit, 1));
    uint32_t even = low_terminal;
    uint32_t odd = high_terminal;
    if (qubit < selector_parameter.size() && selector_parameter[qubit] >= 0) {
        const uint32_t parameter = static_cast<uint32_t>(selector_parameter[qubit]);
        even = circuit.selector_choice(parameter, low_terminal, high_terminal);
        odd = circuit.selector_choice(parameter, high_terminal, low_terminal);
    }
    std::sort(scope.begin(), scope.end(), [&](uint32_t x, uint32_t y) { return rank[x] < rank[y]; });
    for (auto it = scope.rbegin(); it != scope.rend(); ++it) {
        const uint32_t variable = *it;
        const uint32_t new_even = circuit.stabilizer_choice(variable, even, odd);
        const uint32_t new_odd = circuit.stabilizer_choice(variable, odd, even);
        even = new_even;
        odd = new_odd;
    }
    return even;
}

struct Input {
    uint32_t algebra = 0;
    std::vector<uint32_t> order;
    std::vector<uint32_t> selector_qubits;
    std::vector<std::vector<uint32_t>> scopes;
};

Input read_input(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open input");
    Input x;
    size_t count = 0;
    in >> x.algebra;
    if (x.algebra > 2) throw std::runtime_error("invalid algebra id");
    in >> count;
    x.order.resize(count);
    for (auto& v : x.order) in >> v;
    if (x.order.size() > 41) throw std::runtime_error("too many stabilizer variables");
    in >> count;
    x.selector_qubits.resize(count);
    for (auto& q : x.selector_qubits) in >> q;
    size_t factor_count = 0;
    in >> factor_count;
    x.scopes.resize(factor_count);
    for (size_t q = 0; q < factor_count; ++q) {
        size_t n = 0; in >> n;
        x.scopes[q].resize(n);
        for (auto& v : x.scopes[q]) in >> v;
    }
    if (!in) throw std::runtime_error("malformed compact-native input");
    return x;
}

void compile(const Input& input, const std::string& output_path) {
    std::array<uint32_t, 41> rank{};
    rank.fill(std::numeric_limits<uint32_t>::max());
    for (uint32_t i = 0; i < input.order.size(); ++i) {
        if (input.order[i] >= 41) throw std::runtime_error("stabilizer variable out of range");
        rank[input.order[i]] = i;
    }
    std::vector<int32_t> selector_parameter(input.scopes.size(), -1);
    for (uint32_t p = 0; p < input.selector_qubits.size(); ++p) {
        const uint32_t q = input.selector_qubits[p];
        if (q >= selector_parameter.size()) throw std::runtime_error("selector qubit out of range");
        selector_parameter[q] = static_cast<int32_t>(p);
    }

    Circuit circuit;
    std::vector<Factor> factors;
    factors.reserve(input.scopes.size());
    for (uint32_t q = 0; q < input.scopes.size(); ++q) {
        uint64_t scope_mask = 0;
        for (uint32_t v : input.scopes[q]) {
            if (v >= 41 || rank[v] == std::numeric_limits<uint32_t>::max()) {
                throw std::runtime_error("scope variable absent from protected order");
            }
            scope_mask |= (1ULL << v);
        }
        const uint32_t root = build_local_factor(
            circuit, input.algebra, q, input.scopes[q], selector_parameter, rank
        );
        factors.push_back({scope_mask, root});
    }

    const uint8_t multiply = input.algebra == 2 ? K_MPMUL : K_MUL;
    const uint8_t marginal = input.algebra == 2 ? K_MPMIN : K_ADD;

    for (uint32_t step = 0; step < input.order.size(); ++step) {
        const uint32_t variable = input.order[step];
        const uint64_t bit = 1ULL << variable;
        std::vector<Factor> rest;
        std::vector<uint32_t> involved;
        rest.reserve(factors.size());
        involved.reserve(factors.size());
        uint64_t union_scope = 0;
        for (const Factor& f : factors) {
            if (f.scope & bit) {
                involved.push_back(f.root);
                union_scope |= f.scope;
            } else {
                rest.push_back(f);
            }
        }
        if (involved.empty()) throw std::runtime_error("frozen elimination variable absent");
        uint32_t joint = involved.front();
        for (size_t i = 1; i < involved.size(); ++i) {
            joint = circuit.binary(multiply, joint, involved[i]);
        }
        const uint32_t low = circuit.restrict_exact(joint, variable, 0);
        const uint32_t high = circuit.restrict_exact(joint, variable, 1);
        const uint32_t output_root = circuit.binary(marginal, low, high);
        const uint64_t output_scope = union_scope & ~bit;
        rest.push_back({output_scope, output_root});
        factors.swap(rest);

        std::vector<uint32_t> roots;
        roots.reserve(factors.size());
        for (const auto& f : factors) roots.push_back(f.root);
        const std::vector<uint32_t> compacted = circuit.compact(roots);
        for (size_t i = 0; i < factors.size(); ++i) factors[i].root = compacted[i];

        std::cout
            << "{\"phase\":\"EXACT_COMPACT_NATIVE_PROGRESS\""
            << ",\"step\":" << step
            << ",\"variable\":" << variable
            << ",\"involved_factor_count\":" << involved.size()
            << ",\"union_arity\":" << popcount64(union_scope)
            << ",\"output_arity\":" << popcount64(output_scope)
            << ",\"active_factor_count\":" << factors.size()
            << ",\"retained_symbolic_nodes\":" << circuit.nodes.size()
            << ",\"temporary_stabilizer_nodes\":" << circuit.stabilizer_nodes
            << ",\"peak_symbolic_nodes\":" << circuit.peak_nodes
            << "}" << std::endl;
    }

    for (const Factor& f : factors) {
        if (f.scope != 0) throw std::runtime_error("non-scalar factor after frozen elimination");
    }
    if (factors.empty()) throw std::runtime_error("empty factor set");
    uint32_t final_root = factors.front().root;
    for (size_t i = 1; i < factors.size(); ++i) {
        final_root = circuit.binary(multiply, final_root, factors[i].root);
    }
    std::vector<uint32_t> final_roots = circuit.compact({final_root});
    final_root = final_roots.front();
    if (circuit.stabilizer_nodes != 0) {
        throw std::runtime_error("temporary stabilizer nodes remain after frozen elimination");
    }
    circuit.write_binary(output_path, input.algebra, final_root);
    std::cout
        << "{\"phase\":\"EXACT_COMPACT_NATIVE_COMPLETED\""
        << ",\"algebra_id\":" << input.algebra
        << ",\"reachable_nodes\":" << circuit.nodes.size()
        << ",\"root\":" << final_root
        << ",\"peak_symbolic_nodes\":" << circuit.peak_nodes
        << ",\"intern_attempts\":" << circuit.created
        << ",\"intern_reuses\":" << circuit.reused
        << "}" << std::endl;
}

} // namespace

int main(int argc, char** argv) {
    try {
        std::string input_path;
        std::string output_path;
        for (int i = 1; i < argc; ++i) {
            std::string arg = argv[i];
            if (arg == "--input" && i + 1 < argc) input_path = argv[++i];
            else if (arg == "--output" && i + 1 < argc) output_path = argv[++i];
            else throw std::runtime_error("usage: --input PATH --output PATH");
        }
        if (input_path.empty() || output_path.empty()) {
            throw std::runtime_error("usage: --input PATH --output PATH");
        }
        const Input input = read_input(input_path);
        compile(input, output_path);
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "QTR_C90_COMPACT_NATIVE_ERROR: " << e.what() << std::endl;
        return 2;
    }
}
