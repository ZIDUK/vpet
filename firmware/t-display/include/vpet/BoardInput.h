#pragma once

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/task.h>
#include <atomic>
#include "vpet/Input.h"

namespace vpet {

class BoardInput {
public:
    bool begin();
    InputEvent poll(uint32_t nowMs);

private:
    static void sampleTask(void* context);
    QueueHandle_t events_ = nullptr;
    Input input_;
    std::atomic<bool> nextQueued_{false};
};

}  // namespace vpet
