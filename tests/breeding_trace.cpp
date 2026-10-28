#include <array>
#include <cassert>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <string>
#include <type_traits>

#include "vpet/Breeding.h"

using vpet::breeding::Parent;
using vpet::breeding::check_pair;
using vpet::breeding::iv_source_mask;
using vpet::breeding::offspring_dna;
using vpet::breeding::offspring_sex;

static_assert(std::is_same<decltype(offspring_dna(std::array<uint8_t, 4>{},
              std::array<uint8_t, 4>{}, uint32_t{})), std::array<uint8_t, 4>>::value,
              "DNA and seed must have fixed unsigned widths");
static_assert(std::tuple_size<decltype(Parent{}.parents)>::value == 2, "two parents only");
static_assert(std::tuple_size<decltype(Parent{}.grandparents)>::value == 4, "four grandparents only");

bool read_parent(Parent& p) {
    if (!(std::cin >> std::quoted(p.pet_id) >> std::quoted(p.sex) >> std::quoted(p.line_id)
          >> p.adult >> p.health >> p.hunger >> p.energy >> p.happiness
          >> p.injured >> p.dead >> p.asleep >> p.away >> p.paused >> p.busy
          >> p.cooldown_remaining)) return false;
    for (auto& id : p.parents) if (!(std::cin >> std::quoted(id))) return false;
    for (auto& id : p.grandparents) if (!(std::cin >> std::quoted(id))) return false;
    return true;
}

int main(int argc, char** argv) {
    assert(!check_pair(Parent{}, Parent{}));
    if (argc != 2) return 1;
    if (std::string(argv[1]) == "pair") {
        Parent a, b;
        while (read_parent(a)) {
            if (!read_parent(b)) return 2;
            std::cout << check_pair(a, b) << '\n';
        }
        return std::cin.eof() ? 0 : 2;
    }
    if (std::string(argv[1]) == "sex") {
        uint64_t seed; std::string sexA, sexB; unsigned sumA, sumB;
        while (std::cin >> seed >> sexA >> sumA >> sexB >> sumB) {
            if (seed > UINT32_MAX || sumA > 90 || sumB > 90) return 2;
            std::cout << offspring_sex(sexA, static_cast<uint8_t>(sumA), sexB,
                static_cast<uint8_t>(sumB), static_cast<uint32_t>(seed)) << '\n';
        }
        return std::cin.eof() ? 0 : 2;
    }
    if (std::string(argv[1]) != "dna") return 1;
    uint64_t seed;
    while (std::cin >> seed) {
        if (seed > UINT32_MAX) return 2;
        std::array<uint8_t, 4> a{}, b{};
        for (auto* dna : {&a, &b}) {
            for (auto& byte : *dna) {
                unsigned value;
                if (!(std::cin >> value) || value > UINT8_MAX) return 2;
                byte = static_cast<uint8_t>(value);
            }
        }
        const auto before_a = a, before_b = b;
        const auto mask = iv_source_mask(static_cast<uint32_t>(seed));
        const auto result = offspring_dna(a, b, static_cast<uint32_t>(seed));
        assert(mask > 0 && mask < 63);
        assert(a == before_a && b == before_b);
        assert(result == offspring_dna(a, b, static_cast<uint32_t>(seed)));
        std::cout << static_cast<unsigned>(mask);
        for (const auto byte : result) std::cout << ' ' << static_cast<unsigned>(byte);
        std::cout << '\n';
    }
    return std::cin.eof() ? 0 : 2;
}
