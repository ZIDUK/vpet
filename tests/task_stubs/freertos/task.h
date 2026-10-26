#pragma once
#include "FreeRTOS.h"

inline int xTaskCreate(void (*fn)(void*),const char*,unsigned,void* context,int,TaskHandle_t* out) {
    if(rejectTaskCreation) return 0;
    auto* task=new MockTask;
    *out=task; ++liveTasks;
    task->thread=std::thread([=] {
        currentTask=task;
        try { fn(context); } catch(const TaskStopped&) {}
    });
    return pdPASS;
}
inline void xTaskNotifyGive(TaskHandle_t task) {
    std::lock_guard<std::mutex> lock(task->mutex);
    ++task->notifications; task->wake.notify_one();
}
inline unsigned ulTaskNotifyTake(int,unsigned) {
    auto& task=*currentTask;
    std::unique_lock<std::mutex> lock(task.mutex);
    task.wake.wait(lock,[&] { return task.stop || task.notifications; });
    if(task.stop) throw TaskStopped();
    auto count=task.notifications; task.notifications=0; return count;
}
inline void vTaskDelay(unsigned ticks) { std::this_thread::sleep_for(std::chrono::milliseconds(ticks)); }
inline void vTaskDelete(TaskHandle_t task) {
    { std::lock_guard<std::mutex> lock(task->mutex); task->stop=true; task->wake.notify_one(); }
    task->thread.join(); delete task; --liveTasks;
}
