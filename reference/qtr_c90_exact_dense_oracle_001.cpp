// Exact fixed-selector factor-table oracle for QTR-C90-EXACT-DECODER-001.
//
// This is an execution-backend port of the predecessor projection-plan oracle.
// It uses the protected factor graph and protected elimination order only. It
// receives a selector coordinate; it never receives an injected error or a
// decoder-success label.
//
// The numeric semirings are evaluated modulo six pairwise-coprime numbers
// m_i = 2^61 - c_i. Their product exceeds the strict full-C90 sum-product
// bound 2^41 * 9^90. A caller that verifies a native nonnegative integer is
// below that bound can therefore prove exact equality from all six residues.
// Min-plus is evaluated directly with exact 90-bit representatives and keys.

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using u128 = unsigned __int128;

namespace {

constexpr uint64_t TWO61 = 1ULL << 61;
constexpr uint64_t MASK61 = TWO61 - 1;
constexpr std::array<uint64_t, 6> REDUCTION_C = {1, 3, 7, 9, 13, 15};
constexpr std::array<uint64_t, 6> MODULI = {
    TWO61 - 1,
    TWO61 - 3,
    TWO61 - 7,
    TWO61 - 9,
    TWO61 - 13,
    TWO61 - 15,
};

struct Residues {
    std::array<uint64_t, 6> value{};
};

struct MinPlusValue {
    uint16_t weight = 0;
    u128 representative = 0;
    u128 canonical = 0;
};

template <class Value>
struct Factor {
    std::vector<int> scope;
    std::vector<Value> values;
};

struct Input {
    int algebra = -1;
    uint64_t coordinate = 0;
    std::vector<int> order;
    std::vector<int> selector_basis;
    std::vector<std::vector<int>> scopes;
};

uint64_t pseudo_mersenne_reduce(u128 product, uint64_t c, uint64_t modulus) {
    // Since 2^61 == c (mod 2^61-c), two folds suffice for a product of two
    // reduced residues. c <= 15, so the second folded value is < 2*modulus.
    u128 folded = (product & MASK61) + (product >> 61) * c;
    folded = (folded & MASK61) + (folded >> 61) * c;
    uint64_t value = static_cast<uint64_t>(folded);
    if (value >= modulus) value -= modulus;
    if (value >= modulus) value -= modulus;
    return value;
}

Residues residue_identity(uint64_t scalar) {
    Residues out;
    for (size_t i = 0; i < MODULI.size(); ++i) {
        out.value[i] = scalar % MODULI[i];
    }
    return out;
}

Residues residue_multiply(const Residues& left, const Residues& right) {
    Residues out;
    for (size_t i = 0; i < MODULI.size(); ++i) {
        out.value[i] = pseudo_mersenne_reduce(
            static_cast<u128>(left.value[i]) * right.value[i],
            REDUCTION_C[i],
            MODULI[i]
        );
    }
    return out;
}

Residues residue_marginal(const Residues& left, const Residues& right) {
    Residues out;
    for (size_t i = 0; i < MODULI.size(); ++i) {
        uint64_t value = left.value[i] + right.value[i];
        if (value >= MODULI[i]) value -= MODULI[i];
        out.value[i] = value;
    }
    return out;
}

MinPlusValue minplus_multiply(const MinPlusValue& left, const MinPlusValue& right) {
    return MinPlusValue{
        static_cast<uint16_t>(left.weight + right.weight),
        left.representative + right.representative,
        left.canonical + right.canonical,
    };
}

MinPlusValue minplus_marginal(const MinPlusValue& left, const MinPlusValue& right) {
    MinPlusValue out;
    if (left.weight < right.weight ||
        (left.weight == right.weight && left.representative <= right.representative)) {
        out.weight = left.weight;
        out.representative = left.representative;
    } else {
        out.weight = right.weight;
        out.representative = right.representative;
    }
    out.canonical = std::min(left.canonical, right.canonical);
    return out;
}

std::string hex_u128(u128 value) {
    if (value == 0) return "0x0";
    static constexpr char DIGITS[] = "0123456789abcdef";
    std::string text;
    while (value != 0) {
        text.push_back(DIGITS[static_cast<unsigned>(value & 0xFULL)]);
        value >>= 4;
    }
    std::reverse(text.begin(), text.end());
    return "0x" + text;
}

Input read_input() {
    Input input;
    int count = 0;
    if (!(std::cin >> input.algebra >> input.coordinate)) {
        throw std::runtime_error("dense oracle input header is missing");
    }
    if (input.algebra < 0 || input.algebra > 2) {
        throw std::runtime_error("dense oracle algebra id is invalid");
    }

    std::cin >> count;
    input.order.resize(static_cast<size_t>(count));
    for (int& variable : input.order) std::cin >> variable;

    std::cin >> count;
    input.selector_basis.resize(static_cast<size_t>(count));
    for (int& qubit : input.selector_basis) std::cin >> qubit;
    if (input.selector_basis.size() >= 64 ||
        input.coordinate >= (1ULL << input.selector_basis.size())) {
        throw std::runtime_error("dense oracle selector coordinate exceeds rank");
    }

    std::cin >> count;
    input.scopes.resize(static_cast<size_t>(count));
    for (auto& scope : input.scopes) {
        int arity = 0;
        std::cin >> arity;
        scope.resize(static_cast<size_t>(arity));
        for (int& variable : scope) std::cin >> variable;
        std::sort(scope.begin(), scope.end());
        if (std::adjacent_find(scope.begin(), scope.end()) != scope.end()) {
            throw std::runtime_error("dense oracle factor scope contains duplicate variables");
        }
    }
    if (!std::cin) throw std::runtime_error("dense oracle input is truncated");
    return input;
}

std::vector<int> sorted_union(const std::vector<std::vector<int>>& scopes) {
    std::vector<int> values;
    for (const auto& scope : scopes) {
        values.insert(values.end(), scope.begin(), scope.end());
    }
    std::sort(values.begin(), values.end());
    values.erase(std::unique(values.begin(), values.end()), values.end());
    return values;
}

std::vector<uint32_t> projection_map(
    const std::vector<int>& factor_scope,
    int eliminated_variable,
    const std::vector<int>& output_scope
) {
    if (factor_scope.size() >= 32 || output_scope.size() >= 32) {
        throw std::runtime_error("dense oracle table index exceeds uint32 range");
    }
    std::array<int, 64> output_position{};
    output_position.fill(-1);
    for (size_t i = 0; i < output_scope.size(); ++i) {
        if (output_scope[i] < 0 || output_scope[i] >= static_cast<int>(output_position.size())) {
            throw std::runtime_error("dense oracle variable id exceeds projection map range");
        }
        output_position[static_cast<size_t>(output_scope[i])] = static_cast<int>(i);
    }

    const size_t output_size = 1ULL << output_scope.size();
    std::vector<uint32_t> projection(output_size, 0);
    for (size_t factor_position = 0; factor_position < factor_scope.size(); ++factor_position) {
        const int variable = factor_scope[factor_position];
        if (variable == eliminated_variable) continue;
        if (variable < 0 || variable >= static_cast<int>(output_position.size()) ||
            output_position[static_cast<size_t>(variable)] < 0) {
            throw std::runtime_error("dense oracle projection variable is absent from output scope");
        }
        const size_t position = static_cast<size_t>(output_position[static_cast<size_t>(variable)]);
        const size_t block = 1ULL << position;
        const uint32_t factor_bit = 1U << factor_position;
        for (size_t base = 0; base < output_size; base += 2 * block) {
            for (size_t offset = 0; offset < block; ++offset) {
                projection[base + block + offset] = projection[base + offset] | factor_bit;
            }
        }
    }
    return projection;
}

template <class Value, class Multiply, class Marginal, class LocalValue>
Value evaluate(
    const Input& input,
    Multiply multiply,
    Marginal marginal,
    LocalValue local_value
) {
    std::vector<Factor<Value>> factors;
    factors.reserve(input.scopes.size() + input.order.size());

    std::vector<int> selector_parameter(input.scopes.size(), -1);
    for (size_t parameter = 0; parameter < input.selector_basis.size(); ++parameter) {
        const int qubit = input.selector_basis[parameter];
        if (qubit < 0 || qubit >= static_cast<int>(selector_parameter.size())) {
            throw std::runtime_error("dense oracle selector-basis qubit is out of range");
        }
        selector_parameter[static_cast<size_t>(qubit)] = static_cast<int>(parameter);
    }

    for (size_t qubit = 0; qubit < input.scopes.size(); ++qubit) {
        Factor<Value> factor;
        factor.scope = input.scopes[qubit];
        const size_t table_size = 1ULL << factor.scope.size();
        factor.values.resize(table_size);
        const int parameter = selector_parameter[qubit];
        const int base = parameter >= 0 ? static_cast<int>((input.coordinate >> parameter) & 1ULL) : 0;
        for (size_t assignment = 0; assignment < table_size; ++assignment) {
            const int bit = base ^ (__builtin_popcountll(assignment) & 1);
            factor.values[assignment] = local_value(static_cast<int>(qubit), bit, false);
        }
        factors.push_back(std::move(factor));
    }

    size_t step = 0;
    for (const int variable : input.order) {
        std::vector<size_t> involved_indices;
        std::vector<std::vector<int>> involved_scopes;
        for (size_t index = 0; index < factors.size(); ++index) {
            if (std::binary_search(factors[index].scope.begin(), factors[index].scope.end(), variable)) {
                involved_indices.push_back(index);
                involved_scopes.push_back(factors[index].scope);
            }
        }
        if (involved_indices.empty()) {
            throw std::runtime_error("dense oracle elimination variable has no factor");
        }

        const std::vector<int> union_scope = sorted_union(involved_scopes);
        std::vector<int> output_scope;
        for (const int item : union_scope) {
            if (item != variable) output_scope.push_back(item);
        }
        const size_t output_size = 1ULL << output_scope.size();
        const Value identity = local_value(-1, 0, true);
        std::vector<Value> low(output_size, identity);
        std::vector<Value> high(output_size, identity);

        for (const size_t factor_index : involved_indices) {
            const Factor<Value>& factor = factors[factor_index];
            const auto variable_it = std::lower_bound(factor.scope.begin(), factor.scope.end(), variable);
            if (variable_it == factor.scope.end() || *variable_it != variable) {
                throw std::runtime_error("dense oracle involved-factor variable lookup failed");
            }
            const size_t variable_position = static_cast<size_t>(variable_it - factor.scope.begin());
            const uint32_t high_bit = 1U << variable_position;
            const std::vector<uint32_t> projection = projection_map(factor.scope, variable, output_scope);

            #pragma omp parallel for schedule(static)
            for (long long raw = 0; raw < static_cast<long long>(output_size); ++raw) {
                const size_t index = static_cast<size_t>(raw);
                const uint32_t projected = projection[index];
                low[index] = multiply(low[index], factor.values[projected]);
                high[index] = multiply(high[index], factor.values[projected | high_bit]);
            }
        }

        #pragma omp parallel for schedule(static)
        for (long long raw = 0; raw < static_cast<long long>(output_size); ++raw) {
            const size_t index = static_cast<size_t>(raw);
            low[index] = marginal(low[index], high[index]);
        }
        high.clear();
        high.shrink_to_fit();

        std::vector<Factor<Value>> next;
        next.reserve(factors.size() - involved_indices.size() + 1);
        for (size_t index = 0; index < factors.size(); ++index) {
            if (!std::binary_search(involved_indices.begin(), involved_indices.end(), index)) {
                next.push_back(std::move(factors[index]));
            }
        }
        Factor<Value> output_factor;
        output_factor.scope = std::move(output_scope);
        output_factor.values = std::move(low);
        next.push_back(std::move(output_factor));
        factors = std::move(next);

        std::cerr
            << "C90_DENSE_ORACLE_STEP step=" << step
            << " variable=" << variable
            << " active_factors=" << factors.size()
            << " output_entries=" << output_size
            << '\n';
        ++step;
    }

    Value result = local_value(-1, 0, true);
    for (const auto& factor : factors) {
        if (!factor.scope.empty() || factor.values.size() != 1) {
            throw std::runtime_error("dense oracle retained a non-scalar final factor");
        }
        result = multiply(result, factor.values[0]);
    }
    return result;
}

void print_numeric_result(const Input& input, const Residues& result) {
    std::cout
        << "{\"status\":\"C90_DENSE_EXACT_RESIDUE_ORACLE_PASS\""
        << ",\"algebra_id\":" << input.algebra
        << ",\"coordinate\":" << input.coordinate
        << ",\"moduli\":[";
    for (size_t i = 0; i < MODULI.size(); ++i) {
        if (i != 0) std::cout << ',';
        std::cout << MODULI[i];
    }
    std::cout << "],\"residues\":[";
    for (size_t i = 0; i < MODULI.size(); ++i) {
        if (i != 0) std::cout << ',';
        std::cout << result.value[i];
    }
    std::cout << "],\"quality_exposed\":false}" << std::endl;
}

void print_minplus_result(const Input& input, const MinPlusValue& result) {
    std::cout
        << "{\"status\":\"C90_DENSE_EXACT_MINPLUS_ORACLE_PASS\""
        << ",\"algebra_id\":2"
        << ",\"coordinate\":" << input.coordinate
        << ",\"minimum_weight\":" << result.weight
        << ",\"minimum_representative_hex\":\"" << hex_u128(result.representative) << "\""
        << ",\"canonical_hex\":\"" << hex_u128(result.canonical) << "\""
        << ",\"quality_exposed\":false}" << std::endl;
}

}  // namespace

int main() {
    try {
        const Input input = read_input();
        const auto started = std::chrono::steady_clock::now();

        if (input.algebra < 2) {
            const uint64_t zero_weight = input.algebra == 0 ? 9 : 2;
            const auto local_value = [zero_weight](int qubit, int bit, bool identity) {
                (void)qubit;
                return residue_identity(identity ? 1 : (bit ? 1 : zero_weight));
            };
            const Residues result = evaluate<Residues>(
                input,
                residue_multiply,
                residue_marginal,
                local_value
            );
            print_numeric_result(input, result);
        } else {
            const auto local_value = [](int qubit, int bit, bool identity) {
                if (identity) return MinPlusValue{};
                if (qubit < 0 || qubit >= 128) {
                    throw std::runtime_error("dense oracle min-plus qubit exceeds fixed-width range");
                }
                const u128 physical = bit ? (static_cast<u128>(1) << qubit) : 0;
                return MinPlusValue{static_cast<uint16_t>(bit), physical, physical};
            };
            const MinPlusValue result = evaluate<MinPlusValue>(
                input,
                minplus_multiply,
                minplus_marginal,
                local_value
            );
            print_minplus_result(input, result);
        }

        const double elapsed = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started
        ).count();
        std::cerr << "C90_DENSE_ORACLE_ELAPSED_SECONDS " << elapsed << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "QTR_C90_DENSE_ORACLE_ERROR: " << error.what() << '\n';
        return 2;
    }
}
