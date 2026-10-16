#include "vpet/AdoptedInventory.h"
#include <cstdio>

// Standalone cross-language trace, independent of the Unity test runner.
int main() {
    vpet::AdoptedInventory stock;
    stock.seed();
    for (int i=0;i<vpet::adopted::kCount;++i) {
        const auto& item=vpet::adopted::kItems[i];
        std::printf("{\"item\":\"%s\",\"menu_index\":%d,\"stock\":%u,\"limit\":%u}\n",
            item.id,8+i,stock.count(i),vpet::adopted::limit(i));
    }
    for (int n=0;n<42;++n) {
        const int i=stock.reward();
        std::printf("{\"victory\":%d,\"reward\":\"%s\",\"cursor\":%u,\"rewards\":%u,\"stock\":%u}\n",
            n+1,i<0 ? "" : vpet::adopted::kItems[i].id,stock.cursor,stock.rewards,stock.count(i));
    }
}
