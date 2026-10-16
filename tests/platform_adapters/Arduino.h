#pragma once
#include <cstdint>
#include <cstdio>
struct SerialStub {
    template<class... Args> void printf(const char*, Args...) {}
    void println(const char*) {}
};
struct EspStub {
    uint64_t mac = 0xF908;
    uint64_t getEfuseMac() { return mac; }
    unsigned getFreeHeap() { return 100000; }
    unsigned getMinFreeHeap() { return 90000; }
};
inline SerialStub Serial;
inline EspStub ESP;
