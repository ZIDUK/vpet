#include <iostream>
#include "vpet/Strings.h"

int main() {
    for (uint8_t index=0; index<8+vpet::adopted::kCount; ++index) {
        std::cout << vpet::copy::itemName(index,true) << "\n"
                  << vpet::copy::itemName(index,false) << "\n";
    }
}
