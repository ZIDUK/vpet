#pragma once
#include "vpet/Input.h"
#include "vpet/PetState.h"
#include "vpet/PracticeBattle.h"

namespace vpet {
class PracticeSession {
public:
    enum class Page { Menu, Tech, Detail, Arena };
    Page page = Page::Menu;
    uint8_t cursor = 0, technique = 0;
    practice::Battle battle;
    uint32_t updatedAt = 0;
    const char* message = "";
    const char* reason = "ELIGE ORDEN";
    bool dirty = false;
    static const char* name(int i) {
        return i == 0 ? "GOLPE" : i == 1 ? "LLAMA" : "GUARDIA";
    }
    int equippedAt(const PetState& pet, int slot) const {
        for (int i = 0; i < 3; ++i) if (pet.practice.isEquipped(i) && slot-- == 0) return i;
        return -1;
    }
    int count(const PetState& pet) const {
        if (page == Page::Menu || page == Page::Detail) return 3;
        if (page == Page::Tech) return 4;
        if (battle.result) return 1;
        int n = 2;
        for (int i = 0; i < 3; ++i) if (pet.practice.isEquipped(i)) ++n;
        return n;
    }
    const char* label(const PetState& pet, int i) const {
        if (page == Page::Menu) return i == 0 ? "TECNICAS" : i == 1 ? "BATALLA DE PRACTICA" : "VOLVER";
        if (page == Page::Detail) return i == 0 ? "ENTRENAR" : i == 1 ? "EQUIPAR" : "VOLVER";
        if (page == Page::Tech) return i == 3 ? "VOLVER" : pet.practice.learned(i) ? name(i) : "???";
        if (battle.result) return "VOLVER";
        return i == 0 ? "A TU CRITERIO" : i == count(pet)-1 ? "RETIRARSE" : name(equippedAt(pet, i-1));
    }
    bool input(PetState& pet, InputEvent event, uint32_t now) {
        if (event == InputEvent::Next) { cursor = (cursor + 1) % count(pet); return true; }
        if (event == InputEvent::Back) {
            if (page == Page::Arena) return true;
            if (page == Page::Menu) return false;
            page = Page::Menu; cursor = 0; return true;
        }
        if (event != InputEvent::Action) return true;
        if (page == Page::Menu) {
            if (cursor == 2) return false;
            if (cursor == 0) page = Page::Tech;
            else {
                battle = practice::Battle();
                int stats[6];
                for (int i = 0; i < 6; ++i) stats[i] = pet.combatStat(static_cast<CombatStat>(i));
                battle.player.init(stats);
                battle.player.equipped = pet.practice.equipped;
                battle.player.personality = pet.dna()[3] % 3;
                battle.player.bond = pet.practice.bond;
                for (int i = 0; i < 3; ++i) battle.player.mastery[i] = pet.practice.mastery[i];
                page = Page::Arena; reason = "ELIGE ORDEN";
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
        const int order = cursor == 0 ? -1 : equippedAt(pet, cursor-1);
        const int chosen = practice::choose(battle.player, order);
        reason = order < 0 ? "A SU CRITERIO" : chosen == order ? "SIGUE ORDEN" :
            order == 1 && battle.player.mp < 8 ? "SIN MP" :
            battle.player.cooldown[order] ? "EN RECARGA" : chosen == 2 ? "PREFIERE DEFENDER" : "PREFIERE ATACAR";
        if (battle.step(order)) {
            updatedAt = now; cursor = 0;
            if (battle.result) {
                for (int i = 0; i < 3; ++i) {
                    int value = pet.practice.mastery[i] + battle.uses[i];
                    pet.practice.mastery[i] = value > 100 ? 100 : value;
                }
                if (pet.practice.bond < 100) ++pet.practice.bond;
                dirty = true;
            }
        }
        return true;
    }
};
}
