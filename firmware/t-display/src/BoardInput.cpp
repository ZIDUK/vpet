#include "vpet/BoardInput.h"

namespace vpet {
namespace {
constexpr uint8_t kNextPin = 0;
constexpr uint8_t kActionPin = 35;
}

bool BoardInput::begin() {
    pinMode(kNextPin, INPUT_PULLUP);
    pinMode(kActionPin, INPUT);
    events_ = xQueueCreate(32, sizeof(InputEvent));
    if (!events_) return false;
    if (xTaskCreate(sampleTask, "vpet-buttons", 2048, this, 2, nullptr) != pdPASS) {
        vQueueDelete(events_);
        events_ = nullptr;
        return false;
    }
    return true;
}

void BoardInput::sampleTask(void* context) {
    auto& self = *static_cast<BoardInput*>(context);
    TickType_t wake = xTaskGetTickCount();
    for (;;) {
        const InputEvent event = self.input_.poll(
            {digitalRead(kNextPin) == LOW, digitalRead(kActionPin) == LOW}, millis());
        // Long press supersedes queued NEXT repeats, even during a slow redraw.
        if (event == InputEvent::Back) {
            xQueueReset(self.events_);
            self.nextQueued_.store(false);
        }
        const bool shouldQueue = event == InputEvent::Next
            ? !self.nextQueued_.exchange(true)
            : event != InputEvent::None;
        if (shouldQueue && xQueueSend(self.events_, &event, 0) != pdTRUE) {
            if (event == InputEvent::Next) self.nextQueued_.store(false);
            // Bounded queue: report overload instead of silently losing input.
            Serial.println("VPET_INPUT_OVERFLOW");
        }
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(5));
    }
}

InputEvent BoardInput::poll(uint32_t /*nowMs*/) {
    InputEvent event = InputEvent::None;
    if (events_) xQueueReceive(events_, &event, 0);
    if (event == InputEvent::Next) nextQueued_.store(false);
    return event;
}

}  // namespace vpet
