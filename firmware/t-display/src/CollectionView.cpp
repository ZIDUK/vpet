#include "vpet/CollectionPanel.h"
#include "vpet/AssetStore.h"
#include "vpet/PetDefinition.h"
#include <TFT_eSPI.h>
#include <cstdio>

namespace vpet {
namespace {
constexpr uint16_t rgb(int r,int g,int b) { return ((r&248)<<8)|((g&252)<<3)|(b>>3); }
constexpr uint16_t bg=rgb(15,21,25), surface=rgb(30,41,47), selected=rgb(43,54,60);
constexpr uint16_t line=rgb(61,78,85), ink=rgb(239,246,245), muted=rgb(151,172,181);
constexpr uint16_t gold=rgb(255,210,77), mint=rgb(113,225,179), cyan=rgb(106,207,234);
const char* name(uint8_t form,bool es) {
    return form==3 ? (es?"HUEVO":"EGG") : content::builtinDefinition().stage(static_cast<SpeciesId>(form)).name;
}
const char* sexLabel(const CollectionSlot& slot) {
    if (slot.form==3) return "?";
    return slot.profile().sex()==Sex::Male?"M":"F";
}
}

void CollectionPanel::text(int x,int y,const char* value,uint16_t color,int font) {
    canvas_->setTextColor(color,canvas_->readPixel(x,y));
    canvas_->drawString(value,x,y,font);
}
void CollectionPanel::centered(int x,int y,const char* value,uint16_t color) {
    text(x-canvas_->textWidth(value,1)/2,y,value,color);
}
void CollectionPanel::icon(const char* value,int x,int y,int size) {
    if (!assets_) return;
    if (!std::strcmp(value,"egg")) { portraitForm(3,x,y,size); return; }
    char path[48]; std::snprintf(path,sizeof(path),"/ui/icons/%s.vpa",value);
    assets_->drawFrameScaled(*canvas_,path,0,x,y,size,size,false,-1,0,20);
}
void CollectionPanel::button(int x,int width,uint8_t index,const char* image,const char* label) {
    const bool focus=cursor_==index;
    canvas_->fillRect(x,113,width,21,focus?selected:surface);
    canvas_->drawRect(x,113,width,21,focus?gold:line);
    icon(image,x+4,116,14);
    if (label[0]) text(x+22,119,label,focus?gold:ink);
}
void CollectionPanel::portraitForm(uint8_t form,int x,int y,int size,bool flip,bool dim) {
    if (!assets_) return;
    const auto& definition=content::builtinDefinition();
    const auto role=static_cast<SpeciesId>(form);
    const auto& clip=definition.clip(role,content::Action::Idle,content::Context::Training);
    // Installed 68px Training clips avoid a second 88px scratch allocation;
    // eggs use their 36px portrait so the shell is not lost in atlas padding.
    assets_->drawFrameScaled(*canvas_,form==3?definition.stage(role).portrait:clip.path,
        0,x,y,size,size,flip,dim?rgb(53,65,70):-1,0,form==3?36:clip.canvas);
}
void CollectionPanel::portrait(uint8_t index,int x,int y,int size,bool flip,bool dim) {
    if (index<4 && state_.slots[index].occupied) {
        portraitForm(state_.slots[index].form,x,y,size,flip,dim);
    } else if (size<30) centered(x+size/2,y+size/2-4,"+",muted);
    else {
        canvas_->drawRect(x+8,y+5,size-16,size-10,line);
        centered(x+size/2,y+size/2-4,"?",muted);
    }
}

void CollectionPanel::draw(const char* language) {
    if (!canvas_) return;
    const bool es=language && !std::strcmp(language,"ES");
    const bool welcome=page_==Page::Migration || page_==Page::ConfirmMigration;
    const bool pairing=page_==Page::Parents || page_==Page::ConfirmBreed;
    const char* title=es?"COLECCION":"COLLECTION";
    if (welcome) title=es?"TU COLECCION":"YOUR COLLECTION";
    else if (page_==Page::Detail) title=name(state_.slots[selected_].form,es);
    else if (page_==Page::Preferences) title=es?"PREFERENCIAS":"PREFERENCES";
    else if (page_==Page::ConfirmFounder) title=es?"NUEVO HUEVO":"NEW EGG";
    else if (page_==Page::ConfirmSwitch) title=es?"CAMBIAR VPET":"SWITCH VPET";
    else if (page_==Page::ConfirmBreed) title=es?"CONFIRMAR CRUCE":"CONFIRM BREED";
    else if (page_==Page::ConfirmDiscard) title=es?"DESECHAR HUEVO":"DISCARD EGG";
    else if (page_==Page::Parents) title=parentA_==255 ?
        (es?"ELIGE PRIMER VPET":"CHOOSE FIRST VPET"):(es?"ELIGE PAREJA":"CHOOSE PARTNER");
    else if (page_==Page::Error && blockReason_==BlockReason::None) title="ERROR";
    canvas_->fillSprite(bg); canvas_->setTextDatum(TL_DATUM);
    canvas_->fillRect(0,0,240,21,surface); text(7,3,title,ink,2);
    char value[32];
    if (welcome) std::snprintf(value,sizeof(value),"%s",es?"4 PLAZAS":"4 SLOTS");
    else std::snprintf(value,sizeof(value),"%u/4",unsigned(state_.count()));
    text(233-canvas_->textWidth(value,1),6,value,gold);

    if (page_==Page::List) {
        for (uint8_t i=0;i<4;++i) {
            const int x=6+(i%2)*117, y=24+(i/2)*42;
            canvas_->fillRect(x,y,111,40,cursor_==i?selected:surface);
            canvas_->drawRect(x,y,111,40,cursor_==i?gold:line);
            const auto& slot=state_.slots[i];
            if (slot.occupied) {
                portrait(i,x+2,y+2,36);
                text(x+40,y+6,name(slot.form,es),ink);
                text(x+40,y+23,sexLabel(slot),cyan);
                if (i==state_.active) text(x+55,y+23,es?"ACTIVA":"ACTIVE",mint);
            } else {
                text(x+14,y+10,"+",muted,2);
                text(x+40,y+15,es?"LIBRE":"EMPTY",muted);
            }
        }
        button(6,80,4,"egg",es?"HUEVO":"EGG");
        button(93,96,5,"heart",es?"CRUZAR":"BREED"); button(198,36,6,"back");
    } else if (page_==Page::Detail) {
        const auto& slot=state_.slots[selected_]; const bool active=selected_==state_.active;
        const bool discardable=slot.form==static_cast<uint8_t>(SpeciesId::Egg) && !active;
        portrait(selected_,8,27,76);
        text(95,32,sexLabel(slot),cyan,2);
        text(115,34,active?(es?"ACTIVA":"ACTIVE"):(es?"RESERVA":"RESERVE"),active?mint:muted);
        const uint32_t duration=slot.form==3 && slot.incubationRequiredMs ?
            slot.incubationRequiredMs-slot.incubationMs:slot.cooldownMs;
        icon(duration?"clock":"heart",94,57);
        if (duration>=3600000) std::snprintf(value,sizeof(value),"%luh",static_cast<unsigned long>((duration+3599999)/3600000));
        else if (duration) std::snprintf(value,sizeof(value),"%lum",static_cast<unsigned long>((duration+59999)/60000));
        else std::snprintf(value,sizeof(value),"%s",es?"SIN ESPERA":"NO WAIT");
        text(116,61,value,muted);
        const char* actionsEs[]={active?"ACTIVA":"ACTIVAR","CRUZAR","PREFERENCIAS","VOLVER"};
        const char* actionsEn[]={active?"ACTIVE":"SELECT","BREED","PREFERENCES","BACK"};
        const char* images[]={"load","heart","brain","back"};
        if (cursor_==4 && discardable) {
            icon("back",94,82); text(116,86,es?"DESECHAR":"DISCARD",cyan);
        } else {
            icon(images[cursor_%4],94,82); text(116,86,(es?actionsEs:actionsEn)[cursor_%4],cyan);
        }
        button(4,44,0,"load"); button(51,44,1,"heart"); button(98,44,2,"brain");
        button(145,44,3,"back");
        if (discardable) button(192,44,4,"back");
    } else if (pairing) {
        const uint8_t first=parentA_==255?cursor_:parentA_;
        const uint8_t second=page_==Page::ConfirmBreed?selected_:
            (parentA_!=255 && (parentMask_&(1u<<cursor_))?cursor_:255);
        portrait(first,13,26,64); portrait(second,163,26,64,true);
        if (first<4 && state_.slots[first].occupied) centered(45,96,name(state_.slots[first].form,es),ink);
        if (second<4 && state_.slots[second].occupied) centered(195,96,name(state_.slots[second].form,es),ink);
        icon("heart",112,40); canvas_->drawLine(88,70,103,70,line); canvas_->drawLine(137,70,152,70,line);
        if (page_==Page::ConfirmBreed) {
            portraitForm(3,106,66,28); centered(120,96,"30m",cyan);
            button(6,108,0,"back",es?"CANCELAR":"CANCEL"); button(125,109,1,"save",es?"CRUZAR":"BREED");
        } else {
            for (uint8_t i=0;i<4;++i) {
                const int x=8+i*32;
                canvas_->drawRect(x,110,27,25,cursor_==i?gold:parentA_==i?mint:line);
                portrait(i,x+2,111,22,false,!(parentMask_&(1u<<i)) && parentA_!=i);
            }
            button(198,36,4,"back");
            if (!parentMask_) centered(120,97,es?"SIN PAREJA APTA":"NO ELIGIBLE PAIR",muted);
        }
    } else if (page_==Page::Preferences) {
        portrait(selected_,6,30,64);
        const auto* policy=learning_ && selected_==state_.active ? learning_->policy():nullptr;
        const char* images[]={"training","battle","explore"}; const uint8_t counts[]={6,5,3};
        const char* labelsEs[][6]={{"ATAQUE","DEFENSA","VELOCIDAD","VIDA","MP","MENTE"},
            {"GOLPE","LLAMA","GUARDIA","RAFAGA","INFERNO",""},{"PATIO","JORNADA","NOCHE","","",""}};
        const char* labelsEn[][6]={{"ATTACK","DEFENSE","SPEED","HP","MP","BRAIN"},
            {"STRIKE","FLAME","GUARD","BURST","INFERNO",""},{"YARD","JOURNEY","NIGHT","","",""}};
        for (uint8_t domain=0;domain<3;++domain) {
            bool known=false;
            int choice=-1;
            if (policy) {
                int bestScore=-1000;
                for (uint8_t a=0;a<counts[domain];++a) {
                    const auto estimate=policy->estimate(domain,0,a);
                    if (estimate.count || estimate.bias) {
                        known=true;
                        const int score=estimate.mean+estimate.bias;
                        if (score>bestScore) { bestScore=score; choice=a; }
                    }
                }
            }
            icon(images[domain],80,29+domain*25);
            text(104,34+domain*25,choice>=0?(es?labelsEs:labelsEn)[domain][choice]:"---",known?cyan:muted);
        }
        if (selected_!=state_.active) centered(120,102,es?"VPET EN RESERVA":"VPET IN RESERVE",muted);
        button(198,36,0,"back");
    } else if (welcome) {
        portraitForm(previewForm_,8,26,76);
        text(94,34,es?"TU VPET":"YOUR VPET",mint); icon("backpack",94,58);
        text(116,62,es?"MISMA MOCHILA":"SAME BACKPACK",muted);
        text(94,87,es?"PARTIDA CONSERVADA":"PROGRESS KEPT",ink);
        if (page_==Page::Migration) {
            button(6,182,0,"load",es?"ACTIVAR COLECCION":"ENABLE COLLECTION"); button(198,36,1,"back");
        } else {
            button(6,108,0,"back",es?"CANCELAR":"CANCEL"); button(125,109,1,"save",es?"ACTIVAR":"ENABLE");
        }
    } else if (page_==Page::ConfirmFounder || page_==Page::ConfirmSwitch || page_==Page::ConfirmDiscard) {
        const bool egg=page_==Page::ConfirmFounder || page_==Page::ConfirmDiscard;
        if (egg) {
            portraitForm(3,82,23,76);
            text(8,85,es?"1 PLAZA":"1 SLOT",muted);
            const char* tag=es?"SIN OBJETOS":"NO ITEMS"; text(232-canvas_->textWidth(tag,1),85,tag,muted);
        } else {
            portrait(selected_,80,24,76); centered(120,100,name(state_.slots[selected_].form,es),mint);
        }
        if (page_==Page::ConfirmDiscard) text(8,91,es?"EL HUEVO SE ELIMINARA":"EGG WILL BE REMOVED",gold);
        button(6,108,0,"back",es?"CANCELAR":"CANCEL");
        button(125,109,1,"save",page_==Page::ConfirmDiscard?(es?"DESECHAR":"DISCARD"):
            egg?(es?"CREAR":"CREATE"):(es?"ACTIVAR":"SELECT"));
    } else {
        portraitForm(previewForm_,8,29,64);
        if (blockReason_!=BlockReason::None) {
            const char* reasonsEs[]={"","Esta dormido","Crianza pausada","Esta explorando",
                "Entrenamiento activo","Batalla activa","Accion en curso","Guardado pendiente","Almacen bloqueado"};
            const char* reasonsEn[]={"","Pet is asleep","Care is paused","Pet is exploring",
                "Training active","Battle active","Action in progress","Save pending","Storage blocked"};
            const char* hintsEs[]={"","Enciende la luz","Desactiva la pausa","Espera su regreso",
                "Finaliza la sesion","Finaliza la batalla","Espera un momento","Espera un momento","Revisa el guardado"};
            const char* hintsEn[]={"","Turn on the light","Resume care","Wait for return",
                "Finish the session","Finish the battle","Wait a moment","Wait a moment","Check saved data"};
            const auto reason=static_cast<uint8_t>(blockReason_);
            text(84,45,(es?reasonsEs:reasonsEn)[reason],gold);
            text(84,63,(es?hintsEs:hintsEn)[reason],ink);
        } else text(84,45,es?message_:(failed_?"STORAGE ERROR":"NOT AVAILABLE"),gold);
        text(84,84,failed_?(es?"REINICIAR":"RESTART"):(es?"VOLVER":"BACK"),muted);
        button(198,36,0,"back");
    }
    canvas_->pushSprite(0,0);
}
}  // namespace vpet
