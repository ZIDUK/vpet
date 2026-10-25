#pragma once
#include <cassert>
#include <cstring>
extern bool entropyEnabled;
inline void esp_fill_random(void* out,size_t size) { assert(entropyEnabled); memset(out,7,size); }
