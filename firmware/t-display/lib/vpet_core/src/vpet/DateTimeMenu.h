#pragma once

#include <stddef.h>
#include <stdint.h>

namespace vpet {

enum class DateTimeAction : uint8_t { None, Saved, Cancelled };

class DateTimeMenu {
public:
    void begin(bool editingDate, const int values[5], bool spanish = false);
    void next();
    DateTimeAction activate();
    void writeLabel(uint8_t index, char* out, size_t outSize) const;
    static void writeClock(const int values[5], char* out, size_t outSize);
    uint8_t windowStart() const;

    bool editingDate() const { return editingDate_; }
    uint8_t cursor() const { return cursor_; }
    uint8_t count() const { return editingDate_ ? 8 : 6; }
    const int* values() const { return values_; }

private:
    void adjust(uint8_t valueIndex, int delta);
    static int wrap(int value, int min, int max, int delta);

    bool editingDate_ = true;
    bool spanish_ = false;
    uint8_t cursor_ = 0;
    int values_[5] = {2026, 1, 1, 0, 0};
};

}  // namespace vpet
