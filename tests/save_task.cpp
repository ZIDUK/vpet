#include <cassert>
#include <atomic>
#include "vpet/FreeRtosSaveTask.h"

struct Job {
    std::atomic<bool> entered{false}, release{false};
    int result=0;
    static void run(void* context) {
        auto& self=*static_cast<Job*>(context);
        self.entered.store(true);
        while(!self.release.load()) vTaskDelay(1);
        self.result=42;
    }
};
template<class Check> void eventually(Check check) {
    const auto until=std::chrono::steady_clock::now()+std::chrono::seconds(2);
    while(!check()) { assert(std::chrono::steady_clock::now()<until); vTaskDelay(1); }
}
int main() {
    {
        vpet::FreeRtosSaveTask task;
        Job job;
        rejectTaskCreation=true;
        assert(!task.start(Job::run,&job) && !task.finished() && liveTasks==0);
        rejectTaskCreation=false;
        assert(!task.start(nullptr,&job));
        assert(task.start(Job::run,&job));
        eventually([&] { return job.entered.load(); });
        assert(!task.finished() && !task.start(Job::run,&job) && liveTasks==1);
        task.reset(); // Must not release a running job's slot.
        assert(!task.start(Job::run,&job));
        job.release.store(true);
        eventually([&] { return task.finished(); });
        assert(job.result==42 && !task.start(Job::run,&job));
        task.reset();
        for(int i=0;i<30;++i) {
            Job next; next.release.store(true);
            assert(task.start(Job::run,&next));
            task.wait(); assert(task.finished() && next.result==42);
            task.reset(); assert(liveTasks==1);
        }
    }
    assert(liveTasks==0);
    // Destruction must wait until the borrowed job/context is no longer used.
    Job pending;
    auto* task=new vpet::FreeRtosSaveTask;
    assert(task->start(Job::run,&pending));
    std::thread release([&] { vTaskDelay(10); pending.release.store(true); });
    delete task; release.join();
    assert(pending.result==42 && liveTasks==0);
}
