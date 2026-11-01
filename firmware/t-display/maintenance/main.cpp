// Temporary USB-only reader. It never starts the game or modifies user files.
#include <Arduino.h>
#include <LittleFS.h>
#include <mbedtls/sha256.h>

namespace {
bool mounted = false;

bool safePath(const char* path) {
    if (!path || path[0] != '/' || strlen(path) > 192 || strstr(path,"..")) return false;
    for (const char* p=path; *p; ++p)
        if (!isalnum(static_cast<unsigned char>(*p)) && !strchr("/._-",*p)) return false;
    return true;
}

void hexDigest(const uint8_t* digest, char* output) {
    static const char* digits="0123456789abcdef";
    for (int i=0;i<32;++i) { output[2*i]=digits[digest[i]>>4]; output[2*i+1]=digits[digest[i]&15]; }
    output[64]=0;
}

bool readFile(File& file, bool stream, char* sha) {
    mbedtls_sha256_context context;
    mbedtls_sha256_init(&context);
    bool ok=mbedtls_sha256_starts_ret(&context,0)==0;
    uint8_t buffer[256], digest[32];
    char encoded[513];
    size_t total=0;
    while (ok && total<file.size()) {
        const int n=file.read(buffer,sizeof(buffer));
        if (n<=0) { ok=false; break; }
        ok=mbedtls_sha256_update_ret(&context,buffer,n)==0;
        if (stream && ok) {
            static const char* digits="0123456789abcdef";
            for (int i=0;i<n;++i) { encoded[2*i]=digits[buffer[i]>>4]; encoded[2*i+1]=digits[buffer[i]&15]; }
            encoded[2*n]=0;
            Serial.printf("MAINT DATA %s\n",encoded);
        }
        total+=n;
        if (stream || !(total%16384)) delay(1);
    }
    if (ok) ok=mbedtls_sha256_finish_ret(&context,digest)==0;
    mbedtls_sha256_free(&context);
    if (ok) hexDigest(digest,sha);
    return ok;
}

bool inventory(const char* path, unsigned& count, unsigned depth=0) {
    if (depth>8) return false;
    File directory=LittleFS.open(path,"r");
    if (!directory || !directory.isDirectory()) return false;
    for (File entry=directory.openNextFile(); entry; entry=directory.openNextFile()) {
        const String name=entry.path();
        if (!safePath(name.c_str())) return false;
        if (entry.isDirectory()) {
            entry.close();
            if (!inventory(name.c_str(),count,depth+1)) return false;
        } else {
            char sha[65];
            const size_t size=entry.size();
            if (!readFile(entry,false,sha) || ++count>4096) return false;
            Serial.printf("MAINT FILE %s %u %s\n",name.c_str(),unsigned(size),sha);
            entry.close();
        }
    }
    return true;
}

void command(const char* line) {
    if (!mounted) { Serial.println("MAINT ERR mount"); return; }
    if (!strcmp(line,"VPET MAINT INVENTORY")) {
        Serial.println("MAINT BEGIN");
        unsigned count=0;
        if (inventory("/",count)) Serial.printf("MAINT END %u\n",count);
        else Serial.println("MAINT ERR inventory");
    } else if (!strncmp(line,"VPET MAINT READ ",16)) {
        const char* path=line+16;
        if (!safePath(path)) { Serial.println("MAINT ERR path"); return; }
        File file=LittleFS.open(path,"r");
        if (!file || file.isDirectory()) { Serial.println("MAINT ERR file"); return; }
        Serial.printf("MAINT READ %s %u\n",path,unsigned(file.size()));
        char sha[65];
        if (readFile(file,true,sha)) Serial.printf("MAINT DONE %s\n",sha);
        else Serial.println("MAINT ERR read");
    } else Serial.println("MAINT ERR command");
}
}

void setup() {
    Serial.begin(115200);
    mounted=LittleFS.begin(false,"/littlefs",16,"littlefs");
    Serial.println(mounted ? "MAINT READY protocol=1 mode=read-only" : "MAINT ERR mount");
}

void loop() {
    static char line[224];
    static size_t used=0;
    static bool overflow=false;
    while (Serial.available()) {
        const char c=Serial.read();
        if (c=='\r') continue;
        if (c=='\n') {
            line[used]=0;
            if (overflow) Serial.println("MAINT ERR line");
            else command(line);
            used=0; overflow=false;
        } else if (used+1<sizeof(line)) line[used++]=c;
        else overflow=true;
    }
    delay(1);
}
