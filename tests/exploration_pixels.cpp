#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <string>
#include "vpet/ExplorationUi.h"

struct Canvas {
    std::string root;
    uint16_t pixels[240*135] = {};
    void drawPixel(int x,int y,uint16_t color) {
        if(x<0 || x>=240 || y<0 || y>=135) throw std::runtime_error("Exploration pixel out of bounds");
        pixels[y*240+x]=color;
    }
    void fillRect(int x,int y,int w,int h,uint16_t color) {
        for(int yy=y;yy<y+h;++yy) for(int xx=x;xx<x+w;++xx) drawPixel(xx,yy,color);
    }
    void asset(const char* path,uint32_t frame,int x,int y) {
        std::ifstream in(root+path,std::ios::binary);
        if(!in) throw std::runtime_error(std::string("Missing asset: ")+path);
        std::vector<unsigned char> data((std::istreambuf_iterator<char>(in)),{});
        auto u16=[&](int p) { return unsigned(data.at(p)) | (unsigned(data.at(p+1))<<8); };
        auto u32=[&](int p) { return u16(p) | (u16(p+2)<<16); };
        const unsigned w=u16(4),h=u16(6),frames=u16(8),colors=u16(10);
        const unsigned offset=u32(13+colors*2+(frame%frames)*4);
        for(unsigned yy=0;yy<h;++yy) for(unsigned xx=0;xx<w;++xx) {
            const unsigned idx=data.at(offset+yy*w+xx);
            if(idx!=data.at(12)) drawPixel(x+xx,y+yy,u16(13+idx*2));
        }
    }
    void write() {
        std::cout << "P6\n240 135\n255\n";
        for(auto p:pixels) {
            const char rgb[]={char(((p>>11)&31)*255/31),char(((p>>5)&63)*255/63),char((p&31)*255/31)};
            std::cout.write(rgb,3);
        }
    }
};

int main(int argc,char** argv) {
    if(argc!=9) return 2;
    using namespace vpet;
    Canvas c; c.root=argv[1];
    PetState pet;
    pet.restore(static_cast<SpeciesId>(std::stoi(argv[5])),70,70,70,0,90,3600);
    ExplorationSession s;
    s.page=static_cast<ExplorationSession::Page>(std::stoi(argv[2]));
    s.route=static_cast<ExploreRoute>(std::stoi(argv[4])); s.stat=CombatStat::Off;
    s.cursor=std::stoi(argv[6]);
    pet.practice.training=std::stoi(argv[8]);
    const uint64_t now=1791979200, wall=now+std::stoul(argv[7]);
    if(s.page==ExplorationSession::Page::Trip || s.page==ExplorationSession::Page::Recall ||
       s.page==ExplorationSession::Page::Receipt) {
        if(!pet.exploration.start(pet,s.route,s.stat,now)) return 3;
        if(s.page==ExplorationSession::Page::Receipt) pet.exploration.claim(pet,wall);
    }
    exploration_ui::View<Canvas>(c,pet,s,wall,1700,std::string(argv[3])=="ES").draw();
    c.write();
}
