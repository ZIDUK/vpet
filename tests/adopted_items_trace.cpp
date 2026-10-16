#include <iostream>
#include "vpet/ConsumableEffects.h"
int main() {
    for (int p : {20, 50, 90, 100})
        std::cout << vpet::consumables::recovered(0, 86, p) << ' ';
    vpet::practice::Fighter f;
    uint8_t stock = 2;
    std::cout << vpet::consumables::boost(f, stock, 2, 20) << ' ';
    std::cout << f.stats[2] << ' ';
    std::cout << vpet::consumables::boost(f, stock, 2, 20) << ' ' << int(stock);
}
