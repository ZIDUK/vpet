#pragma once
#include <cerrno>
#include <cstdio>
#include <fcntl.h>
#include <string>

// Match the board's formatted LittleFS name_max, not the host filesystem's.
extern "C" int rename(const char* from,const char* to) {
    const std::string path(to);
    if (path.substr(path.find_last_of('/')+1).size()>32) { errno=ENAMETOOLONG; return -1; }
    return ::renameat(AT_FDCWD,from,AT_FDCWD,to);
}
