#pragma once
#include <algorithm>
#include <cerrno>
#include <climits>
#include <cstdio>
#include <cstring>
#include <dirent.h>
#include <limits>
#include <memory>
#include <new>
#include <set>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <fcntl.h>
#include <unistd.h>
#include "vpet/LittleFsCollectionRepository.h"
#include "vpet/LittleFsLearningRepository.h"
#include "vpet/StorageTiming.h"

namespace std {
FILE* storageOpen(const char*, const char*);
int storageClose(FILE*);
size_t storageRead(void*, size_t, size_t, FILE*);
size_t storageWrite(const void*, size_t, size_t, FILE*);
int storageRemove(const char*);
}
int storageRename(const char*, const char*);
int storageSync(int);

// Instrument only the adapters, leaving fixture setup and assertions untouched.
#define fopen storageOpen
#define fclose storageClose
#define fread storageRead
#define fwrite storageWrite
#define remove storageRemove
#define rename storageRename
#define fsync storageSync
