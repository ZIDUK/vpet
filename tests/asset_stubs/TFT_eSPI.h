#pragma once
#include <algorithm>
#include <cstdint>
#include <vector>
#include <string>
#include <cmath>
#define TFT_BLACK 0x0000
#define TFT_WHITE 0xFFFF
#define TFT_YELLOW 0xFFE0
#define TFT_GREEN 0x07E0
#define TFT_RED 0xF800
#define TFT_CYAN 0x07FF
#define TFT_DARKGREY 0x7BEF
#define TFT_LIGHTGREY 0xD69A
#define TL_DATUM 0
#define TC_DATUM 1
#define TR_DATUM 2
#define MC_DATUM 4
class TFT_eSPI {
public:
    void startWrite() {}
    void endWrite() {}
};
class TFT_eSprite {
    int width = 240, height = 135;
    bool swapBytes = false;
    uint16_t textForeground = 0, textBackground = 0;
public:
    struct TextDraw { std::string value; int x, y; uint16_t foreground, background; };
    std::vector<uint16_t> pixels = std::vector<uint16_t>(240 * 135);
    std::vector<std::string> labels;
    std::vector<TextDraw> textDraws;
    explicit TFT_eSprite(TFT_eSprite* = nullptr) {}
    void setColorDepth(int) {}
    void setSwapBytes(bool enabled) { swapBytes=enabled; }
    void* getPointer() { return pixels.data(); }
    void* createSprite(int w, int h) {
        width=w; height=h; pixels.assign(w*h,0); return pixels.data();
    }
    void deleteSprite() { pixels.clear(); }
    void fillSprite(uint16_t color) { std::fill(pixels.begin(), pixels.end(), color); }
    uint16_t readPixel(int x, int y) { return x>=0 && x<width && y>=0 && y<height ? pixels[y*width+x] : 0; }
    void drawPixel(int x,int y,uint16_t color) {
        if(x>=0 && x<width && y>=0 && y<height) pixels[y*width+x]=color;
    }
    void fillRect(int x,int y,int w,int h,uint16_t color) {
        for(int yy=std::max(y,0);yy<std::min(y+h,height);++yy)
            for(int xx=std::max(x,0);xx<std::min(x+w,width);++xx) drawPixel(xx,yy,color);
    }
    void drawRect(int x,int y,int w,int h,uint16_t color) {
        fillRect(x,y,w,1,color); fillRect(x,y+h-1,w,1,color);
        fillRect(x,y,1,h,color); fillRect(x+w-1,y,1,h,color);
    }
    void fillRoundRect(int x,int y,int w,int h,int,uint16_t color) { fillRect(x,y,w,h,color); }
    void drawRoundRect(int x,int y,int w,int h,int,uint16_t color) { drawRect(x,y,w,h,color); }
    void fillScreen(uint16_t color) { fillSprite(color); }
    void fillCircle(int x,int y,int r,uint16_t color) {
        for(int yy=-r;yy<=r;++yy) for(int xx=-r;xx<=r;++xx)
            if(xx*xx+yy*yy<=r*r) drawPixel(x+xx,y+yy,color);
    }
    void drawLine(int x,int y,int x1,int y1,uint16_t color) {
        const int steps=std::max(std::abs(x1-x),std::abs(y1-y));
        for(int i=0;i<=steps;++i) drawPixel(x+(x1-x)*i/std::max(steps,1),y+(y1-y)*i/std::max(steps,1),color);
    }
    void setTextDatum(int) {}
    void setTextColor(uint16_t foreground,uint16_t background) {
        textForeground=foreground; textBackground=background;
    }
    // Capture labels; these tests exercise production sprite draws, not TFT font rasterization.
    int textWidth(const std::string& value,int font=1) { return int(value.size())*(font==1 ? 6 : 8); }
    void drawString(const std::string& value,int x,int y,int=1) {
        labels.push_back(value);
        textDraws.push_back({value,x,y,textForeground,textBackground});
    }
    void drawNumber(int value,int x,int y,int font=1) { drawString(std::to_string(value),x,y,font); }
    void pushSprite(int,int) {}
    void pushImage(int x, int y, int w, int h, const uint16_t* colors) {
        for(int row=0;row<h;++row) for(int col=0;col<w;++col)
            if(x+col>=0 && x+col<width && y+row>=0 && y+row<height)
                pixels[(y+row)*width+x+col]=swapBytes ? colors[row*w+col] :
                    uint16_t((colors[row*w+col] >> 8) | (colors[row*w+col] << 8));
    }
};
