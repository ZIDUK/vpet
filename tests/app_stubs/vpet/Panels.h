#pragma once
namespace vpet {
struct Panels {
    int errors = 0;
    void invalidate() {}
    void drawStorageError(const char*) { ++errors; }
    template<class... T> void draw(T&&...) {}
    template<class... T> void drawPractice(T&&...) {}
    template<class... T> void drawTraining(T&&...) {}
};
}
