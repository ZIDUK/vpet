#pragma once

#include <array>
#include <cstdint>
#include <string>

namespace vpet {
namespace breeding {

// Value input only. Adapter maps adult stages and verifies the installed line.
// IDs follow PetProfile (32 lowercase hex, nonzero), without depending on it.
struct Parent {
    std::string pet_id, sex, line_id;
    bool adult = false;
    int health = 0, hunger = 0, energy = 0, happiness = 0;
    bool injured = false, dead = false, asleep = false;
    bool away = false, paused = false, busy = false;
    // External duration, not a timestamp: only zero is eligible. Signed to
    // reject malformed negative/overflow input before any adapter narrowing.
    int64_t cooldown_remaining = 0;
    std::array<std::string, 2> parents{};
    std::array<std::string, 4> grandparents{};
};

namespace detail {

inline bool valid_id(const std::string& id) {
    return id.size() == 32 && id != std::string(32, '0') &&
           id.find_first_not_of("0123456789abcdef") == std::string::npos;
}

inline bool valid_parent(const Parent& p) {
    if (!valid_id(p.pet_id) || (p.sex != "M" && p.sex != "F")) return false;
    if (p.line_id.empty() || p.line_id.size() > 63 ||
        p.line_id.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-/") != std::string::npos)
        return false;
    if (!p.adult || p.injured || p.dead || p.asleep || p.away || p.paused || p.busy ||
        p.cooldown_remaining != 0) return false;
    if (p.health < 80 || p.health > 100 || p.hunger < 60 || p.hunger > 100 ||
        p.energy < 70 || p.energy > 100 || p.happiness < 60 || p.happiness > 100) return false;
    for (const auto& id : p.parents)
        if (!id.empty() && (!valid_id(id) || id == p.pet_id)) return false;
    for (const auto& id : p.grandparents)
        if (!id.empty() && (!valid_id(id) || id == p.pet_id)) return false;
    return p.parents[0].empty() || p.parents[0] != p.parents[1];
}

inline bool has_ancestor(const Parent& p, const std::string& id) {
    if (id.empty()) return false;
    for (const auto& ancestor : p.parents) if (ancestor == id) return true;
    for (const auto& ancestor : p.grandparents) if (ancestor == id) return true;
    return false;
}

class Stream {
public:
    explicit Stream(uint32_t seed) : state_(seed) {}
    uint32_t draw() {
        // Force uint32 wrapping at each multiply, also on wider integer hosts.
        state_ = static_cast<uint32_t>(state_ + UINT32_C(0x9E3779B9));
        uint32_t value = static_cast<uint32_t>((state_ ^ (state_ >> 16)) * UINT32_C(0x85EBCA6B));
        value = static_cast<uint32_t>((value ^ (value >> 13)) * UINT32_C(0xC2B2AE35));
        return value ^ (value >> 16);
    }
    uint8_t iv_mask() {
        uint8_t mask;
        do { mask = static_cast<uint8_t>(draw() & 63u); } while (mask == 0 || mask == 63);
        return mask;
    }
private:
    uint32_t state_;
};

}  // namespace detail

// Reject direct relations and ANY common known ancestor in two generations.
// Empty references are unknown, not shared ancestors. Missing/older ancestry
// cannot be detected: true does not certify unrelatedness. No clock advances.
inline bool check_pair(const Parent& a, const Parent& b) {
    if (!detail::valid_parent(a) || !detail::valid_parent(b) || a.pet_id == b.pet_id ||
        a.sex == b.sex || a.line_id != b.line_id) return false;
    if (detail::has_ancestor(a, b.pet_id) || detail::has_ancestor(b, a.pet_id)) return false;
    for (const auto& id : a.parents) if (detail::has_ancestor(b, id)) return false;
    for (const auto& id : a.grandparents) if (detail::has_ancestor(b, id)) return false;
    return true;
}

// Six IV source bits, 1=B. Both sources selected; values need not differ.
inline uint8_t iv_source_mask(uint32_t seed) {
    return detail::Stream(seed).iv_mask();
}

// Version 1: first acceptable six-bit mask, then one draw per low/high nibble.
// Six IVs use mask bits; the two trait nibbles use bit 6 of their draw.
// Low five bits == 0 mutate (1/32), bit 5 selects +1 (set) or -1, clamped.
// Typed arrays/seed cannot represent invalid lengths, bytes or uint32 values.
// No Pet, profile, RNG, storage, spending or individual-creation dependencies.
inline std::array<uint8_t, 4> offspring_dna(const std::array<uint8_t, 4>& a,
                                         const std::array<uint8_t, 4>& b,
                                         uint32_t seed) {
    detail::Stream stream(seed);
    const auto mask = stream.iv_mask();
    std::array<uint8_t, 4> result{};
    for (unsigned locus = 0; locus < 8; ++locus) {
        const auto draw = stream.draw();
        const bool from_b = ((locus < 6 ? mask >> locus : draw >> 6) & 1u) != 0;
        const auto& source = from_b ? b : a;
        const unsigned shift = 4 * (locus % 2);
        int value = (source[locus / 2] >> shift) & 15;
        if ((draw & 31u) == 0) {
            value += (draw & 32u) ? 1 : -1;
            if (value < 0) value = 0;
            if (value > 15) value = 15;
        }
        result[locus / 2] |= static_cast<uint8_t>(value << shift);
    }
    return result;
}

}  // namespace breeding
}  // namespace vpet
