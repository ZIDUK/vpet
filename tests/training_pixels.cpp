#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <string>
#include "vpet/TrainingUi.h"

struct Canvas {
    std::string root;
    uint16_t pixels[240*135] = {};
    void drawPixel(int x, int y, uint16_t color) {
        if (x>=0 && x<240 && y>=0 && y<135) pixels[y*240+x]=color;
        else throw std::runtime_error("Training pixel outside 240x135");
    }
    void fillRect(int x,int y,int w,int h,uint16_t color) {
        for (int yy=y;yy<y+h;++yy) for(int xx=x;xx<x+w;++xx) drawPixel(xx,yy,color);
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
        for(auto pixel:pixels) {
            const char rgb[]={char(((pixel>>11)&31)*255/31),char(((pixel>>5)&63)*255/63),char((pixel&31)*255/31)};
            std::cout.write(rgb,3);
        }
    }
};

int main(int argc,char** argv) {
    if(argc!=10 && argc!=12) return 2;
    Canvas c; c.root=argv[1];
    vpet::PetState pet;
    pet.restore(vpet::SpeciesId::Rookie,50,std::stoi(argv[8]),80,0,80,3600);
    const uint8_t dna[]={0xab,0xcd,0xef,0x12}; pet.restoreDna(dna);
    uint8_t ev[]={60,24,30,12,18,0};
    if (std::stoi(argv[2]) >= 7) {
        vpet::PracticeSession p;
        p.page=std::stoi(argv[2])==7 ? vpet::PracticeSession::Page::Tech : vpet::PracticeSession::Page::Detail;
        p.technique=std::stoi(argv[4]); p.cursor=std::stoi(argv[5]);
        pet.practice.training=3; pet.practice.bond=55;
        if(argc==12) {
            pet.practice.training=std::stoi(argv[10]);
            pet.practice.equipped=std::stoi(argv[11]);
        }
        pet.practice.mastery[0]=12; pet.practice.mastery[1]=20; pet.practice.mastery[2]=30;
        const vpet::TrainingSession unused;
        vpet::training_ui::View<Canvas>(c,unused,pet,std::stoul(argv[7]),std::string(argv[3])=="ES").techniques(p);
        c.write(); return 0;
    }
    vpet::TrainingSession s;
    s.cursor=std::stoi(argv[4]);
    s.chosenStat=vpet::trainingTypeAt(s.cursor).stat; s.chosenStatValid=true;
    ev[static_cast<int>(s.chosenStat)]=std::stoi(argv[9]); pet.restoreEv(ev);
    s.state=static_cast<vpet::TrainingSession::State>(std::stoi(argv[2]));
    s.secondary=std::stoi(argv[5])==1;
    s.focus=s.secondary ? vpet::TrainingSession::Focus::Finalize : vpet::TrainingSession::Focus::Train;
    s.repsCompleted=std::stoi(argv[6]); s.pendingEv=s.repsCompleted*6; s.energyReserved=s.repsCompleted*8;
    const uint32_t ms=std::stoul(argv[7]);
    if(s.state==vpet::TrainingSession::State::Session && ms<10000 && s.repsCompleted) {
        s.animating=true; s.animationStartedMs=0;
    }
    if(s.state==vpet::TrainingSession::State::Result) {
        s.captureSnapshot(pet);
        s.lastSummary=vpet::trainingApply(pet,s.chosenStat,s.repsCompleted);
        s.resultStats=s.secondary;
        s.resultChoice=*vpet::trainingBlockReason(pet,s.chosenStat) ? 1 : 0;
    }
    vpet::training_ui::View<Canvas>(c,s,pet,ms,std::string(argv[3])=="ES").draw();
    c.write();
}
