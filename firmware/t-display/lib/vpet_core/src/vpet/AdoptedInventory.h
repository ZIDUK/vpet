#pragma once
#include "vpet/AdoptedItems.generated.h"
#include <string>
#include <sstream>
#include <cstring>
#include <limits>

namespace vpet { namespace adopted {
inline int indexOf(const char* id) {
    for (uint8_t i=0; i<kCount; ++i) if (!strcmp(id,kItems[i].id)) return i;
    return -1;
}
inline uint8_t limit(int i) {
    if (i<0 || i>=kCount || kItems[i].unlimited) return 0;
    return kItems[i].stackMax;
}
}
class AdoptedInventory {
public:
    uint32_t cursor = 0, rewards = 0;
    uint8_t count(int i) const { return i>=0 && i<adopted::kCount ? stock_[i] : 0; }
    void set(int i, int value) {
        if (i<0 || i>=adopted::kCount) return;
        stock_[i] = value<0 ? 0 : value>adopted::limit(i) ? adopted::limit(i) : value;
    }
    void seed() {
        *this = AdoptedInventory();
        for (uint8_t i=0;i<adopted::kCount;++i) set(i,adopted::kItems[i].initialStock);
    }
    int reward() {
        for (uint8_t n=0; n<adopted::kCount; ++n) {
            const int i=(cursor+n)%adopted::kCount;
            if (count(i)>=adopted::limit(i)) continue;
            set(i,count(i)+1);
            cursor=(i+1)%adopted::kCount;
            if (rewards<std::numeric_limits<uint32_t>::max()) ++rewards;
            return i;
        }
        return -1;
    }
    std::string encode() const {
        std::ostringstream out;
        out << "1 " << cursor << ' ' << rewards;
        for (uint8_t i=0; i<adopted::kCount; ++i)
            if (adopted::limit(i)) out << ' ' << adopted::kItems[i].id << ' ' << int(count(i));
        return out.str();
    }
    bool decode(const std::string& record) {
        if (record.empty()) { seed(); return true; }
        std::istringstream in(record);
        int version;
        int64_t parsedCursor;
        AdoptedInventory next;
        if (!(in>>version>>parsedCursor>>next.rewards) || version!=1) return false;
        next.cursor=parsedCursor<0 ? 0 : parsedCursor%adopted::kCount;
        std::string id;
        int value;
        while (in>>id) {
            if (!(in>>value)) return false;
            next.set(adopted::indexOf(id.c_str()), value);
        }
        *this=next;
        return true;
    }
private:
    uint8_t stock_[adopted::kCount] = {};
};
}
