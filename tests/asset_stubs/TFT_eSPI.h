#pragma once
#include <algorithm>
#include <cstdint>
#include <vector>
class TFT_eSprite {
    int width = 240, height = 135;
public:
    std::vector<uint16_t> pixels = std::vector<uint16_t>(240 * 135);
    explicit TFT_eSprite(TFT_eSprite* = nullptr) {}
    void setColorDepth(int) {}
    void* createSprite(int w, int h) {
        width=w; height=h; pixels.assign(w*h,0); return pixels.data();
    }
    void deleteSprite() { pixels.clear(); }
    void fillSprite(uint16_t color) { std::fill(pixels.begin(), pixels.end(), color); }
    uint16_t readPixel(int x, int y) { return pixels[y*width+x]; }
    void pushImage(int x, int y, int w, int h, const uint16_t* colors) {
        for(int row=0;row<h;++row) for(int col=0;col<w;++col)
            if(x+col>=0 && x+col<width && y+row>=0 && y+row<height)
                pixels[(y+row)*width+x+col]=colors[row*w+col];
    }
};
