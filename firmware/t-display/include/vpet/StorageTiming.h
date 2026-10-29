#pragma once

#include <cstdio>
#include <cstdint>
#include <time.h>

namespace vpet {
// Measure storage phases without Arduino dependencies in the repositories.
class StorageTiming {
public:
    explicit StorageTiming(const char* scope) : scope_(scope), started_(now()) {}
    void mark(const char* phase) {
#ifdef ARDUINO
        const auto elapsed=now()-started_;
        std::printf("VPET_STORAGE_PHASE scope=%s phase=%s duration_ms=%lu\n",
            scope_,phase,static_cast<unsigned long>(elapsed/1000));
#else
        (void)phase;
        (void)scope_;
#endif
        started_=now();
    }
private:
    static uint64_t now() {
        timespec value{};
        clock_gettime(CLOCK_MONOTONIC,&value);
        return uint64_t(value.tv_sec)*1000000+value.tv_nsec/1000;
    }
    const char* scope_;
    uint64_t started_;
};
}
