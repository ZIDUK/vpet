#pragma once
#include <chrono>
#include <condition_variable>
#include <mutex>
#include <thread>

constexpr int pdPASS=1, pdTRUE=1;
constexpr unsigned portMAX_DELAY=~0U;
struct MockTask {
    std::thread thread;
    std::mutex mutex;
    std::condition_variable wake;
    unsigned notifications=0;
    bool stop=false;
};
using TaskHandle_t=MockTask*;
inline thread_local TaskHandle_t currentTask=nullptr;
inline bool rejectTaskCreation=false;
inline int liveTasks=0;
struct TaskStopped {};
