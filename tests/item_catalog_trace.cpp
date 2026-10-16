#include <iostream>
#include "vpet/Strings.h"

int main() {
    for (const auto& item : vpet::items::kCatalog) {
        std::cout << item.id << "|" << static_cast<int>(item.index) << "|"
                  << vpet::copy::itemName(item.index, true) << "|"
                  << vpet::copy::itemName(item.index, false) << "|"
                  << vpet::copy::itemBlurb(item.index, true) << "|"
                  << vpet::copy::itemBlurb(item.index, false) << "|"
                  << vpet::copy::itemIcon(item.index) << "|" << item.stackMax
                  << "|" << item.firmwareAvailable << "\n";
    }
    std::cout << vpet::copy::itemName(6, false) << "|"
              << vpet::copy::itemIcon(6) << "\n";
}
