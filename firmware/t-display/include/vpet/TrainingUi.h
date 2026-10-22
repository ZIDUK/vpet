#pragma once

#include <stdio.h>
#include <string.h>
#include "generated/TrainingArtwork.h"
#include "vpet/TrainingSession.h"
#include "vpet/PracticeSession.h"

namespace vpet {
namespace training_ui {
constexpr uint16_t rgb(int r, int g, int b) {
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
}
constexpr uint16_t ink = rgb(19,23,27), white = rgb(242,244,238);
constexpr uint16_t yellow = rgb(255,220,70), muted = rgb(162,181,182);
constexpr uint16_t panel = rgb(36,48,52), teal = rgb(40,74,75);
constexpr uint16_t hp = rgb(241,93,112), mp = rgb(71,191,230), green = rgb(111,208,164);
constexpr uint32_t kActionFrameIntervalMs = 90;
constexpr uint32_t kIdleFrameIntervalMs = 120;
constexpr const char* icons[] = {"attack", "defense", "speed", "hp", "mp", "mind"};
constexpr const char* stats[] = {"off", "def", "spd", "hp", "mp", "brn"};
constexpr const char* actions[] = {"punch", "block", "walk", "walk", "cast", "idle"};

// This renderer is used unchanged by the board and the native pixel-parity test.
// Canvas owns the framebuffer; the renderer never allocates a second screen.
template<class Canvas> class View {
    Canvas& c;
    const TrainingSession& s;
    const PetState& pet;
    uint32_t now;
    bool es;
    using State = TrainingSession::State;

    const char* tr(const char* key) const { return training_assets::copy(key, es); }
    void rect(int x, int y, int w, int h, uint16_t color) { c.fillRect(x,y,w,h,color); }
    void outline(int x, int y, int w, int h, uint16_t color) {
        rect(x,y,w,1,color); rect(x,y+h-1,w,1,color);
        rect(x,y,1,h,color); rect(x+w-1,y,1,h,color);
    }
    void text(int x, int y, const char* value, uint16_t color=white, bool small=false) {
        const auto* font = small ? training_assets::font9 : training_assets::font10;
        int top=16, rasterTop=16;
        for (const unsigned char* p = reinterpret_cast<const unsigned char*>(value); *p; ++p) {
            const auto& g = font[(*p >= 32 && *p <= 126 ? *p : '?') - 32];
            for (int row=0; row<16; ++row) if(g.rows[row]) {
                if(g.rasterTop<rasterTop) rasterTop=g.rasterTop;
                if(g.top<top) top=g.top;
                break;
            }
        }
        y += top-rasterTop;
        for (const unsigned char* p = reinterpret_cast<const unsigned char*>(value); *p; ++p) {
            const auto& glyph = font[(*p >= 32 && *p <= 126 ? *p : '?') - 32];
            for (int row=0; row<16; ++row) {
                uint16_t bits = glyph.rows[row];
                int col = 0;
                while (col < 16) {
                    while (col < 16 && !(bits & (1u << col))) ++col;
                    const int start = col;
                    while (col < 16 && (bits & (1u << col))) ++col;
                    if (col > start) c.fillRect(x+start-2,y+row,col-start,1,color);
                }
            }
            x += glyph.advance;
        }
    }
    template<class... Args> void label(int x, int y, uint16_t color, bool small,
                                       const char* key, Args... args) {
        char line[112];
        snprintf(line,sizeof(line),tr(key),args...);
        text(x,y,line,color,small);
    }
    void asset(const char* name, int x, int y, uint32_t frame=0) {
        char path[64];
        snprintf(path,sizeof(path),"/training/%s.vpa",name);
        c.asset(path,frame,x,y);
    }
    void petAsset(const char* action, int x, int y, uint32_t frame=0) {
        const char* name = "firemon";
        const char* resolved = action;
        switch (pet.species()) {
            case SpeciesId::Egg: name="egg"; resolved="idle"; break;
            case SpeciesId::Baby:
                name="sparkmon";
                if (strcmp(action,"walk")!=0 && strcmp(action,"eat")!=0) resolved="idle";
                break;
            case SpeciesId::Rookie: break;
            case SpeciesId::Champion:
                name="flamemon";
                break;
            case SpeciesId::Ultimate:
                name="dragfiremon";
                break;
        }
        char path[64];
        snprintf(path,sizeof(path),"/training/%s_%s.vpa",name,resolved);
        c.asset(path,frame,x,y);
    }
    int index() const {
        const auto i = trainingIndexFor(s.chosenStat);
        return i < 6 ? i : 0;
    }
    const char* name(int i) const {
        char key[20]; snprintf(key,sizeof(key),"stat.%s",stats[i]);
        return tr(key);
    }
    const char* reason(const char* value) const {
        if (!value || !*value || es) return value ? value : "";
        if (strcmp(value,kTrainingNoEnergy)==0) return "NO ENERGY";
        if (strcmp(value,kTrainingNotFit)==0) return "PET NOT FIT";
        if (strcmp(value,kTrainingEvMaxReason)==0) return "EV MAX";
        if (strcmp(value,"SIN REPS")==0) return "NO REPS";
        return "NOT SAVED";
    }
    int maxReps() const {
        const char* ignored;
        const int max = trainingMaxReps(pet,s.chosenStat,&ignored);
        return max;
    }
    const char* block() const {
        const char* base = trainingBlockReason(pet,s.chosenStat);
        if (*base) return reason(base);
        if (pet.evAt(s.chosenStat)+s.pendingEv >= 252) return reason(kTrainingEvMaxReason);
        if (pet.energy()-s.energyReserved < 8) return reason(kTrainingNoEnergy);
        return "";
    }
    void portrait(bool active=false) {
        const int i = s.state == State::Select ? (s.cursor < 6 ? s.cursor : 5) : index();
        const uint32_t interval = active ? kActionFrameIntervalMs : kIdleFrameIntervalMs;
        petAsset(active ? actions[i] : "idle",0,30,now/interval);
    }
    void info(int i, const char* value) {
        char icon[24]; snprintf(icon,sizeof(icon),"%s10",icons[i]);
        asset(icon,70,25); text(84,24,value,yellow,true);
    }
    void button(int x, const char* key, uint16_t color) {
        outline(x,115,90,18,color);
        text(x+4,118,tr(key),color);
    }
    void header(const char* title, const char* tag, uint16_t color=teal,
                bool icon=true, int tagX=210) {
        rect(0,0,240,20,color);
        if (icon) asset("training",4,2);
        text(26,4,title); text(tagX,4,tag,muted,true);
    }
    void pair() {
        const int real = projectedStatValue(pet,s.chosenStat,0);
        const int projected = projectedStatValue(pet,s.chosenStat,trainingPreviewEv(pet,s.chosenStat,s.pendingEv));
        label(70,41,white,true,"training.session.real_proj",name(index()),real);
        label(170,41,projected != real ? green : white,true,"training.session.proj",projected);
    }
    void feedback() {
        if (!s.message || !*s.message) return;
        rect(0,99,240,12,ink); text(6,99,reason(s.message),hp,true);
    }
    void select(bool drawFooter) {
        char tag[12]; snprintf(tag,sizeof(tag),"%d/8",s.cursor+1);
        header(tr("training.title"),tag); portrait(s.cursor < 6);
        const char* selectBlocked = "";
        if (s.cursor < 6) {
            const CombatStat stat = trainingTypeAt(s.cursor).stat;
            info(s.cursor,name(s.cursor));
            const int real = projectedStatValue(pet,stat,0);
            const int projected = projectedStatValue(pet,stat,trainingPreviewEv(pet,stat,trainingPlanOneRep(pet,stat).evAdded));
            char line[40]; snprintf(line,sizeof(line),"%d > %d (+%d)",real,projected,projected-real);
            rect(66,41,2,19,yellow);
            text(72,41,line,green);
            rect(70,61,165,2,panel);
            rect(70,61,pet.evAt(stat)*165/252,2,green);
            const char* blocked;
            const int reps = trainingMaxReps(pet,stat,&blocked);
            selectBlocked = blocked;
            const int xs[] = {70,126,182};
            const uint16_t accents[] = {green,yellow,mp};
            for (int i=0;i<3;++i) {
                rect(xs[i],73,52,31,panel);
                rect(xs[i],73,52,2,accents[i]);
            }
            text(73,77,"EV",muted,true);
            snprintf(line,sizeof(line),"%d/252",pet.evAt(stat));
            text(73,89,line,green,true);
            text(129,77,es ? "SES" : "SETS",muted,true);
            snprintf(line,sizeof(line),"%d",reps);
            text(129,89,line,yellow,true);
            text(185,77,es ? "COSTE" : "COST",muted,true);
            snprintf(line,sizeof(line),"%d ENE",8);
            text(185,89,line,mp,true);
            if (*blocked) text(70,105,reason(blocked),hp,true);
        } else {
            text(70,24,tr("training.techniques"),yellow);
            {
                int learned=0, equipped=0;
                for(int i=0;i<3;++i) {
                    learned+=pet.practice.learned(i);
                    equipped+=pet.practice.isEquipped(i);
                }
                char line[32];
                snprintf(line,sizeof(line),"%s %d/3",es ? "APRENDIDAS" : "LEARNED",learned);
                text(70,41,line,green,true);
                asset("tech_punch",82,64); asset("tech_flame",136,64); asset("tech_guard",190,64);
                text(74,86,es ? "GOLPE" : "PUNCH",yellow,true);
                text(128,86,es ? "LLAMA" : "FLAME",hp,true);
                text(182,86,es ? "GUARDIA" : "GUARD",mp,true);
                snprintf(line,sizeof(line),"%s %d/2",es ? "EQUIPADAS" : "EQUIPPED",equipped);
                text(70,101,line,muted,true);
            }
        }
        if (!*selectBlocked) feedback();
        if (drawFooter) selectFooter();
    }
public:
    void selectFooter() {
        rect(0,115,240,20,ink);
        for (int i=0;i<8;++i) {
            const int x = 4+i*29;
            const bool selected = s.cursor == i;
            rect(x,115,20,20,selected ? teal : panel);
            outline(x,115,20,20,selected ? yellow : panel);
            outline(x+1,116,18,18,selected ? yellow : panel);
            char icon[24];
            if (i<6) snprintf(icon,sizeof(icon),"%s16",icons[i]);
            else snprintf(icon,sizeof(icon),"%s",i==6 ? "pedia" : "back");
            asset(icon,x+2,117);
        }
    }
private:
    void metric(int y, const char* title, const char* value, uint16_t color) {
        outline(70,y,168,14,panel);
        rect(160,y,1,14,panel);
        text(74,y+1,title,color,true);
        text(166,y+1,value,white,true);
    }
    void prepare() {
        char title[64]; snprintf(title,sizeof(title),tr("training.prepare.title"),name(index()));
        header(title,"B"); portrait(); info(index(),name(index()));
        const int real = projectedStatValue(pet,s.chosenStat,0);
        const auto plan=trainingPlanOneRep(pet,s.chosenStat);
        const int previewEv=trainingPreviewEv(pet,s.chosenStat,plan.evAdded);
        const int projected = projectedStatValue(pet,s.chosenStat,previewEv);
        char value[24];
        snprintf(value,sizeof(value),"%d > %d",real,projected);
        metric(40,es ? "VALOR" : "VALUE",value,green);
        snprintf(value,sizeof(value),"%u/252",pet.evAt(s.chosenStat));
        metric(54,es ? "ENTRENO" : "TRAINING",value,green);
        snprintf(value,sizeof(value),"%d/100",pet.energy());
        metric(68,es ? "ENERGIA" : "ENERGY",value,mp);
        metric(82,es ? "COSTE" : "COST","-8",hp);
        metric(96,es ? "TIEMPO" : "TIME","10s",yellow);
        if (previewEv>plan.evAdded) text(70,106,"MANUAL +1 EV",yellow,true);
        if (!maxReps()) { rect(0,99,240,12,ink); text(6,99,block(),hp,true); }
        button(4,"training.prepare.start",s.secondary ? muted : yellow);
        button(100,"training.prepare.back",s.secondary ? yellow : muted);
        feedback();
    }
    void session() {
        header(tr("training.timed.title"),"10s");
        const uint32_t elapsed = now-s.animationStartedMs;
        const bool active = s.animating && elapsed<kTrainingDurationMs;
        portrait(active);
        info(index(),name(index()));
        char value[24];
        const int previewEv=trainingPreviewEv(pet,s.chosenStat,s.pendingEv);
        snprintf(value,sizeof(value),"%d > %d",projectedStatValue(pet,s.chosenStat,0),projectedStatValue(pet,s.chosenStat,previewEv));
        metric(40,es ? "VALOR" : "VALUE",value,green);
        snprintf(value,sizeof(value),"+%u EV",static_cast<unsigned>(previewEv));
        metric(54,es ? "GANANCIA" : "GAIN",value,green);
        snprintf(value,sizeof(value),"%d > %d",pet.energy(),pet.energy()-s.energyReserved);
        metric(68,es ? "ENERGIA" : "ENERGY",value,mp);
        const uint32_t progress = elapsed<kTrainingDurationMs ? elapsed : kTrainingDurationMs;
        label(70,87,yellow,true,"training.timed.remaining",(kTrainingDurationMs-progress+999)/1000);
        if (previewEv>s.pendingEv) text(70,94,"MANUAL +1 EV",yellow,true);
        rect(70,103,164,3,panel); rect(70,103,progress*164/kTrainingDurationMs,3,green);
        button(4,"training.timed.cancel",yellow);
        feedback();
    }
    void confirm() {
        header(tr("training.confirm.title"),tr("training.result.ok"),teal,false,200);
        portrait();
        char line[64]; snprintf(line,sizeof(line),tr("training.confirm.x_rep"),name(index()),s.repsCompleted);
        info(index(),line); pair();
        label(70,57,green,true,"training.confirm.ev_added",trainingPreviewEv(pet,s.chosenStat,s.pendingEv));
        label(70,72,hp,true,"training.confirm.ene_delta",s.energyReserved);
        label(70,87,muted,true,"training.confirm.effort",s.repsCompleted*8);
        button(4,"training.confirm.confirm",s.secondary ? muted : yellow);
        button(100,"training.confirm.follow",s.secondary ? yellow : muted);
    }
    void cancel() {
        header(tr("training.timed.cancel_title"),"",hp,false);
        text(24,24,tr("training.cancel.body"),muted,true);
        button(4,"training.cancel.follow",s.secondary ? muted : yellow);
        button(100,"training.cancel.discard",s.secondary ? yellow : hp);
    }
    void indicator(int y) {
        text(140,y,tr("training.result.page_summary"),s.resultStats ? muted : yellow,true);
        text(200,y,tr("training.result.page_stats"),s.resultStats ? yellow : muted,true);
    }
    void resultRow(int y, const char* rowName, int before, int delta, int after, uint16_t color) {
        text(72,y,rowName,color,true);
        char value[16];
        snprintf(value,sizeof(value),"%d",before); text(126,y,value,color,true);
        snprintf(value,sizeof(value),"%+d",delta); text(164,y,value,color,true);
        snprintf(value,sizeof(value),"%d",after); text(204,y,value,color,true);
    }
    void result() {
        header(tr("training.result.title"),tr("training.result.ok"),green); portrait();
        const auto& summary = s.lastSummary;
        if (s.resultStats) {
            indicator(24);
            for (int i=0;i<6;++i) {
                const auto stat = trainingTypeAt(i).stat;
                const bool trained = stat==s.chosenStat;
                const int after = pet.evAt(stat);
                const int delta = trained ? summary.evAdded : 0;
                const int before = after-delta;
                const int y = 40+i*12;
                char shortName[5]; snprintf(shortName,sizeof(shortName),"%.4s",name(i));
                text(70,y,shortName,trained ? yellow : white,true);
                outline(108,y,97,7,muted);
                const int beforeWidth=(before*96+126)/252, afterWidth=(after*96+126)/252;
                if (beforeWidth) rect(108,y,beforeWidth+1,7,muted);
                if (afterWidth) rect(108,y,afterWidth+1,7,trained ? yellow : green);
                char value[16]; snprintf(value,sizeof(value),delta ? "%+d" : "%d",delta ? delta : after);
                text(208,y,value,delta ? (trained ? yellow : green) : muted,true);
            }
        } else {
            outline(69,23,170,79,panel);
            for (int x : {121,159,199}) rect(x,23,1,79,panel);
            for (int y : {37,53,69,85}) rect(69,y,170,1,panel);
            text(124,25,es ? "ANTES" : "BEFORE",muted,true);
            text(162,25,es ? "CAMBIO" : "CHANGE",muted,true);
            text(202,25,es ? "AHORA" : "AFTER",muted,true);
            const int evAfter=pet.evAt(s.chosenStat), evBefore=evAfter-summary.evAdded;
            int before=10+pet.ivAt(s.chosenStat)*3+evBefore/6;
            if (before>99) before=99;
            if (s.chosenStat==CombatStat::Hp) before=40+before*2;
            if (s.chosenStat==CombatStat::Mp) before=10+before;
            const int after=projectedStatValue(pet,s.chosenStat,0);
            resultRow(40,name(index()),before,after-before,after,white);
            resultRow(56,tr("training.result.label.ev"),evBefore,summary.evAdded,evAfter,green);
            if (summary.energyCharged) resultRow(72,tr("training.result.label.ene"),
                pet.energy()+summary.energyCharged,-summary.energyCharged,pet.energy(),hp);
            if (summary.effortAdded) resultRow(88,tr("training.result.label.effort"),
                pet.effort() > summary.effortAdded ? pet.effort()-summary.effortAdded : 0,
                summary.effortAdded,pet.effort(),muted);
            indicator(104);
        }
        button(4,"training.timed.repeat",s.resultChoice==0 ? yellow : muted);
        button(100,"training.prepare.back",s.resultChoice==1 ? yellow : muted);
        const uint16_t color = s.resultChoice==2 ? yellow : muted;
        outline(196,115,44,18,color);
        text(200,118,tr("training.result.page_stats"),color);
    }
    void error() {
        header(tr("training.error.title"),"E",hp,false,200);
        text(24,24,tr("training.error.body"),muted,true);
        button(4,"training.error.retry",s.secondary ? muted : yellow);
        button(100,"training.error.discard",s.secondary ? yellow : hp);
    }
public:
    void techniques(const PracticeSession& p) {
        rect(0,0,240,135,ink);
        header(es ? "TECNICAS" : "TECHNIQUES","",teal);
        const char* symbols[] = {"tech_punch","tech_flame","tech_guard","tech_flare","tech_inferno"};
        const char* names[techniques::kCount];
        for (int i=0;i<techniques::kCount;++i) names[i]=es ? techniques::kCatalog[i].es : techniques::kCatalog[i].en;
        char line[32];
        if (p.page == PracticeSession::Page::Tech) {
            text(6,27,es ? "EQUIPADAS" : "EQUIPPED",muted,true);
            int equipped[4]={-1,-1,-1,-1}, count=0;
            const int capacity=pet.techniqueCapacity();
            for(int j=0;j<techniques::kCount && count<capacity;++j) if(pet.practice.isEquipped(j)) equipped[count++]=j;
            snprintf(line,sizeof(line),"%d/%d",count,capacity); text(62,27,line,muted,true);
            for(int slot=0;slot<capacity;++slot) {
                const int x=115+slot*30;
                rect(x,21,26,20,panel);
                if(equipped[slot]>=0) {
                    asset(symbols[equipped[slot]],x+5,23);
                } else text(x+10,27,"-",muted,true);
            }
            rect(5,45,230,1,teal);
            const int i=p.cursor;
            const bool learned=i<techniques::kCount && pet.practice.learned(i,pet.techniqueStage());
            petAsset(learned ? (i==0 ? "punch" : i==2 ? "block" : "cast") : "idle",10,40,
                     now/(learned ? kActionFrameIntervalMs : kIdleFrameIntervalMs));
            for(int j=0;j<techniques::kCount+1;++j) {
                const int x=4+j*20;
                rect(x,107,18,24,i==j ? teal : panel);
                outline(x,107,18,24,i==j ? yellow : panel);
                asset(j<techniques::kCount ? symbols[j] : "back",x+1,111);
            }
            if(i==techniques::kCount) { text(126,52,es ? "VOLVER" : "BACK",yellow); return; }
            text(126,52,learned ? names[i] : "???",yellow);
            text(126,67,learned ? (pet.practice.isEquipped(i) ? (es ? "EQUIPADA" : "EQUIPPED") : (es ? "EN RESERVA" : "IN RESERVE")) : (es ? "BLOQUEADA" : "LOCKED"),learned ? green : muted,true);
            if(learned) {
                asset(i==2 ? "defense10" : "power10",126,82);
                snprintf(line,sizeof(line),"%s %d",es ? "POTENCIA" : "POWER",techniques::kCatalog[i].power);
                text(140,82,i==2 ? (es ? "DANO /2" : "DAMAGE /2") : line,white,true);
                asset("cost10",126,96);
                snprintf(line,sizeof(line),"%s %d MP",es ? "COSTE" : "COST",techniques::kCatalog[i].mp);
                text(140,96,i==2 ? (es ? "RECUPERA 4 MP" : "RESTORE 4 MP") : line,mp,true);
                asset("mastery10",126,110);
                snprintf(line,sizeof(line),"%s %u/100",es ? "DOMINIO" : "MASTERY",pet.practice.mastery[i]);
                text(140,110,line,muted,true);
            } else {
                asset("training10",126,82); text(140,82,es ? "ENTRENAR" : "TRAIN",muted,true);
                asset("lock10",126,96);
                if (pet.techniqueStage() < techniques::kCatalog[i].stage)
                    snprintf(line,sizeof(line),"%s",techniques::kCatalog[i].stage==2 ? "FLAMEMON" : "DRAGFIREMON");
                else snprintf(line,sizeof(line),"%u / %d",pet.practice.training,techniques::kCatalog[i].training);
                text(140,96,line,yellow,true);
            }
            rect(126,125,107,4,panel);
            const int needed=techniques::kCatalog[i].training;
            int width=learned ? pet.practice.mastery[i]*107/100 :
                pet.techniqueStage() < techniques::kCatalog[i].stage ? 0 : pet.practice.training*107/(needed ? needed : 1);
            if(width>107) width=107;
            rect(126,125,width,4,learned ? green : yellow);
            return;
        }
        const int i=p.technique;
        asset(symbols[i],8,25);
        text(32,25,names[i],yellow);
        petAsset(i==0 ? "punch" : i==2 ? "block" : "cast",0,42,now/kActionFrameIntervalMs);
        snprintf(line,sizeof(line),"%d",techniques::kCatalog[i].power);
        metric(43,es ? "POTENCIA" : "POWER",i==2 ? "DANO /2" : line,yellow);
        snprintf(line,sizeof(line),"%d MP",techniques::kCatalog[i].mp);
        metric(57,es ? "USAR" : "USE",i==2 ? "+4 MP" : line,mp);
        snprintf(line,sizeof(line),"%u/100",pet.practice.mastery[i]);
        metric(71,es ? "DOMINIO" : "MASTERY",line,green);
        metric(85,es ? "ENTRENAR" : "TRAIN","-4 ENE",hp);
        text(6,101,p.message,yellow,true);
        const char* commands[]={es ? "ENTRENAR" : "TRAIN",pet.practice.isEquipped(i) ? (es ? "QUITAR" : "REMOVE") : (es ? "EQUIPAR" : "EQUIP"),es ? "VOLVER" : "BACK"};
        for(int j=0;j<3;++j) {
            outline(4+j*78,116,76,18,p.cursor==j ? yellow : panel);
            text(8+j*78,120,commands[j],p.cursor==j ? yellow : muted,true);
        }
    }
    View(Canvas& canvas, const TrainingSession& session, const PetState& p, uint32_t ms, bool spanish)
        : c(canvas), s(session), pet(p), now(ms), es(spanish) {}
    void draw(bool drawSelectFooter = true) {
        rect(0,0,240,135,ink);
        switch(s.state) {
            case State::Select: select(drawSelectFooter); break;
            case State::Prepare: prepare(); break;
            case State::Session: session(); break;
            case State::Confirm: confirm(); break;
            case State::Cancel: cancel(); break;
            case State::Result: result(); break;
            case State::Error: error(); break;
        }
    }
};
} // namespace training_ui
} // namespace vpet
