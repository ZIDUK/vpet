#pragma once
#include <cstdint>
#include <cstring>
#include <string>
class String : public std::string {
public:
    using std::string::string;
    using std::string::operator=;
    String(const std::string& value) : std::string(value) {}
    String substring(size_t start, size_t end = std::string::npos) const {
        return substr(start, end == std::string::npos ? end : end - start);
    }
    int lastIndexOf(char c) const { auto pos = rfind(c); return pos == npos ? -1 : int(pos); }
    void remove(size_t start) { erase(start); }
    void trim() {
        const auto first = find_first_not_of(" \t\r\n");
        if (first == npos) clear();
        else *this = substr(first, find_last_not_of(" \t\r\n") - first + 1);
    }
};
