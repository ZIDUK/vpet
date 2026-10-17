#pragma once
#include <fstream>
#include <string>
#include <cstdint>

inline size_t assetOpens = 0, assetReads = 0;
inline std::string assetRoot;
class File {
    std::ifstream file;
public:
    File() = default;
    explicit File(const std::string& path) : file(path, std::ios::binary) {}
    explicit operator bool() const { return file.is_open(); }
    int read() { ++assetReads; return file.get(); }
    size_t read(uint8_t* out, size_t size) {
        ++assetReads; file.read(reinterpret_cast<char*>(out), size); return file.gcount();
    }
    size_t readBytes(char* out, size_t size) {
        return read(reinterpret_cast<uint8_t*>(out), size);
    }
    bool seek(size_t offset) { file.clear(); file.seekg(offset); return bool(file); }
    int available() {
        const auto current=file.tellg();
        file.seekg(0,std::ios::end); const auto end=file.tellg();
        file.seekg(current); return static_cast<int>(end-current);
    }
    bool find(const char* needle) {
        std::string value((std::istreambuf_iterator<char>(file)), {});
        return value.find(needle) != std::string::npos;
    }
    void close() { file.close(); }
};
struct LittleFSMock {
    bool begin(bool, const char*, int, const char*) { return true; }
    File open(const char* path, const char*) {
        ++assetOpens; return File(assetRoot + path);
    }
};
inline LittleFSMock LittleFS;
