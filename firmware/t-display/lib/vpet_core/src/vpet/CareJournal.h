#pragma once
#include "vpet/SettingsStore.h"
#include <limits>
#include <sstream>
namespace vpet {
enum class CareLoad { Missing, Loaded, Corrupt, Future, Error };
struct CareRecord {
    uint64_t base=0, revision=0;
    uint32_t elapsedMs=0;
    uint8_t active=0;
    std::string identity, snapshot;
};
class CareJournal {
public:
    static constexpr size_t kMaxBytes=3950;
    explicit CareJournal(KeyValueStore& store) : store_(store) {}
    const CareRecord& record() const { return record_; }
    bool present() const { return present_; }
    bool settled() const { return settled_; }
    uint32_t fingerprint() const { return token_; }
    static uint32_t checksum(const std::string& value) {
        uint32_t crc=~uint32_t(0);
        for (unsigned char c : value) {
            crc^=c;
            for(int bit=0;bit<8;++bit) crc=(crc>>1)^((crc&1)?0xedb88320U:0);
        }
        return ~crc;
    }
    static std::string encode(const CareRecord& record) {
        if (!record.base || !record.revision || record.active>=4 || record.identity.size()!=32 ||
            record.identity==std::string(32,'0') ||
            record.identity.find_first_not_of("0123456789abcdef")!=std::string::npos ||
            record.snapshot.empty() || record.snapshot.size()>3800) return "";
        const std::string payload="VPCJ1\n"+std::to_string(record.base)+"\n"+
            std::to_string(record.revision)+"\n"+std::to_string(record.active)+"\n"+
            std::to_string(record.elapsedMs)+"\n"+record.identity+"\n"+record.snapshot;
        const std::string result=payload+"CRC "+std::to_string(checksum(payload))+"\n";
        return result.size()<=kMaxBytes?result:"";
    }
    static CareLoad decode(const std::string& raw, CareRecord& out) {
        if (raw.size()>kMaxBytes || raw.find('\0')!=std::string::npos) return CareLoad::Corrupt;
        if (raw.compare(0,6,"VPCJ1\n"))
            return raw.compare(0,4,"VPCJ")==0?CareLoad::Future:CareLoad::Corrupt;
        const auto end=raw.rfind("CRC ");
        if (end==std::string::npos || !end || raw[end-1]!='\n' || raw.back()!='\n') return CareLoad::Corrupt;
        uint64_t expected=0;
        if (!unsignedValue(raw.substr(end+4,raw.size()-end-5),expected,UINT32_MAX) ||
            checksum(raw.substr(0,end))!=expected) return CareLoad::Corrupt;
        std::istringstream input(raw.substr(0,end));
        std::string line; std::getline(input,line);
        CareRecord next; uint64_t value=0;
        if (!std::getline(input,line) || !unsignedValue(line,next.base,UINT64_MAX) || !next.base ||
            !std::getline(input,line) || !unsignedValue(line,next.revision,UINT64_MAX) || !next.revision ||
            !std::getline(input,line) || !unsignedValue(line,value,3)) return CareLoad::Corrupt;
        next.active=value;
        if (!std::getline(input,line) || !unsignedValue(line,value,UINT32_MAX)) return CareLoad::Corrupt;
        next.elapsedMs=value;
        if (!std::getline(input,next.identity)) return CareLoad::Corrupt;
        const auto at=input.tellg();
        if (at<0 || static_cast<size_t>(at)>=end) return CareLoad::Corrupt;
        next.snapshot=raw.substr(static_cast<size_t>(at),end-static_cast<size_t>(at));
        if (encode(next)!=raw) return CareLoad::Corrupt;
        out=std::move(next); return CareLoad::Loaded;
    }
    CareLoad load() {
        if (!store_.sync()) return CareLoad::Error;
        std::string raw; const auto read=store_.readString("colCare",raw);
        if (read==StoreRead::Error) return CareLoad::Error;
        if (read==StoreRead::Missing) {
            record_=CareRecord(); token_=0; present_=false; loaded_=settled_=true;
            return CareLoad::Missing;
        }
        CareRecord next; const auto result=decode(raw,next);
        if (result!=CareLoad::Loaded) { loaded_=false; return result; }
        record_=std::move(next); token_=checksum(raw); present_=loaded_=settled_=true;
        return CareLoad::Loaded;
    }
    bool settle() {
        if (!loaded_ || !store_.sync()) return false;
        std::string raw; const auto result=store_.readString("colCare",raw);
        if (result==StoreRead::Error || (present_ ? result!=StoreRead::Present || checksum(raw)!=token_
                                               : result!=StoreRead::Missing)) return false;
        settled_=true; return true;
    }
    bool save(CareRecord next) {
        if (!settle() || record_.revision==UINT64_MAX) return false;
        next.revision=record_.revision+1;
        const auto raw=encode(next);
        if (raw.empty()) return false;
        const auto result=store_.commitString("colCare",raw.c_str());
        if (result==StoreCommit::Rejected) return false;
        record_=std::move(next); token_=checksum(raw); present_=true;
        settled_=result==StoreCommit::Committed;
        return true;
    }
private:
    static bool unsignedValue(const std::string& text, uint64_t& value, uint64_t limit) {
        if (text.empty() || text.find_first_not_of("0123456789")!=std::string::npos) return false;
        uint64_t next=0;
        for (char c:text) {
            const auto digit=static_cast<uint64_t>(c-'0');
            if (digit>limit || next>(limit-digit)/10) return false;
            next=next*10+digit;
        }
        value=next; return true;
    }
    KeyValueStore& store_;
    CareRecord record_;
    uint32_t token_=0;
    bool present_=false, loaded_=false, settled_=false;
};
}
