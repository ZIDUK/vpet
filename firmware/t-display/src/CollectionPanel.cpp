#include "vpet/CollectionPanel.h"

#include <TFT_eSPI.h>
#include <algorithm>
#include <array>
#include <cstdio>
#include <limits>
#include <memory>
#include <new>
#include "vpet/AssetStore.h"
#include "vpet/Breeding.h"
#include "vpet/OptionMenu.h"
#include "vpet/PetDefinition.h"

namespace vpet {
namespace {
const char* form(uint8_t value) {
    const char* labels[] = {"FIREMON", "FLAMEMON", "DRAGFIREMON", "HUEVO", "SPARKMON"};
    return value < 5 ? labels[value] : "?";
}
breeding::Parent parent(const PetState& pet, const CollectionSlot& slot) {
    breeding::Parent p;
    p.pet_id=pet.profile.petId(); p.sex=pet.profile.sex()==Sex::Male ? "M" : "F";
    p.line_id=slot.lineage; p.adult=pet.techniqueStage()>0;
    p.health=pet.health(); p.hunger=pet.hunger(); p.energy=pet.energy(); p.happiness=pet.happiness();
    p.injured=pet.injured(); p.dead=pet.dead(); p.asleep=pet.sleep.asleep;
    p.away=pet.exploration.away(); p.paused=pet.cold(); p.busy=pet.pendingAction()!=Action::None;
    p.cooldown_remaining=slot.cooldownMs;
    p.parents={pet.profile.parentA(),pet.profile.parentB()};
    for (size_t i=0;i<4;++i) p.grandparents[i]=slot.ancestors[i];
    return p;
}
}

CollectionPanel::CollectionPanel(CollectionStore& store, SettingsStore& legacy, ProfileGenerator profiles,
                                 SeedGenerator seeds, TFT_eSprite* canvas, AssetStore* assets, LearningRuntime* learning)
    : store_(store), legacy_(legacy), profiles_(profiles), seeds_(seeds), canvas_(canvas), assets_(assets), learning_(learning) {}

CollectionLoad CollectionPanel::load(PetState& pet, Settings& settings) {
    pendingElapsed_=0;
    const auto result=store_.load(state_);
    if (result==CollectionLoad::Missing) {
        if (failed_) return CollectionLoad::Error;
        enabled_=false; return result;
    }
    if (result!=CollectionLoad::Loaded || !store_.readPet(state_,state_.active,pet,settings)) {
        error("Almacen no disponible",true); return CollectionLoad::Error;
    }
    if (learning_ && !learning_->load(state_.slots[state_.active])) {
        error("Politica no disponible",true); return CollectionLoad::Error;
    }
    enabled_=true; failed_=false; return CollectionLoad::Loaded;
}

void CollectionPanel::error(const char* message, bool storage) {
    message_=message; page_=Page::Error; cursor_=0;
    if (storage) failed_=true;
}
bool CollectionPanel::flush() {
    if (!pendingElapsed_) return !failed_;
    if (!store_.advance(state_,pendingElapsed_,false)) { error("Error al guardar",true); return false; }
    pendingElapsed_=0; return true;
}
bool CollectionPanel::save(const PetState& pet, const Settings& settings) {
    if (!enabled_ || failed_ || !flush() || !store_.saveActive(state_,pet,settings)) {
        error("Error al guardar",true); return false;
    }
    return true;
}
bool CollectionPanel::saveExperience(const PetState& pet, const Settings& settings,
                                    const RuntimeExperience* events, size_t count) {
    if (!count) return save(pet,settings);
    if (!enabled_ || failed_ || !learning_ || !flush() ||
        !learning_->commit(store_,state_,pet,settings,events,count)) {
        error("Error al guardar politica",true); return false;
    }
    return true;
}
int CollectionPanel::chooseAuto(const practice::Fighter& fighter, uint8_t learnedMask) const {
    if (learning_ && enabled_ && !failed_) return learning_->chooseAuto(fighter,learnedMask);
    practice::Fighter fixed=fighter; fixed.autoSelector=nullptr; fixed.autoContext=nullptr;
    return practice::choose(fixed);
}
bool CollectionPanel::advance(uint32_t elapsedMs, bool paused) {
    if (!enabled_) return !failed_;
    if (failed_) return false;
    if (paused) return true;
    // Checkpoint only trusted powered-on deltas. begin/load always discard RAM
    // remainder, so reboot can lose at most a minute and never grants time.
    if (elapsedMs>std::numeric_limits<uint32_t>::max()-pendingElapsed_) {
        if (!flush()) return false;
    }
    pendingElapsed_+=elapsedMs;
    const auto& active=state_.slots[state_.active];
    const bool hatchDue=active.form==static_cast<uint8_t>(SpeciesId::Egg) && active.incubationRequiredMs &&
        pendingElapsed_>=active.incubationRequiredMs-active.incubationMs;
    return (!hatchDue && pendingElapsed_<60000) || flush();
}
bool CollectionPanel::timedEgg() const {
    return enabled_ && state_.slots[state_.active].incubationRequiredMs!=0;
}
bool CollectionPanel::hatchReady() const {
    if (!timedEgg()) return true;
    const auto& egg=state_.slots[state_.active];
    return egg.incubationMs>=egg.incubationRequiredMs;
}
void CollectionPanel::open() {
    changedActive_=false; cursor_=0; parentA_=255;
    page_=failed_ ? Page::Error : enabled_ ? Page::List : Page::Migration;
}
bool CollectionPanel::migrate(PetState& pet, Settings& settings) {
    std::string active, backup; bool present=false;
    if (!legacy_.exportLegacySnapshots(active,backup,present)) {
        error("Migracion bloqueada",true); return false;
    }
    // Allocate missing identities only for the explicitly confirmed candidate.
    // Both originals are retained; the durable collection is the commit marker.
    PetProfile missingActive, missingBackup;
    std::unique_ptr<PetState> old(new (std::nothrow) PetState); Settings ignored;
    if (!old) { error("Memoria no disponible",true); return false; }
    if (!CollectionStore::restore(active,*old,ignored)) { error("Activo no valido",true); return false; }
    if (!old->profile.assigned() && profiles_) missingActive=profiles_();
    if (present) {
        if (!CollectionStore::restore(backup,*old,ignored)) { error("Reserva no valida",true); return false; }
        if (!old->profile.assigned() && profiles_) missingBackup=profiles_();
    }
    // Migration confirms the live individual, including care not checkpointed
    // in legacy NVS. Originals were validated above and remain untouched.
    if (!CollectionStore::capture(pet,settings,active)) { error("Activo no valido",true); return false; }
    if (!store_.migrate(state_,active,present?&backup:nullptr,missingActive,missingBackup) ||
        !store_.readPet(state_,state_.active,pet,settings)) {
        error("Migracion bloqueada",true); return false;
    }
    if (learning_ && !learning_->load(state_.slots[state_.active])) {
        error("Politica no disponible",true); return false;
    }
    enabled_=true; changedActive_=true; pendingElapsed_=0; page_=Page::List; cursor_=0; return true;
}
bool CollectionPanel::founder(const PetState& pet, const Settings& settings) {
    if (state_.count()>=CollectionState::kSlots) { error("Cuatro plazas ocupadas"); return false; }
    if (!profiles_ || !seeds_) { error("Identidad no disponible"); return false; }
    if (!save(pet,settings)) return false;
    std::unique_ptr<PetState> egg(new (std::nothrow) PetState);
    if (!egg) { error("Memoria no disponible",true); return false; }
    egg->profile=profiles_(); egg->rollDna(seeds_());
    egg->restoreItems(0,0,0,0,0,0); egg->adoptedStock=AdoptedInventory();
    if (!store_.addFounder(state_,*egg,settings,true)) { error("Fundador no guardado",store_.blocked()); return false; }
    page_=Page::List; cursor_=0; return true;
}
bool CollectionPanel::eligible(const PetState& pet, size_t a, size_t b) {
    if (a>=4 || b>=4 || a==b || !state_.slots[a].occupied || !state_.slots[b].occupied) return false;
    std::unique_ptr<PetState> loaded(new (std::nothrow) PetState); Settings ignored;
    if (!loaded) { error("Memoria no disponible",true); return false; }
    if (!store_.readPet(state_,a,*loaded,ignored)) { error("Error al leer padres",true); return false; }
    const auto first=parent(a==state_.active?pet:*loaded,state_.slots[a]);
    if (!store_.readPet(state_,b,*loaded,ignored)) { error("Error al leer padres",true); return false; }
    return breeding::check_pair(first,parent(b==state_.active?pet:*loaded,state_.slots[b]));
}
bool CollectionPanel::breed(const PetState& pet, const Settings& settings) {
    if (state_.count()>=4) { error("Cuatro plazas ocupadas"); return false; }
    if (!eligible(pet,parentA_,selected_)) { if (!failed_) error("Padres no elegibles"); return false; }
    if (!learning_ && (state_.slots[parentA_].learningRef[0] || state_.slots[selected_].learningRef[0])) {
        error("Herencia no disponible"); return false;
    }
    if (!profiles_ || !seeds_ || state_.sequence==std::numeric_limits<uint64_t>::max()) {
        error("Identidad no disponible"); return false;
    }
    if (!save(pet,settings)) return false;
    CollectionEggTransaction tx; tx.id=state_.sequence+1; tx.seed=seeds_();
    tx.parentA=parentA_; tx.parentB=selected_;
    std::unique_ptr<PetState> loaded(new (std::nothrow) PetState); Settings ignored;
    if (!loaded) { error("Memoria no disponible",true); return false; }
    std::array<uint8_t,4> dnaA,dnaB;
    if (!store_.readPet(state_,parentA_,*loaded,ignored)) { error("Error al leer padres",true); return false; }
    std::copy(loaded->dna(),loaded->dna()+4,dnaA.begin());
    if (!store_.readPet(state_,selected_,*loaded,ignored)) { error("Error al leer padres",true); return false; }
    std::copy(loaded->dna(),loaded->dna()+4,dnaB.begin());
    const auto dna=breeding::offspring_dna(dnaA,dnaB,static_cast<uint32_t>(tx.seed));
    const auto identity=profiles_();
    const auto a=state_.slots[parentA_].profile(), b=state_.slots[selected_].profile();
    *loaded=PetState();
    const std::string profileRecord="1:"+identity.petId()+(identity.sex()==Sex::Male?":M:":":F:")+a.petId()+":"+b.petId();
    if (!identity.assigned() || !loaded->profile.decode(profileRecord)) { error("Identidad no disponible"); return false; }
    if (learning_) {
        std::string inheritedRef;
        if (!learning_->inherit(state_.slots[parentA_],state_.slots[selected_],loaded->profile,inheritedRef) || inheritedRef.size()>64) {
            error("Error al heredar politica",true); return false;
        }
        std::snprintf(tx.learningRef,sizeof(tx.learningRef),"%s",inheritedRef.c_str());
    }
    loaded->restoreDna(dna.data()); loaded->restoreItems(0,0,0,0,0,0); loaded->adoptedStock=AdoptedInventory();
    size_t child=0;
    if (!store_.commitEgg(state_,tx,*loaded,settings,child,true)) { error("Cruce no guardado",store_.blocked()); return false; }
    page_=Page::List; cursor_=child; parentA_=255; return true;
}

bool CollectionPanel::input(InputEvent event, PetState& pet, Settings& settings, const CollectionSwitchGuard& guard) {
    changedActive_=false;
    if (event==InputEvent::None) return false;
    if (event==InputEvent::Back) {
        if (page_==Page::List || page_==Page::Migration || page_==Page::Error) return true;
        page_=enabled_?Page::List:Page::Migration; cursor_=enabled_ && selected_<7?selected_:0; parentA_=255; return false;
    }
    if (page_==Page::Error) return event==InputEvent::Action;
    if (page_==Page::Migration) {
        if (event==InputEvent::Action) { page_=Page::ConfirmMigration; cursor_=0; }
        return false;
    }
    if (page_==Page::List) {
        if (event==InputEvent::Next) cursor_=(cursor_+1)%7;
        else if (event==InputEvent::Action) {
            if (cursor_==6) return true;
            selected_=cursor_; cursor_=0;
            if (selected_<4 && state_.slots[selected_].occupied) page_=Page::Detail;
            else if (selected_==5) { page_=Page::Parents; parentA_=255; }
            else page_=Page::ConfirmFounder;
        }
        return false;
    }
    if (page_==Page::Detail) {
        if (event==InputEvent::Next) cursor_=(cursor_+1)%3;
        else if (event==InputEvent::Action) {
            if (cursor_==2) { page_=Page::List; cursor_=selected_; }
            else if (cursor_==1) { parentA_=selected_; page_=Page::Parents; cursor_=0; }
            else { page_=Page::ConfirmSwitch; cursor_=0; }
        }
        return false;
    }
    if (page_==Page::Parents) {
        if (event==InputEvent::Next) cursor_=(cursor_+1)%5;
        else if (event==InputEvent::Action) {
            if (cursor_==4) { page_=Page::List; cursor_=0; parentA_=255; }
            else if (state_.slots[cursor_].occupied) {
                if (parentA_==255) parentA_=cursor_;
                else if (eligible(pet,parentA_,cursor_)) { selected_=cursor_; page_=Page::ConfirmBreed; cursor_=0; }
                else if (!failed_) error("Padres no elegibles");
            }
        }
        return false;
    }
    if (event==InputEvent::Next) { cursor_=1-cursor_; return false; }
    if (event!=InputEvent::Action) return false;
    if (!cursor_) { page_=enabled_?Page::List:Page::Migration; cursor_=enabled_ && selected_<7?selected_:0; return false; }
    if (guard.blocked() || pet.pendingAction()!=Action::None || pet.cold() || pet.sleep.asleep || pet.exploration.away()) {
        error("Sesion activa o pausa"); return false;
    }
    const auto confirmation=page_;
    if (confirmation==Page::ConfirmMigration) migrate(pet,settings);
    else if (confirmation==Page::ConfirmFounder) founder(pet,settings);
    else if (confirmation==Page::ConfirmBreed) breed(pet,settings);
    else if (confirmation==Page::ConfirmSwitch) {
        std::unique_ptr<LearningState> nextPolicy;
        if (learning_ && !learning_->readPolicy(state_.slots[selected_],nextPolicy)) {
            error("Politica no disponible",true); return false;
        }
        if (!flush() || !store_.activate(state_,selected_,pet,settings,guard,true)) {
            if (!failed_) error("Cambio no disponible",store_.blocked());
        } else {
            if (learning_) learning_->adopt(std::move(nextPolicy),pet.profile.petId(),state_.slots[state_.active].learningRef);
            changedActive_=true; page_=Page::List; cursor_=selected_;
        }
    }
    return false;
}

void CollectionPanel::row(uint8_t, int y, const char* label, bool selected) {
    const uint16_t fill=selected?TFT_YELLOW:TFT_DARKGREY;
    canvas_->fillRect(6,y,228,18,fill);
    canvas_->setTextColor(selected?TFT_BLACK:TFT_WHITE,fill);
    canvas_->drawString(label,10,y+4,1);
}
void CollectionPanel::portrait(uint8_t index, int x, int y, int size) {
    if (!assets_ || index>=4 || !state_.slots[index].occupied) return;
    const auto species=static_cast<SpeciesId>(state_.slots[index].form);
    const auto& clip=content::builtinDefinition().clip(species,content::Action::Idle);
    assets_->drawFrameScaled(*canvas_,clip.path,0,x,y,size,size,false,-1,0,clip.canvas);
}
void CollectionPanel::draw(const char* language) {
    if (!canvas_) return;
    canvas_->fillSprite(TFT_BLACK); canvas_->setTextDatum(TL_DATUM);
    canvas_->setTextColor(TFT_WHITE,TFT_BLACK);
    const bool es=language && !std::strcmp(language,"ES");
    char line[38]; std::snprintf(line,sizeof(line),"%s  %u/4",es?"COLECCION":"COLLECTION",unsigned(state_.count()));
    canvas_->drawString(line,8,5,2);
    if (page_==Page::List || page_==Page::Parents) {
        for (uint8_t i=0;i<4;++i) {
            const auto& slot=state_.slots[i]; const auto profile=slot.profile();
            std::snprintf(line,sizeof(line),"%u %s %s %s",unsigned(i+1),slot.occupied?form(slot.form):"---",
                slot.occupied?(profile.sex()==Sex::Male?"M":"F"):"",slot.occupied && i==state_.active?"*":"");
            row(i,26+i*20,line,cursor_==i);
            portrait(i,212,27+i*20,16);
        }
        canvas_->setTextColor(TFT_WHITE,TFT_BLACK);
        if (page_==Page::Parents) {
            canvas_->drawString(parentA_==255?"PADRE A":"PADRE B",8,112,1);
            if (cursor_==4) row(4,110,"< VOLVER",true);
        } else {
            const char* commands[]={"+ FUNDADOR","CRUZAR","<"};
            for (uint8_t i=0;i<3;++i) {
                canvas_->setTextColor(cursor_==i+4?TFT_YELLOW:TFT_WHITE,TFT_BLACK);
                canvas_->drawString(commands[i],8+i*94,112,1);
            }
        }
    } else if (page_==Page::Detail) {
        portrait(selected_,8,29,64);
        const auto& slot=state_.slots[selected_]; const auto profile=slot.profile();
        canvas_->drawString(form(slot.form),80,30,1);
        canvas_->drawString(profile.petId().substr(0,16).c_str(),80,46,1);
        canvas_->drawString(profile.petId().substr(16).c_str(),80,58,1);
        std::snprintf(line,sizeof(line),"%s  %s",profile.sex()==Sex::Male?"M":"F",selected_==state_.active?"ACTIVO":"");
        canvas_->drawString(line,80,74,1);
        if (slot.cooldownMs) { std::snprintf(line,sizeof(line),"Espera %lum",static_cast<unsigned long>((slot.cooldownMs+59999)/60000)); canvas_->drawString(line,80,90,1); }
        if (slot.form==3 && slot.incubationRequiredMs) { std::snprintf(line,sizeof(line),"Incuba %lum",static_cast<unsigned long>((slot.incubationRequiredMs-slot.incubationMs+59999)/60000)); canvas_->drawString(line,80,94,1); }
        const char* actions[]={"ACTIVAR","PADRE","<"};
        for (uint8_t i=0;i<3;++i) {
            canvas_->setTextColor(cursor_==i?TFT_YELLOW:TFT_WHITE,TFT_BLACK);
            canvas_->drawString(actions[i],8+i*90,116,1);
        }
    } else if (page_==Page::Error) {
        canvas_->drawString(message_,8,48,1);
        canvas_->drawString(failed_?"Reiniciar para recuperar":"< VOLVER",8,82,1);
    } else if (page_==Page::Migration) {
        canvas_->drawString("Activo + reserva legacy",8,40,1);
        canvas_->drawString("Mochila: solo activo",8,60,1);
        row(0,97,"MIGRAR...",true);
    } else {
        const char* action=page_==Page::ConfirmMigration?"Migrar activo y reserva?":
            page_==Page::ConfirmFounder?"Crear huevo fundador?":
            page_==Page::ConfirmSwitch?"Cambiar mascota activa?":"Confirmar cruce?";
        canvas_->drawString(action,8,39,1);
        if (page_==Page::ConfirmFounder) canvas_->drawString("Sin objetos nuevos",8,62,1);
        if (page_==Page::ConfirmBreed) canvas_->drawString("Huevo 30m / espera 24h",8,62,1);
        row(0,86,"CANCELAR",cursor_==0); row(1,108,"CONFIRMAR",cursor_==1);
    }
    canvas_->pushSprite(0,0);
}
}  // namespace vpet
