#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <new>
#include <string>
#include <type_traits>

namespace vpet {

struct LearningEstimate {
    int16_t mean = 0;
    uint16_t count = 0;
    int8_t bias = 0;
};

struct LearningEvent {
    uint64_t sequence = 0;
    uint8_t domain = 0, context = 0, action = 0;
    int8_t reward = 0;
};

// Portable policy v1, matching core/learning.py. Domains: training=0, combat=1,
// exploration=2. The adapter supplies context/reward meaning and legal actions.
// Mean moves toward reward by max(1, abs(delta)/min(new_count,8)), truncating;
// zero delta stays zero. Counts saturate at 65535 without freezing adaptation.
// Score = mean+bias+(legal fallback ? 5 : 0); ties favor fallback, then lowest ID.
// Inheritance centers combined parental mean+bias per row, normalizes to +/-25,
// and copies only bias. No RNG, rewards, runtime hooks or persistence writes.
// Codec: canonical ASCII base64 of little-endian "VPL1", u64 last, u16 size,
// 768 (i16 mean,u16 count,i8 bias) cells, oldest-first 12-byte events
// (u64 sequence,u8 domain,u8 context,u8 action,i8 reward), then IEEE CRC32.
// Max 6930 raw bytes / 9240 ASCII bytes; in-memory event padding is not encoded.
class LearningState {
public:
    static constexpr size_t DOMAINS = 3, CONTEXTS = 32, ACTIONS = 8;
    static constexpr size_t HISTORY_CAPACITY = 256, MAX_ENCODED_SIZE = 9240;

    uint64_t last_sequence() const { return last_; }
    // Zero is an exhausted sentinel, never an acceptable receipt.
    uint64_t next_sequence() const { return last_ == UINT64_MAX ? 0 : last_ + 1; }
    size_t history_size() const { return size_; }
    LearningEvent event(size_t oldest_first_index) const {
        return oldest_first_index < size_ ? events_[(head_ + oldest_first_index) % HISTORY_CAPACITY] : LearningEvent{};
    }

    template <typename D, typename C, typename A>
    LearningEstimate estimate(D domain, C context, A action) const {
        if constexpr (!(integer_type<D> && integer_type<C> && integer_type<A>)) {
            (void)domain; (void)context; (void)action;
            return {};
        } else {
            if (!bounded(domain, 0, 2) || !bounded(context, 0, 31) || !bounded(action, 0, 7)) return {};
            const auto i = index(static_cast<int>(domain), static_cast<int>(context), static_cast<int>(action));
            return {means_[i], counts_[i], biases_[i]};
        }
    }

    // Invalid numeric types/ranges, replay and gaps all return false atomically.
    template <typename S, typename D, typename C, typename A, typename R>
    bool record(S sequence, D domain, C context, A action, R reward) {
        if constexpr (!(integer_type<S> && integer_type<D> && integer_type<C> && integer_type<A> && integer_type<R>)) {
            (void)sequence; (void)domain; (void)context; (void)action; (void)reward;
            return false;
        } else {
            if (sequence <= 0 || !bounded(domain, 0, 2) || !bounded(context, 0, 31) ||
                !bounded(action, 0, 7) || !bounded(reward, -100, 100)) return false;
            const uint64_t seq = static_cast<uint64_t>(sequence);
            if (seq != next_sequence()) return false;
            const auto i = index(static_cast<int>(domain), static_cast<int>(context), static_cast<int>(action));
            update(means_[i], counts_[i], static_cast<int>(reward));
            events_[(head_ + size_) % HISTORY_CAPACITY] = {
                seq, static_cast<uint8_t>(domain), static_cast<uint8_t>(context),
                static_cast<uint8_t>(action), static_cast<int8_t>(reward)};
            if (size_ < HISTORY_CAPACITY) ++size_;
            else head_ = (head_ + 1) % HISTORY_CAPACITY;
            last_ = seq;
            return true;
        }
    }

    template <typename D, typename C, typename M, typename F>
    int choose(D domain, C context, M legal_mask, F fallback) const {
        if constexpr (!(integer_type<D> && integer_type<C> && integer_type<M> && integer_type<F>)) {
            (void)domain; (void)context; (void)legal_mask; (void)fallback;
            return -1;
        } else {
            if (!bounded(domain, 0, 2) || !bounded(context, 0, 31) ||
                !bounded(legal_mask, 0, 255) || !bounded(fallback, -1, 7)) return -1;
            const auto start = index(static_cast<int>(domain), static_cast<int>(context), 0);
            const int mask = static_cast<int>(legal_mask), fixed = static_cast<int>(fallback);
            int best = -1, best_score = -1000;
            for (int action = 0; action < static_cast<int>(ACTIONS); ++action) {
                if (!(mask & (1 << action))) continue;
                const int score = means_[start + action] + biases_[start + action] + (action == fixed ? 5 : 0);
                if (score > best_score || (score == best_score && action == fixed)) {
                    best = action;
                    best_score = score;
                }
            }
            return best;
        }
    }

    static LearningState inherited(const LearningState& a, const LearningState& b) {
        LearningState child;
        child.inheritFrom(a,b);
        return child;
    }

    // Destination belongs on the heap on ESP32. It must not alias a parent.
    void inheritFrom(const LearningState& a, const LearningState& b) {
        if (this==&a || this==&b) return;
        means_.fill(0); counts_.fill(0); biases_.fill(0);
        events_.fill(LearningEvent{}); last_=0; head_=size_=0;
        for (size_t row = 0; row < CELLS; row += ACTIONS) {
            int scores[ACTIONS], total = 0, peak = 0;
            for (size_t j = 0; j < ACTIONS; ++j) {
                scores[j] = a.means_[row + j] + a.biases_[row + j] + b.means_[row + j] + b.biases_[row + j];
                total += scores[j];
            }
            for (size_t j = 0; j < ACTIONS; ++j) {
                scores[j] = static_cast<int>(ACTIONS) * scores[j] - total;
                const int magnitude = scores[j] < 0 ? -scores[j] : scores[j];
                if (magnitude > peak) peak = magnitude;
            }
            if (peak) {
                for (size_t j = 0; j < ACTIONS; ++j)
                    biases_[row + j] = static_cast<int8_t>(25 * scores[j] / peak);
            }
        }
    }

    std::string encode() const {
        std::string raw("VPL1");
        raw.reserve(BASE_SIZE + size_ * 12);
        append(raw, last_, 8);
        append(raw, size_, 2);
        for (size_t i = 0; i < CELLS; ++i) {
            append(raw, static_cast<uint16_t>(means_[i]), 2);
            append(raw, counts_[i], 2);
            append(raw, static_cast<uint8_t>(biases_[i]), 1);
        }
        for (size_t i = 0; i < size_; ++i) {
            const auto e = event(i);
            append(raw, e.sequence, 8);
            append(raw, e.domain, 1); append(raw, e.context, 1); append(raw, e.action, 1);
            append(raw, static_cast<uint8_t>(e.reward), 1);
        }
        append(raw, crc32(raw, raw.size()), 4);
        return encode64(raw);
    }

    // Parse into a temporary heap candidate. Failure leaves *this unchanged.
    // Only one active individual's state is needed; inactive policies stay on disk.
    // Scratch: candidate sizeof(LearningState) plus <=6930 decoded bytes on heap;
    // no second state or large history/table buffers are placed on the task stack.
    bool decode(const std::string& record) {
        std::string raw;
        if (!decode64(record, raw) || raw.size() < BASE_SIZE || raw.compare(0, 4, "VPL1") != 0 ||
            crc32(raw, raw.size() - 4) != read(raw, raw.size() - 4, 4)) return false;
        const uint64_t last = read(raw, 4, 8), size = read(raw, 12, 2);
        if (size != (last < HISTORY_CAPACITY ? last : HISTORY_CAPACITY) || raw.size() != BASE_SIZE + size * 12)
            return false;
        std::unique_ptr<LearningState> candidate(new (std::nothrow) LearningState());
        if (!candidate) return false;
        candidate->last_ = last;
        candidate->size_ = static_cast<uint16_t>(size);
        size_t offset = 14;
        uint64_t total = 0;
        bool saturated = false;
        for (size_t i = 0; i < CELLS; ++i, offset += 5) {
            const int mean = signed_value(read(raw, offset, 2), 16);
            const auto count = static_cast<uint16_t>(read(raw, offset + 2, 2));
            const int bias = signed_value(read(raw, offset + 4, 1), 8);
            if (mean < -100 || mean > 100 || bias < -25 || bias > 25 || (!count && mean)) return false;
            candidate->means_[i] = static_cast<int16_t>(mean);
            candidate->counts_[i] = count;
            candidate->biases_[i] = static_cast<int8_t>(bias);
            total += count;
            saturated = saturated || count == 65535;
        }
        if (total > last || (!saturated && total != last)) return false;
        for (size_t i = 0; i < size; ++i, offset += 12) {
            const auto seq = read(raw, offset, 8);
            const int domain = static_cast<int>(read(raw, offset + 8, 1));
            const int context = static_cast<int>(read(raw, offset + 9, 1));
            const int action = static_cast<int>(read(raw, offset + 10, 1));
            const int reward = signed_value(read(raw, offset + 11, 1), 8);
            if (seq != last - size + i + 1 || domain >= 3 || context >= 32 || action >= 8 || reward < -100 || reward > 100)
                return false;
            candidate->events_[i] = {seq, static_cast<uint8_t>(domain), static_cast<uint8_t>(context),
                                    static_cast<uint8_t>(action), static_cast<int8_t>(reward)};
        }
        // Recompute each retained cell without allocating another table on the stack.
        for (size_t i = 0; i < CELLS; ++i) {
            int16_t mean = 0;
            uint16_t count = 0;
            for (size_t j = 0; j < size; ++j) {
                const auto& e = candidate->events_[j];
                if (index(e.domain, e.context, e.action) == i) update(mean, count, e.reward);
            }
            if (candidate->counts_[i] < count || (candidate->counts_[i] == count && candidate->means_[i] != mean))
                return false;
        }
        *this = *candidate;
        return true;
    }

private:
    static constexpr size_t CELLS = DOMAINS * CONTEXTS * ACTIONS;
    static constexpr size_t BASE_SIZE = 14 + CELLS * 5 + 4;
    template <typename T>
    static constexpr bool integer_type = std::is_integral<T>::value && !std::is_same<T, bool>::value;

    template <typename T>
    static bool bounded(T value, int64_t low, int64_t high) {
        if constexpr (std::is_signed<T>::value) return value >= low && value <= high;
        else return (low <= 0 || value >= static_cast<uint64_t>(low)) && value <= static_cast<uint64_t>(high);
    }
    static size_t index(int domain, int context, int action) {
        return (static_cast<size_t>(domain) * CONTEXTS + context) * ACTIONS + action;
    }
    static void update(int16_t& mean, uint16_t& count, int reward) {
        if (count < 65535) ++count;
        const int delta = reward - mean;
        if (!delta) return;
        const int divisor = count < 8 ? count : 8;
        int step = (delta < 0 ? -delta : delta) / divisor;
        if (!step) step = 1;
        mean = static_cast<int16_t>(mean + (delta > 0 ? step : -step));
    }
    static int signed_value(uint64_t value, unsigned bits) {
        return static_cast<int>(value) - (value & (uint64_t(1) << (bits - 1)) ? (1 << bits) : 0);
    }
    static void append(std::string& out, uint64_t value, unsigned bytes) {
        for (unsigned i = 0; i < bytes; ++i) out += static_cast<char>((value >> (8 * i)) & 255);
    }
    static uint64_t read(const std::string& raw, size_t offset, unsigned bytes) {
        uint64_t value = 0;
        for (unsigned i = 0; i < bytes; ++i) value |= uint64_t(static_cast<unsigned char>(raw[offset + i])) << (8 * i);
        return value;
    }
    static uint32_t crc32(const std::string& raw, size_t length) {
        uint32_t crc = 0xffffffffu;
        for (size_t i = 0; i < length; ++i) {
            crc ^= static_cast<unsigned char>(raw[i]);
            for (int bit = 0; bit < 8; ++bit) crc = (crc >> 1) ^ ((crc & 1) ? 0xedb88320u : 0u);
        }
        return crc ^ 0xffffffffu;
    }
    static std::string encode64(const std::string& raw) {
        const char* alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        std::string out;
        out.reserve(raw.size() / 3 * 4);
        // Every valid record is a multiple of three bytes, so padding is never used.
        for (size_t i = 0; i < raw.size(); i += 3) {
            const auto a = static_cast<unsigned char>(raw[i]);
            const auto b = static_cast<unsigned char>(raw[i + 1]);
            const auto c = static_cast<unsigned char>(raw[i + 2]);
            out += alphabet[a >> 2]; out += alphabet[((a & 3) << 4) | (b >> 4)];
            out += alphabet[((b & 15) << 2) | (c >> 6)]; out += alphabet[c & 63];
        }
        return out;
    }
    static int base64_digit(unsigned char c) {
        if (c >= 'A' && c <= 'Z') return c - 'A';
        if (c >= 'a' && c <= 'z') return c - 'a' + 26;
        if (c >= '0' && c <= '9') return c - '0' + 52;
        if (c == '+') return 62;
        if (c == '/') return 63;
        return -1;
    }
    static bool decode64(const std::string& text, std::string& raw) {
        if (text.size() < 5144 || text.size() > MAX_ENCODED_SIZE || text.size() % 4) return false;
        raw.reserve(text.size() / 4 * 3);
        for (size_t i = 0; i < text.size(); i += 4) {
            const int a = base64_digit(text[i]), b = base64_digit(text[i + 1]);
            const int c = base64_digit(text[i + 2]), d = base64_digit(text[i + 3]);
            if (a < 0 || b < 0 || c < 0 || d < 0) return false;
            raw += static_cast<char>((a << 2) | (b >> 4));
            raw += static_cast<char>(((b & 15) << 4) | (c >> 2));
            raw += static_cast<char>(((c & 3) << 6) | d);
        }
        return true;
    }

    std::array<int16_t, CELLS> means_{};
    std::array<uint16_t, CELLS> counts_{};
    std::array<int8_t, CELLS> biases_{};
    std::array<LearningEvent, HISTORY_CAPACITY> events_{};
    uint64_t last_ = 0;
    uint16_t head_ = 0, size_ = 0;
};

static_assert(sizeof(LearningEvent) <= 32, "Learning events exceed the RAM budget");
static_assert(sizeof(LearningState) <= 8192, "Load only one active learning state");

}  // namespace vpet
