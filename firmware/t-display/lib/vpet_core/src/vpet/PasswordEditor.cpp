#include "vpet/PasswordEditor.h"

namespace vpet {
namespace {
constexpr const char* kGroups[] = {
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789",
    "!@#$%^&*()-_=+[]{};:,.?/",
};
constexpr const char* kLabels[] = {"UPPER", "LOWER", "NUM", "SYM"};
}

const char* PasswordEditor::characters() const { return kGroups[group_]; }
const char* PasswordEditor::groupLabel() const { return kLabels[group_]; }

void PasswordEditor::next() {
    const size_t count = std::char_traits<char>::length(characters());
    index_ = (index_ + 1) % (count + 4);
}

bool PasswordEditor::select() {
    const size_t count = std::char_traits<char>::length(characters());
    if (index_ >= count) {
        return selectCommand(static_cast<PasswordCommand>(index_ - count));
    }
    if (password_.size() >= 63) return false;
    password_.push_back(characters()[index_]);
    return false;
}

bool PasswordEditor::selectCommand(PasswordCommand command) {
    if (command == PasswordCommand::Mode) {
        group_ = (group_ + 1) % 4;
        index_ = 0;
    } else if (command == PasswordCommand::Delete && !password_.empty()) {
        password_.pop_back();
    } else if (command == PasswordCommand::Cancel) {
        clear();
        cancelled_ = true;
    }
    return command == PasswordCommand::Connect;
}

void PasswordEditor::clear() {
    password_.clear();
    group_ = 0;
    index_ = 0;
}

bool PasswordEditor::consumeCancelled() {
    const bool value = cancelled_;
    cancelled_ = false;
    return value;
}

const char* PasswordEditor::keyLabel() const {
    const size_t count = std::char_traits<char>::length(characters());
    if (index_ >= count) {
        constexpr const char* commands[] = {"MODE", "DEL", "CONNECT", "CANCEL"};
        return commands[index_ - count];
    }
    static char label[2] = {'A', '\0'};
    label[0] = characters()[index_];
    return label;
}

}  // namespace vpet
