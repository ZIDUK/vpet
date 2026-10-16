#pragma once
#include "vpet/Input.h"
#include "vpet/PetState.h"
#include "vpet/PracticeBattle.h"
#include "vpet/ConsumableEffects.h"

namespace vpet {
class PracticeSession {
public:
    enum class Page { Menu, Tech, Detail, Arena, Bag };
    Page page = Page::Menu;
    uint8_t cursor = 0, technique = 0;
    practice::Battle battle;
    uint32_t updatedAt = 0;
    uint32_t nextRoundAt = 0;
    int lastOrder = -1;
    const char* message = "";
    const char* reason = "ELIGE ORDEN";
    bool dirty = false;
    bool awarded = false;
    bool pendingAward = false;
    int rewardItem = -1;
    void finishSave(PetState& pet, const PetState& before, const PracticeSession& previous, bool committed) {
        if (!committed) {
            pet=before;
            if (battle.result && !previous.battle.result) {
                // Keep the terminal presentation; retry acquisition only on Action.
                awarded=false;
                pendingAward=true;
                rewardItem=-1;
                page=Page::Arena;
                cursor=0;
            } else *this=previous;
            message="ERROR AL GUARDAR";
        }
        dirty=false;
    }
    int requestedOrder(const PetState& pet) const {
        return page == Page::Bag || cursor == 0 || cursor >= count(pet)-2
            ? -1 : equippedAt(pet,cursor-1);
    }
    int bagCount(const PetState& pet) const {
        int n=1;
        for (int i=0;i<adopted::kCount;++i) if (bagItemVisible(pet,i)) ++n;
        return n;
    }
    bool bagItemVisible(const PetState& pet, int i) const {
        if (i<0 || i>=adopted::kCount || !pet.adoptedStock.count(i)) return false;
        const char* category=adopted::kItems[i].category;
        return !strcmp(category,"combat_recovery") || !strcmp(category,"battle_boost");
    }
    int bagItemAt(const PetState& pet, int slot) const {
        for (int i=0;i<adopted::kCount;++i)
            if (bagItemVisible(pet,i) && slot--==0) return i;
        return -1;
    }
    bool useItem(PetState& pet, int index) {
        if (!bagItemVisible(pet,index) || pet.cold() || pet.dead()) return false;
        uint8_t stock=pet.adoptedStock.count(index);
        if (!consumables::use(battle,stock,index)) return false;
        pet.adoptedStock.set(index,stock);
        dirty=true;
        return true;
    }
    void award(PetState& pet) {
        if (awarded || !battle.result) return;
        awarded=true;
        for (int i = 0; i < 3; ++i) {
            int value = pet.practice.mastery[i] + battle.uses[i];
            pet.practice.mastery[i] = value > 100 ? 100 : value;
        }
        if (pet.practice.bond < 100) ++pet.practice.bond;
        rewardItem=battle.result==1 ? pet.adoptedStock.reward() : -1;
        dirty = true;
    }
    void round(PetState& pet, int order, uint32_t now) {
        if (battle.result || order < -1 || order > 2) return;
        const int chosen = practice::choose(battle.player, order);
        reason = order < 0 ? "A SU CRITERIO" : chosen == order ? "SIGUE ORDEN" :
            order == 1 && battle.player.mp < 8 ? "SIN MP" :
            battle.player.cooldown[order] ? "EN RECARGA" : chosen == 2 ? "PREFIERE DEFENDER" : "PREFIERE ATACAR";
        if (battle.step(order)) {
            lastOrder = order;
            updatedAt = now;
            nextRoundAt = now + 1450;
            if (page != Page::Bag) cursor = 0;
            if (battle.result) { award(pet); page=Page::Arena; cursor=0; }
        }
    }
    void tick(PetState& pet, uint32_t now) {
        if (page != Page::Arena && page != Page::Bag) return;
        if (battle.result) { page=Page::Arena; cursor=0; return; }
        if (static_cast<int32_t>(now - nextRoundAt) < 0) return;
        round(pet, requestedOrder(pet), now);
    }
    static const char* name(int i) {
        return i == 0 ? "GOLPE" : i == 1 ? "LLAMA" : "GUARDIA";
    }
    int equippedAt(const PetState& pet, int slot) const {
        for (int i = 0; i < 3; ++i) if (pet.practice.isEquipped(i) && slot-- == 0) return i;
        return -1;
    }
    int count(const PetState& pet) const {
        if (page == Page::Bag) return bagCount(pet);
        if (page == Page::Menu || page == Page::Detail) return 3;
        if (page == Page::Tech) return 4;
        if (battle.result) return 1;
        int n = 3;
        for (int i = 0; i < 3; ++i) if (pet.practice.isEquipped(i)) ++n;
        return n;
    }
    const char* actionIcon(const PetState& pet, int i) const {
        if (battle.result || i==count(pet)-1) return "/ui/icons/back.vpa";
        if (i==0) return "/ui/icons/brain.vpa";
        if (i==count(pet)-2) return "/ui/icons/backpack.vpa";
        const char* techniques[]={"/training/tech_punch.vpa","/training/tech_flame.vpa","/training/tech_guard.vpa"};
        const int technique=equippedAt(pet,i-1);
        return technique>=0 && technique<3 ? techniques[technique] : "/ui/icons/back.vpa";
    }
    const char* label(const PetState& pet, int i) const {
        if (page == Page::Menu) return i == 0 ? "TECNICAS" : i == 1 ? "BATALLA DE PRACTICA" : "VOLVER";
        if (page == Page::Detail) return i == 0 ? "ENTRENAR" : i == 1 ? "EQUIPAR" : "VOLVER";
        if (page == Page::Tech) return i == 3 ? "VOLVER" : pet.practice.learned(i) ? name(i) : "???";
        if (battle.result) return pendingAward ? "REINTENTAR" : "VOLVER";
        return i == 0 ? "AUTO" : i == count(pet)-1 ? "RETIRARSE" :
            i == count(pet)-2 ? "MOCHILA" : name(equippedAt(pet, i-1));
    }
    bool input(PetState& pet, InputEvent event, uint32_t now) {
        if (event == InputEvent::Next) { cursor = (cursor + 1) % count(pet); return true; }
        if (event == InputEvent::Back) {
            if (page == Page::Bag) { page=Page::Arena; cursor=0; return true; }
            if (page == Page::Arena) return true;
            if (page == Page::Menu) return false;
            page = Page::Menu; cursor = 0; return true;
        }
        if (event != InputEvent::Action) return true;
        if (page==Page::Arena && battle.result && pendingAward) {
            pendingAward=false;
            award(pet);
            message="LISTO";
            return true;
        }
        if (page == Page::Bag) {
            const int item=bagItemAt(pet,cursor);
            if (item>=0) {
                message=useItem(pet,item) ? "LISTO" : "NO DISPONIBLE";
                if (cursor>=bagCount(pet)) cursor=bagCount(pet)-1;
                return true;
            }
            page=Page::Arena; cursor=0; return true;
        }
        if (page == Page::Menu) {
            if (cursor == 2) return false;
            if (cursor == 0) page = Page::Tech;
            else {
                battle = practice::Battle();
                lastOrder = -1;
                battle.rival.element = practice::Element::Fire;
                awarded = false;
                pendingAward = false;
                rewardItem = -1;
                int stats[6];
                for (int i = 0; i < 6; ++i) stats[i] = pet.effectiveCombatStat(static_cast<CombatStat>(i));
                battle.player.init(stats);
                battle.player.element = pet.species() == SpeciesId::Egg || pet.species() == SpeciesId::Baby
                    ? practice::Element::Neutral : practice::Element::Fire;
                battle.player.equipped = pet.practice.equipped;
                battle.player.personality = pet.dna()[3] % 3;
                battle.player.bond = pet.practice.bond;
                for (int i = 0; i < 3; ++i) battle.player.mastery[i] = pet.practice.mastery[i];
                page = Page::Arena; reason = "COMBATE AUTOMATICO"; nextRoundAt = now + 500;
            }
            cursor = 0; message = ""; return true;
        }
        if (page == Page::Tech) {
            technique = cursor;
            page = cursor == 3 ? Page::Menu : Page::Detail;
            cursor = 0; message = ""; return true;
        }
        if (page == Page::Detail) {
            if (cursor == 2) { page = Page::Tech; cursor = technique; return true; }
            const bool ok = cursor == 0 ? pet.trainTechnique(technique) : pet.practice.toggle(technique);
            dirty |= ok; message = ok ? "LISTO" : "NO DISPONIBLE"; return true;
        }
        if (battle.result || cursor == count(pet)-1) { page = Page::Menu; cursor = 1; return true; }
        if (cursor == count(pet)-2) { page=Page::Bag; cursor=0; return true; }
        const int order = cursor == 0 ? -1 : equippedAt(pet, cursor-1);
        round(pet, order, now);
        return true;
    }
};
}
