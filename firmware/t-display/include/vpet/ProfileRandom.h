#pragma once
#include <mbedtls/ctr_drbg.h>
#include "vpet/PetProfile.h"

namespace vpet {

// Seed once at startup, before any ADC/RF client; use DRBG thereafter.
class ProfileRandom {
public:
    ProfileRandom() { mbedtls_ctr_drbg_init(&context_); }
    ~ProfileRandom() { mbedtls_ctr_drbg_free(&context_); }
    ProfileRandom(const ProfileRandom&) = delete;
    ProfileRandom& operator=(const ProfileRandom&) = delete;
    bool begin();
    PetProfile next();
private:
    static int entropy(void* self,unsigned char* out,size_t size);
    mbedtls_ctr_drbg_context context_;
    bool attempted_=false, ready_=false, entropyEnabled_=false;
};
}  // namespace vpet
