#pragma once

#include <stddef.h>
#include <string>

namespace vpet {

enum class PasswordCommand : uint8_t { Mode, Delete, Connect, Cancel };

class PasswordEditor {
public:
    void next();
    bool select();
    bool selectCommand(PasswordCommand command);
    bool consumeCancelled();
    void clear();
    const std::string& password() const { return password_; }
    const char* keyLabel() const;
    const char* groupLabel() const;

private:
    const char* characters() const;

    std::string password_;
    uint8_t group_ = 0;
    size_t index_ = 0;
    bool cancelled_ = false;
};

}  // namespace vpet
