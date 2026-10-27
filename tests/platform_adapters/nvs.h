#pragma once
#include <cstdint>
#include <map>
#include <string>
#include <variant>
#include <cstring>

using nvs_handle_t = unsigned;
using esp_err_t = int;
constexpr int ESP_OK = 0;
constexpr int NVS_READWRITE = 1;
constexpr int NVS_READONLY = 0;
constexpr int ESP_ERR_NVS_NOT_FOUND = 2;

namespace storage_stub {
using Value = std::variant<int32_t, std::string>;
using Namespace = std::map<std::string, Value>;
inline std::map<std::string, Namespace> visible, durable;
inline std::map<nvs_handle_t, std::string> handles;
inline unsigned nextHandle = 0;
inline bool failOpen = false, failSet = false, failCommit = false, failGet = false;
// A failed commit may still have reached flash. Exercise both outcomes.
inline bool persistFailedCommit = false;
inline std::string failCommitKey, failCommitNamespace;
inline int closes = 0, sets = 0, commits = 0;
inline nvs_handle_t lastSetHandle = 0, lastCommitHandle = 0;
inline std::map<nvs_handle_t, std::string> lastKeys;
inline void reboot() {
    visible = durable;
    handles.clear();
    lastKeys.clear();
    failOpen = failSet = failCommit = failGet = persistFailedCommit = false;
    failCommitKey.clear();
    failCommitNamespace.clear();
}
inline esp_err_t set(nvs_handle_t handle, const char* key, Value value) {
    if (failSet || !key || !*key || std::string(key).size() > 15) return 1;
    visible[handles.at(handle)][key] = std::move(value);
    lastKeys[handle] = key;
    lastSetHandle = handle;
    ++sets;
    return ESP_OK;
}
}
inline esp_err_t nvs_open(const char* ns, int, nvs_handle_t* handle) {
    if (storage_stub::failOpen || !ns) return 1;
    *handle = ++storage_stub::nextHandle;
    storage_stub::handles[*handle] = ns;
    return ESP_OK;
}
inline esp_err_t nvs_set_str(nvs_handle_t handle, const char* key, const char* value) {
    if (!value) return 1;
    return storage_stub::set(handle, key, std::string(value));
}
inline esp_err_t nvs_get_str(nvs_handle_t handle,const char* key,char* out,size_t* bytes) {
    if(storage_stub::failGet) return 1;
    const auto& values=storage_stub::visible[storage_stub::handles.at(handle)];
    const auto found=values.find(key);
    if(found==values.end()) return ESP_ERR_NVS_NOT_FOUND;
    if(!std::holds_alternative<std::string>(found->second)) return 1;
    const auto& value=std::get<std::string>(found->second);
    if(out && *bytes<value.size()+1) return 1;
    if(out) std::memcpy(out,value.c_str(),value.size()+1);
    *bytes=value.size()+1; return ESP_OK;
}
inline esp_err_t nvs_set_i32(nvs_handle_t handle, const char* key, int32_t value) {
    return storage_stub::set(handle, key, value);
}
inline esp_err_t nvs_commit(nvs_handle_t handle) {
    using namespace storage_stub;
    ++commits;
    lastCommitHandle = handle;
    const auto& ns = handles.at(handle);
    const bool failed = failCommit || (!failCommitKey.empty() && lastKeys[handle] == failCommitKey &&
        (failCommitNamespace.empty() || failCommitNamespace == ns));
    if (!failed || persistFailedCommit) durable[ns] = visible[ns];
    return failed ? 1 : ESP_OK;
}
inline void nvs_close(nvs_handle_t handle) {
    storage_stub::handles.erase(handle);
    storage_stub::lastKeys.erase(handle);
    ++storage_stub::closes;
}
