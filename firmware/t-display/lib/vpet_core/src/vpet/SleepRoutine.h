#pragma once
#include <stdint.h>
#include <cstdlib>
#include <algorithm>
#include <sstream>
#include <string>

namespace vpet {
struct SleepRoutine {
    int bedtime=0, target=0, samples=0, learnedNight=-1;
    bool asleep=false;
    int elapsed=0, required=0, carry=0, sessionNight=-1, sessionMinute=0, trait=1;
    int rewardNight=-1, subMs=0;
    bool physicalTired=false;
    static bool isNight(int minute) { return minute>=1080 || minute<360; }
    int preferred(int dnaTrait) const { return bedtime ? bedtime : 1080+(2-dnaTrait%3)*15; }
    bool tired(int energy, int dnaTrait, int minute=-1) {
        if (asleep) return false;
        const int threshold=20+dnaTrait%3*5;
        if (energy<=threshold) physicalTired=true;
        else if (energy>=threshold+10) physicalTired=false;
        return physicalTired || (minute>=0 && (minute>=preferred(dnaTrait) || minute<360));
    }
    bool start(uint64_t civilSeconds,int dnaTrait) {
        if (asleep) return false;
        trait=dnaTrait%3;
        sessionMinute=civilSeconds%86400/60;
        const bool night=civilSeconds>=1704067200ULL && isNight(sessionMinute);
        sessionNight=night ? static_cast<int>((civilSeconds-21600)/86400) : -1;
        const int untilDawn=(21600+86400-civilSeconds%86400)%86400;
        required=night ? std::max(28800,untilDawn) : 1800;
        elapsed=carry=subMs=0; asleep=true;
        return true;
    }
    void learn() {
        if (sessionNight<=learnedNight || sessionMinute<1080 || sessionMinute>1380) return;
        learnedNight=sessionNight;
        if (samples && std::abs(target-sessionMinute)<=30) {
            samples=std::min(3,samples+1); target=(target+sessionMinute)/2;
        } else { target=sessionMinute; samples=1; }
        if (samples==3) bedtime=std::max(1080,std::min(1380,preferred(trait)+
            std::max(-15,std::min(15,target-preferred(trait)))));
    }
    void stop() { asleep=false; }
    bool advance(uint32_t seconds,int& energy,bool& reward) {
        reward=false;
        if (!asleep) return false;
        const int delta=std::min(seconds,static_cast<uint32_t>(required-elapsed));
        elapsed+=delta;
        energy=std::min(100,energy+(carry+delta)/300);
        carry=(carry+delta)%300;
        if (elapsed<required) return false;
        asleep=false;
        if (sessionNight>=0) { learn(); reward=sessionNight>rewardNight; rewardNight=std::max(rewardNight,sessionNight); }
        return true;
    }
    bool advanceMs(uint32_t milliseconds,int& energy,bool& reward) {
        if (!asleep) { reward=false; return false; }
        const uint64_t total=static_cast<uint64_t>(subMs)+milliseconds;
        subMs=total%1000;
        return advance(total/1000,energy,reward);
    }
    std::string encode() const {
        std::ostringstream out;
        out<<1<<','<<bedtime<<','<<target<<','<<samples<<','<<learnedNight<<','<<asleep<<','
            <<elapsed<<','<<required<<','<<carry<<','<<sessionNight<<','<<sessionMinute<<','
            <<trait<<','<<rewardNight<<','<<subMs;
        return out.str();
    }
    bool decode(const std::string& value) {
        if (value.empty()) { *this=SleepRoutine(); return true; }
        std::istringstream in(value);
        int v[14]; char comma;
        for (int i=0;i<14;++i) {
            if (!(in>>v[i]) || (i<13 && (!(in>>comma) || comma!=','))) return false;
        }
        if (in>>comma || v[0]!=1 || (v[1]!=0 && (v[1]<1080 || v[1]>1380)) ||
            (v[2]!=0 && (v[2]<1080 || v[2]>1380)) || v[3]<0 || v[3]>3 ||
            v[4]<-1 || v[4]>100000 || v[5]<0 || v[5]>1 || v[6]<0 || v[6]>v[7] ||
            v[7]<0 || v[7]>43200 || v[8]<0 || v[8]>=300 || v[9]<-1 || v[9]>100000 ||
            v[10]<0 || v[10]>=1440 || v[11]<0 || v[11]>2 || v[12]<-1 || v[12]>100000 ||
            v[13]<0 || v[13]>=1000 || (v[5] && v[7]<1800)) return false;
        SleepRoutine next;
        next.bedtime=v[1]; next.target=v[2]; next.samples=v[3]; next.learnedNight=v[4];
        next.asleep=v[5]; next.elapsed=v[6]; next.required=v[7]; next.carry=v[8];
        next.sessionNight=v[9]; next.sessionMinute=v[10]; next.trait=v[11];
        next.rewardNight=v[12]; next.subMs=v[13];
        *this=next; return true;
    }
};
}
