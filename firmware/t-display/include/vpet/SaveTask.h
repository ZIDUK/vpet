#pragma once

namespace vpet {

// Capacity one. finished() is the acquire barrier for everything written by work.
// Work/context stay alive until wait()/finished(); reset only after completion.
class SaveTask {
public:
    using Work = void (*)(void*);
    virtual ~SaveTask() = default;
    virtual bool start(Work work, void* context) = 0;
    virtual bool finished() const = 0;
    virtual void reset() = 0;
    virtual void wait() = 0;
};

}  // namespace vpet
