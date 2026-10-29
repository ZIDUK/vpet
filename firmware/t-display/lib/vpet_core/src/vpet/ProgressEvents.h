#pragma once
#include "vpet/Learning.h"

namespace vpet {
// Each implicit consecutive sequence stores domain/context/action/reward in 3 bytes.
class ProgressEvents {
public:
    static constexpr size_t kCapacity=64;
    static bool append(std::string& log, unsigned domain, unsigned context, unsigned action, int reward) {
        if (!valid(log) || log.size()/6>=kCapacity || domain>2 || context>31 || action>7 || reward < -100 || reward>100) return false;
        const uint32_t value=(domain<<16)|(context<<11)|(action<<8)|static_cast<uint8_t>(reward);
        constexpr char hex[]="0123456789abcdef";
        for(int shift=20;shift>=0;shift-=4) log.push_back(hex[(value>>shift)&15]);
        return true;
    }
    static bool valid(const std::string& log) {
        if (log.size()%6 || log.size()/6>kCapacity || log.find_first_not_of("0123456789abcdef")!=std::string::npos) return false;
        for(size_t at=0;at<log.size();at+=6) {
            const auto value=decode(log,at);
            const int reward=static_cast<int8_t>(value&255);
            if ((value>>16)>2 || reward < -100 || reward>100) return false;
        }
        return true;
    }
    static bool replay(const std::string& log, uint64_t base, LearningState& state) {
        if (!valid(log) || state.last_sequence()!=base || base>UINT64_MAX-log.size()/6) return false;
        for(size_t at=0;at<log.size();at+=6) {
            const auto value=decode(log,at);
            if (!state.record(state.next_sequence(),value>>16,(value>>11)&31,(value>>8)&7,static_cast<int8_t>(value&255))) return false;
        }
        return true;
    }
private:
    static uint32_t decode(const std::string& log,size_t at) {
        uint32_t value=0;
        for(size_t i=0;i<6;++i) {
            const char c=log[at+i]; value=(value<<4)|static_cast<unsigned>(c<='9'?c-'0':c-'a'+10);
        }
        return value;
    }
};
}
