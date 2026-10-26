#pragma once

#include <atomic>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include "vpet/SaveTask.h"

namespace vpet {

class FreeRtosSaveTask final : public SaveTask {
public:
    ~FreeRtosSaveTask() override {
        wait();
        if (task_) vTaskDelete(task_);
    }
    bool start(Work work, void* context) override {
        if (!work || state_.load(std::memory_order_acquire) != State::Idle) return false;
        if (!task_ && xTaskCreate(run, "vpet-save", 8192, this, 1, &task_) != pdPASS) {
            task_ = nullptr;
            return false;
        }
        work_ = work;
        context_ = context;
        state_.store(State::Pending, std::memory_order_release);
        xTaskNotifyGive(task_);
        return true;
    }
    bool finished() const override { return state_.load(std::memory_order_acquire) == State::Done; }
    void reset() override {
        if (finished()) state_.store(State::Idle, std::memory_order_release);
    }
    void wait() override {
        while (state_.load(std::memory_order_acquire) == State::Pending) vTaskDelay(1);
    }

private:
    enum class State { Idle, Pending, Done };
    static void run(void* context) {
        auto& self = *static_cast<FreeRtosSaveTask*>(context);
        for (;;) {
            ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
            if (self.state_.load(std::memory_order_acquire) != State::Pending) continue;
            self.work_(self.context_);
            self.state_.store(State::Done, std::memory_order_release);
        }
    }
    std::atomic<State> state_{State::Idle};
    TaskHandle_t task_ = nullptr;
    Work work_ = nullptr;
    void* context_ = nullptr;
};

}  // namespace vpet
