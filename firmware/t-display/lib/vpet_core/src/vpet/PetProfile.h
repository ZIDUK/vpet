#pragma once
#include <stdint.h>
#include <cstdio>
#include <string>

namespace vpet {

// New enum: unrelated to the existing persisted species/action numeric values.
enum class Sex : uint8_t { Unknown = 0, Male = 1, Female = 2 };

class PetProfile {
public:
    bool assigned() const { return !id_.empty(); }
    const std::string& petId() const { return id_; }
    Sex sex() const { return sex_; }
    const std::string& parentA() const { return a_; }
    const std::string& parentB() const { return b_; }
    static PetProfile fromWords(const uint32_t words[4], const std::string& a = "", const std::string& b = "") {
        PetProfile result;
        if (!words) return result;
        char id[33];
        snprintf(id,sizeof(id),"%08lx%08lx%08lx%08lx", static_cast<unsigned long>(words[0]),
                 static_cast<unsigned long>(words[1]),static_cast<unsigned long>(words[2]),
                 static_cast<unsigned long>(words[3]));
        result.decode(std::string("1:")+id+(words[0]&1 ? ":F:" : ":M:")+
                      (a.empty()?"-":a)+":"+(b.empty()?"-":b));
        return result;
    }
    std::string encode() const {
        if (!assigned()) return "";
        return "1:"+id_+(sex_==Sex::Male?":M:":":F:")+(a_.empty()?"-":a_)+":"+(b_.empty()?"-":b_);
    }
    bool decode(const std::string& record) {
        if (record.empty()) { *this=PetProfile(); return true; }
        if (record.size()>103) return false;
        std::string fields[5];
        size_t start=0;
        for (int i=0;i<5;++i) {
            const auto end=record.find(':',start);
            if ((i<4 && end==std::string::npos) || (i==4 && end!=std::string::npos)) return false;
            fields[i]=record.substr(start,end==std::string::npos?end:end-start);
            start=end+1;
        }
        if (fields[0]!="1" || !validId(fields[1]) || (fields[2]!="M" && fields[2]!="F") ||
            fields[3].empty() || fields[4].empty()) return false;
        const auto a=fields[3]=="-"?"":fields[3], b=fields[4]=="-"?"":fields[4];
        if ((!a.empty() || !b.empty()) &&
            (!validId(a) || !validId(b) || a==b || a==fields[1] || b==fields[1])) return false;
        id_=fields[1]; sex_=fields[2]=="M"?Sex::Male:Sex::Female; a_=a; b_=b;
        return true;
    }
private:
    static bool validId(const std::string& id) {
        if (id.size()!=32 || id==std::string(32,'0')) return false;
        return id.find_first_not_of("0123456789abcdef")==std::string::npos;
    }
    std::string id_, a_, b_;
    Sex sex_=Sex::Unknown;
};

using ProfileGenerator = PetProfile (*)();
}  // namespace vpet
