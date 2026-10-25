#include "vpet/ProfileRandom.h"
#include <bootloader_random.h>
#include <esp_system.h>

namespace vpet {
int ProfileRandom::entropy(void* self,unsigned char* out,size_t size) {
    if (!static_cast<ProfileRandom*>(self)->entropyEnabled_)
        return MBEDTLS_ERR_CTR_DRBG_ENTROPY_SOURCE_FAILED;
    esp_fill_random(out,size);
    return 0;
}

bool ProfileRandom::begin() {
    if (attempted_) return ready_;
    attempted_=true;
    bootloader_random_enable();
    entropyEnabled_=true;
    const unsigned char purpose[]="vpet-profile-v1";
    const int result=mbedtls_ctr_drbg_seed(&context_,entropy,this,purpose,sizeof(purpose)-1);
    entropyEnabled_=false;
    bootloader_random_disable();
    ready_=result==0;
    // Never reopen ADC while gameplay/radio is active. At mbedTLS's bounded
    // reseed interval, entropy() fails closed; reboot seeds a fresh session.
    return ready_;
}

PetProfile ProfileRandom::next() {
    unsigned char bytes[16];
    if (!ready_ || mbedtls_ctr_drbg_random(&context_,bytes,sizeof(bytes))!=0) return PetProfile();
    uint32_t words[4]={};
    for(int i=0;i<16;++i) words[i/4]=(words[i/4]<<8)|bytes[i];
    return PetProfile::fromWords(words);
}
}  // namespace vpet
