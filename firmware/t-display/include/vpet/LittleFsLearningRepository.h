#pragma once
#include "vpet/LearningRuntime.h"

namespace vpet {
// Single writer on the already mounted LittleFS volume. No formatting or
// recovery writes on construction/read. Referenced policies are never deleted.
class LittleFsLearningRepository final : public LearningRepository {
public:
    static constexpr size_t kMaxBlobBytes=12*1024;
    static constexpr size_t kStorageBudgetBytes=128*1024;
    explicit LittleFsLearningRepository(const char* directory="/littlefs/collection/policies");
    bool read(const std::string& owner, const char* ref, std::string& record) override;
    bool prepare(const std::string& owner, const LearningState& policy, std::string& ref) override;
    bool inspect() { return collect(false); }
    const char* failureReason() const override { return failureReason_; }
    void setInterrupt(bool (*callback)(void*), void* context) override {
        interrupt_ = callback; interruptContext_ = context;
    }
    bool interrupted() const override { return interrupt_ && interrupt_(interruptContext_); }
private:
    bool collect(bool cleanup=true);
    std::string directory_;
    const char* failureReason_ = "none";
    bool (*interrupt_)(void*) = nullptr;
    void* interruptContext_ = nullptr;
};
}  // namespace vpet
