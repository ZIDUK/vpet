#pragma once
#include <cstdint>
#include <cstdio>
#include <string>
struct SerialMock {
    std::string output;
    void println(const char* s) { output += std::string(s) + "\n"; }
    void printf(const char* s) { output += s; }
    template<class... T> void printf(const char* fmt, T... args) {
        char buffer[256]; std::snprintf(buffer, sizeof(buffer), fmt, args...); output += buffer;
    }
};
extern SerialMock Serial;
inline uint32_t esp_random() { return 42; }
