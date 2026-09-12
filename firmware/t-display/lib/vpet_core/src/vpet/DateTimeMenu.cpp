#include "vpet/DateTimeMenu.h"
#include "vpet/Strings.h"

#include <stdio.h>
#include <string.h>

namespace vpet {
namespace {
constexpr int kMinima[] = {2024, 1, 1, 0, 0};
constexpr int kMaxima[] = {2099, 12, 31, 23, 59};

uint8_t valueIndexForRow(bool editingDate, uint8_t cursor) {
    if (editingDate) return static_cast<uint8_t>(cursor / 2);
    return static_cast<uint8_t>(3 + cursor / 2);
}
}

void DateTimeMenu::begin(bool editingDate, const int values[5], bool spanish) {
    editingDate_ = editingDate;
    spanish_ = spanish;
    cursor_ = 0;
    memcpy(values_, values, sizeof(values_));
}

void DateTimeMenu::next() {
    cursor_ = static_cast<uint8_t>((cursor_ + 1) % count());
}

int DateTimeMenu::wrap(int value, int min, int max, int delta) {
    const int next = value + delta;
    if (next > max) return min;
    if (next < min) return max;
    return next;
}

void DateTimeMenu::adjust(uint8_t valueIndex, int delta) {
    values_[valueIndex] = wrap(values_[valueIndex], kMinima[valueIndex], kMaxima[valueIndex], delta);
}

DateTimeAction DateTimeMenu::activate() {
    const uint8_t last = static_cast<uint8_t>(count() - 1);
    if (cursor_ == last) return DateTimeAction::Cancelled;
    if (cursor_ == last - 1) return DateTimeAction::Saved;
    const uint8_t valueIndex = valueIndexForRow(editingDate_, cursor_);
    adjust(valueIndex, cursor_ % 2 == 0 ? 1 : -1);
    return DateTimeAction::None;
}

uint8_t DateTimeMenu::windowStart() const {
    if (cursor_ < 4) return 0;
    return static_cast<uint8_t>(count() - 4);
}

void DateTimeMenu::writeClock(const int values[5], char* out, size_t outSize) {
    snprintf(
        out,
        outSize,
        "%04d/%02d/%02d %02d:%02d",
        values[0],
        values[1],
        values[2],
        values[3],
        values[4]
    );
}

void DateTimeMenu::writeLabel(uint8_t index, char* out, size_t outSize) const {
    const uint8_t last = static_cast<uint8_t>(count() - 1);
    if (index == last) {
        snprintf(out, outSize, "%s", copy::back(spanish_));
        return;
    }
    if (index == last - 1) {
        snprintf(out, outSize, "%s", copy::save(spanish_));
        return;
    }
    const uint8_t valueIndex = valueIndexForRow(editingDate_, index);
    const char* names[] = {
        copy::year(spanish_),
        copy::month(spanish_),
        copy::day(spanish_),
        copy::hour(spanish_),
        copy::minute(spanish_),
    };
    const char sign = index % 2 == 0 ? '+' : '-';
    if (valueIndex == 0) {
        snprintf(out, outSize, "%s %c  %04d", names[valueIndex], sign, values_[valueIndex]);
    } else {
        snprintf(out, outSize, "%s %c  %02d", names[valueIndex], sign, values_[valueIndex]);
    }
}

}  // namespace vpet
