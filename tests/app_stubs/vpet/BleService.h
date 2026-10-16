#pragma once
namespace vpet {
enum class BleStatus { Off, Advertising, Connected, Error };
struct BleService {
    bool fail = false, enabled = false;
    bool setEnabled(bool value) { enabled = value && !fail; return !fail; }
    BleStatus status() const { return enabled ? BleStatus::Advertising : BleStatus::Off; }
};
}
