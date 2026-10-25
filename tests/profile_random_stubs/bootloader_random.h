#pragma once
extern bool entropyEnabled;
extern int enables, disables;
inline void bootloader_random_enable() { entropyEnabled=true; ++enables; }
inline void bootloader_random_disable() { entropyEnabled=false; ++disables; }
