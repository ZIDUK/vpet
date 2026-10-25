#pragma once
#include <cstddef>
#include <cassert>
extern bool entropyEnabled, seedFails, randomFails;
extern int seeds, generations;
#define MBEDTLS_ERR_CTR_DRBG_ENTROPY_SOURCE_FAILED -1
struct mbedtls_ctr_drbg_context { bool seeded; };
inline void mbedtls_ctr_drbg_init(mbedtls_ctr_drbg_context* c) { c->seeded=false; }
inline void mbedtls_ctr_drbg_free(mbedtls_ctr_drbg_context*) {}
inline int mbedtls_ctr_drbg_seed(mbedtls_ctr_drbg_context* c,int(*entropy)(void*,unsigned char*,size_t),void* ctx,
                               const unsigned char*,size_t) {
    ++seeds;
    unsigned char buffer[48];
    assert(entropyEnabled && entropy(ctx,buffer,sizeof(buffer))==0);
    c->seeded=!seedFails; return seedFails?-1:0;
}
inline int mbedtls_ctr_drbg_random(void* context,unsigned char* out,size_t size) {
    assert(!entropyEnabled && static_cast<mbedtls_ctr_drbg_context*>(context)->seeded);
    ++generations;
    for(size_t i=0;i<size;++i) out[i]=static_cast<unsigned char>(generations+i);
    return randomFails?-1:0;
}
