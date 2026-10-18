#pragma once
#include <stdio.h>
#include <string.h>
#include "generated/TrainingArtwork.h"
#include "vpet/ExplorationSession.h"
#include "vpet/MenuBar.h"

namespace vpet { namespace exploration_ui {
constexpr uint16_t rgb(int r, int g, int b) { return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3); }
constexpr uint16_t ink = rgb(16,22,26), panel = rgb(32,47,51), selected = rgb(40,74,75);
constexpr uint16_t white = rgb(234,238,219), muted = rgb(156,178,179), green = rgb(102,204,160);
constexpr uint16_t yellow = rgb(255,217,61), cyan = rgb(77,190,217), pink = rgb(241,93,112);

template<class Canvas> class View {
    Canvas& c;
    const PetState& pet;
    const ExplorationSession& s;
    uint64_t wall;
    uint32_t ms;
    bool es;
    using Page = ExplorationSession::Page;
    void rect(int x,int y,int w,int h,uint16_t color) { c.fillRect(x,y,w,h,color); }
    void outline(int x,int y,int w,int h,uint16_t color) {
        rect(x,y,w,1,color); rect(x,y+h-1,w,1,color); rect(x,y,1,h,color); rect(x+w-1,y,1,h,color);
    }
    const char* tr(const char* spanish,const char* english) const { return es ? spanish : english; }
    const char* routeName(ExploreRoute route) const {
        return route == ExploreRoute::Patio ? "PATIO" : route == ExploreRoute::Jornada ? tr("JORNADA","SHIFT") : tr("NOCHE","NIGHT");
    }
    const char* statName(CombatStat stat) const {
        const char* namesEs[] = {"VIDA","MP","ATAQUE","DEFENSA","VELOCIDAD","MENTE"};
        const char* namesEn[] = {"HP","MP","ATTACK","DEFENSE","SPEED","MIND"};
        return (es ? namesEs : namesEn)[static_cast<uint8_t>(stat) % 6];
    }
    const char* statIcon(CombatStat stat, bool tiny) const {
        const char* small[] = {"/training/hp10.vpa","/training/mp10.vpa","/training/attack10.vpa",
            "/training/defense10.vpa","/training/speed10.vpa","/training/mind10.vpa"};
        const char* large[] = {"/training/hp16.vpa","/training/mp16.vpa","/training/attack16.vpa",
            "/training/defense16.vpa","/training/speed16.vpa","/training/mind16.vpa"};
        return (tiny ? small : large)[static_cast<uint8_t>(stat) % 6];
    }
    void text(int x,int y,int w,int h,const char* value,uint16_t color=white,bool large=false,bool right=false) {
        const auto* font = large ? training_assets::font12 : training_assets::font10;
        char fitted[96]; snprintf(fitted,sizeof(fitted),"%s",value);
        int minx=0,miny=0,maxx=-1,maxy=-1;
        for (;;) {
            minx=10000; miny=16; maxx=maxy=-1;
            int cursor=0;
            for (const unsigned char* p=reinterpret_cast<const unsigned char*>(fitted);*p;++p) {
                const auto& g=font[(*p>=32 && *p<=126 ? *p : '?')-32];
                for(int yy=0;yy<16;++yy) for(int xx=0;xx<16;++xx) if(g.rows[yy]&(1u<<xx)) {
                    const int px=cursor+xx-2;
                    if(px<minx) minx=px; if(px>maxx) maxx=px;
                    if(yy<miny) miny=yy; if(yy>maxy) maxy=yy;
                }
                cursor+=g.advance;
            }
            if(maxx-minx+1<=w || !*fitted) break;
            fitted[strlen(fitted)-1]='\0';
        }
        if(maxx<minx) return;
        const int originX=x+(right ? w-(maxx-minx+1) : 0)-minx;
        const int originY=y+(h-(maxy-miny+1))/2-miny;
        int cursor=0;
        for(const unsigned char* p=reinterpret_cast<const unsigned char*>(fitted);*p;++p) {
            const auto& g=font[(*p>=32 && *p<=126 ? *p : '?')-32];
            for(int yy=0;yy<16;++yy) for(int xx=0;xx<16;++xx) if(g.rows[yy]&(1u<<xx)) {
                const int px=originX+cursor+xx-2, py=originY+yy;
                if(px>=x && px<x+w && py>=y && py<y+h) c.drawPixel(px,py,color);
            }
            cursor+=g.advance;
        }
    }
    void icon(const char* path,int x,int y) { c.asset(path,0,x,y); }
    void portrait(bool walking=false,int x=5,int y=55) {
        const char* names[] = {"firemon","flamemon","dragfiremon","egg","sparkmon"};
        char path[80];
        const bool walk=walking && pet.species()!=SpeciesId::Egg;
        snprintf(path,sizeof(path),"/exploration/%s_%s%d.vpa",names[static_cast<uint8_t>(pet.species())],
                 walk ? "walk" : "idle",walk ? 28 : 48);
        c.asset(path,ms/(walk ? 70 : 85),x,y);
    }
    void heading(const char* label) { rect(0,24,240,20,panel); text(8,25,224,17,label,yellow,true); }
    void button(int i,int count,const char* label,bool outlined=false) {
        const int width=232/count, x=4+i*width;
        const bool focus=s.cursor==i;
        const uint16_t bg=outlined ? ink : focus ? yellow : panel;
        rect(x,116,width-4,18,bg);
        if(outlined) outline(x,116,width-4,18,focus ? yellow : muted);
        text(x+5,117,width-10,16,label,outlined ? (focus ? yellow : muted) : focus ? ink : white);
    }
    void row(int y,const char* name,const char* value,const char* path,uint16_t accent=green,int h=11) {
        rect(70,y,168,h,ink); outline(70,y,168,h,panel); rect(160,y,1,h,panel);
        icon(path,73,y+(h-10)/2);
        text(86,y+1,70,h-2,name,accent);
        text(166,y+1,68,h-2,value);
    }
    void attribute(int y,const ExploreReward& r,int height=11) {
        if(r.route==ExploreRoute::Jornada) row(y,tr("ATRIBUTO","STAT"),statName(r.stat),statIcon(r.stat,true),green,height);
        else if(r.route==ExploreRoute::Patio) row(y,tr("RECURSO","RESOURCE"),"ENE","/exploration/energy10.vpa",cyan,height);
        else row(y,tr("TECNICA","TECHNIQUE"),tr("LLAMA","FLAME"),"/training/mastery10.vpa",yellow,height);
    }
    void rewardRows(const ExploreReward& r,bool confirm) {
        char amount[32];
        if(r.route==ExploreRoute::Patio) snprintf(amount,sizeof(amount),"+%u ENE",r.energy);
        else if(r.route==ExploreRoute::Jornada) snprintf(amount,sizeof(amount),"+%u EV",r.ev);
        else if(r.learning) snprintf(amount,sizeof(amount),"%s",r.learned ? tr("APRENDIDA","LEARNED") : "1/2");
        else snprintf(amount,sizeof(amount),"+%u DOM",r.mastery);
        const int h=confirm ? 14 : 11;
        if(!confirm) {
            char time[20]; formatTime(r.elapsed,time,sizeof(time));
            row(60,tr("TIEMPO","TIME"),time,"/exploration/clock10.vpa",cyan);
        }
        attribute(confirm ? 60 : 71,r,h);
        row(confirm ? 73 : 82,tr("PREMIO","REWARD"),amount,"/training/training10.vpa",green,h);
        row(confirm ? 86 : 93,tr("OBJETO","ITEM"),r.guide ? tr("GUIA","GUIDE") : "--",
            r.guide ? "/exploration/itemguide10.vpa" : "/training/training10.vpa",r.guide ? yellow : muted,h);
        if(confirm) row(99,tr("COSTE","COST"),"0 ENE","/exploration/energy10.vpa",pink,h);
    }
public:
    View(Canvas& canvas,const PetState& p,const ExplorationSession& session,uint64_t now,uint32_t animation,bool spanish)
        : c(canvas),pet(p),s(session),wall(now),ms(animation),es(spanish) {}
    static void formatTime(uint32_t seconds,char* out,size_t size) {
        snprintf(out,size,"%02u:%02u:%02u",seconds/3600,(seconds%3600)/60,seconds%60);
    }
    void draw(bool home=false,uint8_t menu=3,bool chrome=true) {
        rect(0,chrome ? 0 : 24,240,chrome ? 135 : 111,ink);
        if(chrome) for(uint8_t i=0;i<menu_bar::count;++i) icon(menu_bar::icons[i],menu_bar::iconX(i),2);
        outline(menu_bar::left(menu),0,menu_bar::width(menu),24,yellow);
        outline(menu_bar::left(menu)+1,1,menu_bar::width(menu)-2,22,yellow);
        if(!ExplorationSession::eligible(pet)) {
            heading(tr("EXPLORAR","EXPLORE")); portrait();
            text(70,64,165,18,tr("DESDE FIREMON","FROM FIREMON"),muted);
            button(0,1,tr("VOLVER","BACK")); return;
        }
        if(s.page==Page::Clock) {
            heading(tr("AJUSTAR RELOJ","SET THE CLOCK")); portrait();
            text(70,62,165,16,tr("HORA NO FIABLE","CLOCK NOT SET"),yellow);
            text(70,82,165,14,tr("FECHA Y HORA","DATE AND TIME"),muted);
            if(!home) { button(0,2,tr("AJUSTAR","SET")); button(1,2,tr("VOLVER","BACK")); }
            return;
        }
        if(s.page==Page::Routes || s.page==Page::Stats) {
            const bool stats=s.page==Page::Stats;
            heading(stats ? tr("ELEGIR ATRIBUTO","CHOOSE A STAT") : tr("EXPLORAR","EXPLORE"));
            const int count=s.count(pet), start=s.cursor==0 ? 0 : (s.cursor-1<count-3 ? s.cursor-1 : count-3);
            for(int slot=0;slot<3;++slot) {
                const int item=start+slot,y=46+slot*29;
                rect(5,y,230,27,item==s.cursor ? selected : panel);
                if(item==s.cursor) rect(5,y,3,27,yellow);
                const bool back=item==count-1;
                if(stats || back) {
                    icon(back ? "/training/back.vpa" : statIcon(static_cast<CombatStat>(item),false),13,y+5);
                    text(39,y+4,189,19,back ? tr("VOLVER","BACK") : statName(static_cast<CombatStat>(item)),item==s.cursor ? yellow : white,true);
                } else {
                    const auto route=static_cast<ExploreRoute>(item);
                    const char* path=item==0 ? "/ui/icons/energy.vpa" : item==1 ? "/ui/icons/itemguide.vpa" : "/ui/icons/pedia.vpa";
                    icon(path,12,y+4);
                    text(39,y+1,149,13,routeName(route),item==s.cursor ? yellow : white,true);
                    text(194,y+1,35,13,item==0 ? "30m" : "8h",cyan,false,true);
                    const char* reward=item==0 ? tr("RECUPERA ENERGIA","RESTORES ENERGY") : item==1 ? tr("+2 EV Y GUIA","+2 EV AND GUIDE") : tr("APRENDE / DOMINA LLAMA","LEARN / MASTER FLAME");
                    text(39,y+16,191,10,reward,muted);
                }
            }
        } else if(s.page==Page::Confirm) {
            heading(tr("PREPARAR SALIDA","READY TO LEAVE")); portrait();
            PetState projected=pet;
            projected.exploration.start(projected,s.route,s.stat,wall);
            const auto r=projected.exploration.preview(projected,wall+Exploration::duration(s.route));
            text(70,46,120,13,routeName(s.route),yellow,true);
            text(194,46,39,13,s.route==ExploreRoute::Patio ? "30m" : "8h",cyan,false,true);
            rewardRows(r,true);
            text(4,105,61,10,r.good ? tr("BIEN","GOOD") : tr("ATENDER","NEEDS CARE"),r.good ? green : yellow);
            button(0,2,tr("ENVIAR","SEND"),true); button(1,2,tr("VOLVER","BACK"),true);
        } else if(s.page==Page::Receipt || s.page==Page::Recall || pet.exploration.remaining(wall)==0) {
            const bool saved=s.page==Page::Receipt;
            const auto r=saved ? pet.exploration.receipt : pet.exploration.preview(pet,wall);
            heading(saved ? tr("RECOMPENSAS GUARDADAS","REWARDS SAVED") : s.page==Page::Recall ? tr("REGRESO ANTICIPADO","EARLY RETURN") : tr("DE VUELTA","BACK FROM TRIP"));
            portrait(); text(70,46,163,13,routeName(r.route),yellow,true); rewardRows(r,false);
            text(70,104,163,10,saved ? tr("YA GUARDADO","ALREADY SAVED") : tr("POR RECLAMAR","TO CLAIM"),saved ? green : yellow);
            if(home) text(8,117,224,16,tr("PREMIO POR RECLAMAR","REWARD TO CLAIM"),yellow);
            else if(saved) button(0,1,tr("CONTINUAR","CONTINUE"));
            else if(s.page==Page::Recall) { button(0,2,tr("VOLVER","BACK")); button(1,2,tr("RECLAMAR","CLAIM")); }
            else { button(0,2,tr("RECLAMAR","CLAIM")); button(1,2,tr("VOLVER","BACK")); }
        } else {
            heading(tr("EXPLORANDO","EXPLORING"));
            const auto& e=pet.exploration;
            const uint32_t remaining=e.remaining(wall), duration=Exploration::duration(e.route);
            text(8,48,126,15,routeName(e.route),white,true);
            char time[20]; formatTime(remaining,time,sizeof(time)); text(142,48,90,15,time,cyan,true);
            const int x=18+202ULL*(duration-remaining)/duration;
            rect(18,84,203,2,muted); rect(18,84,x-18+1,2,green);
            for(int tick : {18,119,220}) rect(tick-2,82,5,5,white);
            portrait(true,x<32 ? 4 : x>224 ? 210 : x-14,56);
            const bool newWeek=(wall+259200)/604800>e.week;
            char week[50]; snprintf(week,sizeof(week),"%s %u/8 EV  %u/4 DOM",tr("SEMANA","WEEK"),newWeek ? 0 : e.weekEv,newWeek ? 0 : e.weekMastery);
            text(8,96,224,12,week,muted);
            if(!home) { button(0,2,tr("VOLVER","BACK")); button(1,2,tr("REGRESAR","RETURN")); }
        }
        if(s.saveFailed) { rect(0,100,240,15,ink); text(5,100,230,15,tr("NO GUARDADO. REINTENTAR","NOT SAVED. RETRY"),pink); }
    }
};
} }
