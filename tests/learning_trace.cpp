#include <vpet/Learning.h>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>

using vpet::LearningState;

static void selftest() {
    static_assert(sizeof(vpet::LearningEvent) <= 32, "bounded events");
    static_assert(sizeof(LearningState) <= 8192, "active policy RAM budget");
    LearningState state;
    const auto before = state.encode();
    assert(!state.record(true, 0, 0, 0, 0));
    assert(!state.record(1.5, 0, 0, 0, 0));
    assert(!state.record(1, false, 0, 0, 0));
    assert(!state.record(1, 0, 0.5, 0, 0));
    assert(!state.record(1, 0, 0, true, 0));
    assert(!state.record(1, 0, 0, 0, 100.5));
    assert(!state.record(1, 256, 0, 0, 0));
    assert(!state.record(1, 0, 256, 0, 0));
    assert(!state.record(1, 0, 0, 256, 0));
    assert(!state.record(1, 0, 0, 0, 256));
    assert(!state.record(-1, 0, 0, 0, 0));
    assert(!state.record(2, 0, 0, 0, 0));
    assert(!state.record(1, 0, 0, 0, std::numeric_limits<uint64_t>::max()));
    assert(state.choose(0, 0, 256, 0) == -1);
    assert(state.choose(0, 0, -1, 0) == -1);
    assert(state.choose(0, 0, true, 0) == -1);
    assert(state.choose(0, 0, 255.0, 0) == -1);
    assert(state.choose(0, 0, 255, false) == -1);
    assert(state.choose(0, 0, 255, 8) == -1);
    assert(state.encode() == before);
    assert(state.record(1, 0, 0, 0, 100));
    const auto recorded = state.encode();
    assert(!state.record(1, 0, 0, 0, -100));
    assert(!state.record(3, 0, 0, 0, -100));
    assert(state.encode() == recorded);
    assert(state.last_sequence() == 1 && state.next_sequence() == 2);
    const auto cell = state.estimate(0, 0, 0);
    assert(cell.mean == 100 && cell.count == 1 && cell.bias == 0);
    assert(state.history_size() == 1 && state.event(0).sequence == 1);
    for (int mask = 0; mask < 256; ++mask) {
        for (int fallback = -1; fallback < 8; ++fallback) {
            const int action = state.choose(0, 0, mask, fallback);
            assert((!mask && action == -1) || (action >= 0 && action < 8 && (mask & (1 << action))));
        }
    }
    const auto child = LearningState::inherited(state, state);
    assert(child.last_sequence() == 0 && child.history_size() == 0);
    assert(child.estimate(0, 0, 0).count == 0);
    assert(child.estimate(0, 0, 0).bias == 25);
    LearningState decoded;
    assert(decoded.decode(recorded) && decoded.encode() == recorded);
    assert(!decoded.decode(recorded + "x") && decoded.encode() == recorded);
    for (const auto& bad : {recorded + "=", recorded + "\n", " " + recorded,
                            recorded.substr(1), std::string("!") + recorded.substr(1)}) {
        assert(!decoded.decode(bad) && decoded.encode() == recorded);
    }
    std::cout << "selftest ok; event=" << sizeof(vpet::LearningEvent) << "; state=" << sizeof(LearningState) << '\n';
}

int main() {
    LearningState state;
    std::string line;
    while (std::getline(std::cin, line)) {
        std::istringstream args(line);
        std::string op;
        args >> op;
        if (op == "selftest") selftest();
        else if (op == "encode") std::cout << state.encode() << '\n';
        else if (op == "decode") {
            std::string value; args >> value;
            std::cout << state.decode(value) << '\n';
        } else if (op == "record") {
            uint64_t sequence; int domain, context, action, reward;
            args >> sequence >> domain >> context >> action >> reward;
            assert(args);
            std::cout << state.record(sequence, domain, context, action, reward) << '\n';
        } else if (op == "choose") {
            int domain, context, mask, fallback;
            args >> domain >> context >> mask >> fallback;
            assert(args);
            std::cout << state.choose(domain, context, mask, fallback) << '\n';
        } else if (op == "inherit") {
            state = LearningState::inherited(state, state);
            std::cout << "1\n";
        } else if (op == "sequence") {
            std::cout << state.last_sequence() << ' ' << state.next_sequence() << '\n';
        } else if (op == "saturate") {
            state = LearningState();
            for (uint64_t i = 1; i <= 65540; ++i) assert(state.record(i, 1, 3, 2, 100));
            for (int i = 0; i < 64; ++i) assert(state.record(state.next_sequence(), 1, 3, 2, -100));
            assert(state.estimate(1, 3, 2).count == 65535);
            assert(state.estimate(1, 3, 2).mean == -100);
            assert(state.history_size() == 256 && state.event(255).sequence == state.last_sequence());
            assert(state.encode().size() == 9240);
            std::cout << "1\n";
        } else return 2;
    }
}
