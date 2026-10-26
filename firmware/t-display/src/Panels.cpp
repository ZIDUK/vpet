#include "vpet/Panels.h"
#include "vpet/Evolution.h"
#include "vpet/EvolutionUi.h"
#include "vpet/Layout.h"
#include "vpet/Nutrition.h"
#include "vpet/Strings.h"
#include "vpet/TrainingUi.h"
#include "vpet/MenuBar.h"
#include "vpet/ExplorationUi.h"
#include "vpet/UiCue.h"

#include <stdio.h>
#include <string.h>
#include <time.h>

namespace vpet {
namespace {
constexpr uint16_t kPanel = 0xD6B4;
constexpr uint16_t kChip = 0xC52D;
constexpr uint16_t kInk = 0x31C7;
constexpr SpeciesId kEvolutionStages[] = {
    SpeciesId::Egg, SpeciesId::Baby, SpeciesId::Rookie,
    SpeciesId::Champion, SpeciesId::Ultimate,
};

}

const char* Panels::portraitPath(SpeciesId species, bool thumbnail) const {
    return thumbnail ? definition_.stage(species).portrait : definition_.clip(species, content::Action::Idle).path;
}

const char* Panels::battleSpritePath(SpeciesId species, int action) const {
    const content::Action actions[] = {content::Action::Punch, content::Action::Cast, content::Action::Block,
                                      content::Action::Hit, content::Action::Hurt};
    return definition_.clip(species, action >= 0 && action < 5 ? actions[action] : content::Action::Idle,
                            content::Context::Battle).path;
}

const char* Panels::battleSpeciesLabel(SpeciesId species) const {
    return definition_.stage(species).battleName;
}

Panels::Panels(TFT_eSPI& display, TFT_eSprite& canvas, AssetStore& assets, TFT_eSprite* scene,
               const content::PetDefinition& definition)
    : output_(display), display_(canvas), assets_(assets), definition_(definition), scene_(scene) {}

void Panels::drawExploration(const ExplorationSession& session,const PetState& pet,
                            uint64_t wall,uint32_t nowMs,const char* language,bool home,uint8_t menu) {
    if (scene_) {
        if (sceneKind_ != Scene::Exploration || sceneSpecies_ != pet.species()) {
            scene_->fillSprite(exploration_ui::ink);
            for (uint8_t i=0;i<menu_bar::count;++i) {
                assets_.drawFrame(*scene_,menu_bar::icons[i],0,menu_bar::iconX(i),2);
                menu_bar::dimLockedIcon(*scene_,pet.species(),i);
            }
            sceneKind_ = Scene::Exploration;
            sceneSpecies_ = pet.species();
        }
        memcpy(display_.getPointer(),scene_->getPointer(),240*24*2);
    }
    struct Canvas {
        TFT_eSprite& pixels;
        AssetStore& assets;
        void fillRect(int x,int y,int w,int h,uint16_t color) { if(w>0 && h>0) pixels.fillRect(x,y,w,h,color); }
        void drawPixel(int x,int y,uint16_t color) { pixels.drawPixel(x,y,color); }
        uint16_t readPixel(int x,int y) { return pixels.readPixel(x,y); }
        void asset(const char* path,uint32_t frame,int x,int y) { assets.drawFrame(pixels,path,frame,x,y); }
    } canvas{display_,assets_};
    exploration_ui::View<Canvas>(canvas,pet,session,wall,nowMs,languageIsSpanish(language),definition_).draw(home,menu,scene_==nullptr);
    display_.pushSprite(0,0);
}

void Panels::drawStorageError(const char* language) {
    const bool spanish = languageIsSpanish(language);
    display_.fillSprite(TFT_BLACK);
    display_.setTextDatum(TL_DATUM);
    display_.setTextColor(TFT_YELLOW, TFT_BLACK);
    drawLabel(spanish ? "GUARDADO PENDIENTE" : "SAVE PENDING", 16, 42, 208, 2);
    display_.setTextColor(TFT_WHITE, TFT_BLACK);
    drawLabel(spanish ? "REINTENTANDO..." : "RETRYING...", 16, 70, 208, 2);
    display_.pushSprite(0, 0);
    invalidate();
}

void Panels::invalidate() {
    sceneKind_ = Scene::None;
    lastPanel_ = PanelId::Home;
    lastSpanish_ = true;
    lastStatusPage_ = 255;
    lastOptionsIndex_ = 255;
    lastInventoryIndex_ = 255;
    lastEvolutionIndex_ = 255;
    lastBluetoothStatus_ = BleStatus::Off;
    lastSoundEnabled_ = true;
    lastLanguage_[0] = '\0';
}

void Panels::drawLabel(const char* text, int16_t x, int16_t y, int16_t width, uint8_t font) {
    String fitted(text);
    while (fitted.length() > 1 && display_.textWidth(fitted, font) > width) {
        fitted.remove(fitted.length() - 1);
    }
    display_.drawString(fitted, x, y, font);
}

void Panels::drawCallBadge(uint8_t selected, bool calling) {
    if (!calling) return;
    const int16_t selectorX = menu_bar::left(selected);
    display_.setTextDatum(TR_DATUM);
    display_.setTextColor(TFT_YELLOW, TFT_BLACK);
    display_.drawString("*", selectorX + menu_bar::width(selected) - 2, 1, 2);
    display_.setTextDatum(TL_DATUM);
}

void Panels::drawChrome(uint8_t selected, const char* title, bool calling) {
    display_.fillScreen(TFT_BLACK);
    for (uint8_t index = 0; index < menu_bar::count; ++index) {
        assets_.drawFrame(display_, menu_bar::icons[index], 0, menu_bar::iconX(index), 2);
        menu_bar::dimLockedIcon(display_,menuSpecies_,index);
    }
    const int16_t selectorX = menu_bar::left(selected), width = menu_bar::width(selected);
    display_.drawRect(selectorX, 0, width, 24, TFT_YELLOW);
    display_.drawRect(selectorX + 1, 1, width - 2, 22, TFT_YELLOW);
    drawCallBadge(selected, calling);
    display_.fillRect(0, 24, 240, 111, kPanel);
    display_.fillRect(3, 27, 234, 20, kInk);
    const bool statusTitle = strncmp(title, "STATUS", 6) == 0 ||
                             strncmp(title, "ESTADO", 6) == 0;
    display_.setTextDatum(statusTitle ? TL_DATUM : MC_DATUM);
    display_.setTextColor(TFT_WHITE, kInk);
    drawLabel(title, statusTitle ? 14 : 120, statusTitle ? 30 : 37,
              statusTitle ? 120 : 220, 2);
    display_.setTextDatum(TL_DATUM);
    display_.setTextColor(kInk, kPanel);
}

void Panels::beginPanel(bool panelChanged, uint8_t selected, const char* title, bool calling) {
    if (panelChanged) {
        drawChrome(selected, title, calling);
        return;
    }
    display_.fillRect(0, 48, 240, 87, kPanel);
    display_.setTextDatum(TL_DATUM);
    display_.setTextColor(kInk, kPanel);
}

void Panels::drawStatusPet(const PetState& pet, uint32_t nowMs, bool spanish) {
    const int16_t x = statusPetX(88);
    const int16_t y = 47;
    if (pet.dead() || pet.injured()) {
        display_.setTextDatum(TC_DATUM);
        display_.setTextColor(pet.dead() ? kInk : 0xB800, kPanel);
        drawLabel(pet.dead() ? (spanish ? "MUERTO" : "DEAD") : (spanish ? "HERIDO" : "HURT"), 50, 49, 96, 1);
        display_.setTextDatum(TL_DATUM);
        display_.setTextColor(kInk, kPanel);
        assets_.drawFrameScaled(display_, pet.dead() ? "/ui/fx/grave.vpa" : portraitPath(pet.species(), false),
                                pet.dead() ? 0 : nowMs / 80, 12, 59, 76, 76, false, -1, 0, 88);
        return;
    }
    assets_.drawFrame(display_, portraitPath(pet.species(), false), nowMs / 80, x, y);
}

void Panels::drawStat(
    const char* icon,
    const char* label,
    const char* value,
    int16_t x,
    int16_t y,
    int16_t width,
    const char* extra
) {
    constexpr uint16_t kChip = 0xC52D;
    display_.fillRoundRect(x, y, width, kStatusCardH, 4, kChip);
    display_.drawRoundRect(x, y, width, kStatusCardH, 4, kInk);
    assets_.drawFrame(display_, icon, 0, x + 2, y + 2, false, -1, 72);
    display_.setTextColor(kInk, kChip);
    if (extra != nullptr && extra[0] != '\0') {
        drawLabel(label, x + 24, y + 2, 36, 2);
        drawLabel(extra, x + 24, y + 14, width - 50, 1);
        display_.setTextDatum(TR_DATUM);
        drawLabel(value, x + width - 3, y + 2, 40, 2);
    } else {
        drawLabel(label, x + 24, y + 5, 36, 2);
        display_.setTextDatum(TR_DATUM);
        drawLabel(value, x + width - 3, y + 5, 40, 2);
    }
    display_.setTextDatum(TL_DATUM);
    display_.setTextColor(kInk, kPanel);
}

void Panels::drawVital(const char* icon, const char* label, int value, int16_t y, uint16_t barColor, uint8_t minLuma) {
    constexpr uint16_t kChip = 0xC52D;
    const int16_t x = kStatusVitalX;
    const int16_t width = kStatusVitalW;
    const int clamped = value < 0 ? 0 : (value > 100 ? 100 : value);
    display_.fillRoundRect(x, y, width, kStatusVitalH, 4, kChip);
    display_.drawRoundRect(x, y, width, kStatusVitalH, 4, kInk);
    assets_.drawFrameScaled(display_, icon, 0, x + 2, y + 2, 16, 16, false, -1, minLuma);
    display_.setTextColor(kInk, kChip);
    drawLabel(label, x + 22, y + 2, 44, 1);
    char num[8];
    snprintf(num, sizeof(num), "%d", clamped);
    display_.setTextDatum(TR_DATUM);
    drawLabel(num, x + width - 3, y + 2, 28, 1);
    display_.setTextDatum(TL_DATUM);
    display_.drawRect(x + 22, y + 12, width - 29, 7, kInk);
    const int16_t filled = static_cast<int16_t>((clamped * (width - 31)) / 100);
    if (filled > 0) display_.fillRect(x + 23, y + 13, filled, 5, barColor);
    display_.setTextColor(kInk, kPanel);
}

void Panels::drawBar(const char* label, int value, int16_t y) {
    drawLabel(label, 6, y, 56, 2);
    display_.fillRect(62, y + 4, 174, 8, 0x8C51);
    const int clamped = value < 0 ? 0 : (value > 100 ? 100 : value);
    const int16_t filled = static_cast<int16_t>((clamped * 174) / 100);
    if (filled > 0) display_.fillRect(62, y + 4, filled, 8, kInk);
}

void Panels::drawHelix(int16_t x, int16_t y, const uint8_t dna[4], float spin, int16_t width, int16_t height) {
    const uint16_t colorA = helixColor(dna, 0);
    const uint16_t colorB = helixColor(dna, 1);
    const bool empty = dna == nullptr || (dna[0] | dna[1] | dna[2] | dna[3]) == 0;
    const uint8_t steps = 48;
    display_.fillRoundRect(x - 2, y - 2, width + 4, height + 4, 4, 0x2104);
    int16_t xs[2][49];
    int16_t ys[49];
    for (uint8_t step = 0; step <= steps; ++step) {
        xs[0][step] = static_cast<int16_t>(x + helixSample(0, step, steps, width, spin));
        xs[1][step] = static_cast<int16_t>(x + helixSample(1, step, steps, width, spin));
        ys[step] = y + static_cast<int16_t>((step * height) / steps);
    }
    for (uint8_t pass = 0; pass < 2; ++pass) {
        const bool back = pass == 0;
        for (uint8_t step = 0; step < steps; ++step) {
            for (uint8_t strand = 0; strand < 2; ++strand) {
                const float depth = helixDepth(strand, step, steps, spin);
                if (back == (depth < 0)) {
                    display_.drawLine(
                        xs[strand][step],
                        ys[step],
                        xs[strand][step + 1],
                        ys[step + 1],
                        strand == 0 ? colorA : colorB
                    );
                }
            }
        }
    }
    if (!empty) {
        for (uint8_t rung = 0; rung < kHelixRungs; ++rung) {
            const uint8_t step = static_cast<uint8_t>(((rung + 1) * steps) / (kHelixRungs + 1));
            const int16_t row = y + static_cast<int16_t>((step * height) / steps);
            const int16_t x0 = static_cast<int16_t>(x + helixSample(0, step, steps, width, spin));
            const int16_t x1 = static_cast<int16_t>(x + helixSample(1, step, steps, width, spin));
            display_.drawLine(x0, row, x1, row, (rung % 2) == 0 ? colorA : colorB);
            display_.fillCircle(x0, row, 1, colorA);
            display_.fillCircle(x1, row, 1, colorB);
        }
    }
}

void Panels::drawDnaPage(const PetState& pet, bool spanish, uint32_t nowMs) {
    const int16_t x = kStatusSplitX + 2;
    // Helix occupies the right strip (x..x+kHelixWidth). The agreed
    // visual contract for 4/4 is kHelixWidth=40; the height stays at
    // 68 so the code strip and the first stat row are not overlapped.
    drawHelix(x, 58, pet.dna(), helixSpin(nowMs), kHelixWidth, 68);
    char code[20];
    if (pet.hasDna()) {
        // Format: "DNA:XX-XX-XX-XX" (15 chars, no space after colon).
        // At font 1 (6 px/char default) the string is 90 px and fits
        // in the 94 px strip without truncation. All 8 hex digits and
        // their separating dashes are preserved verbatim.
        snprintf(
            code,
            sizeof(code),
            "DNA:%02X-%02X-%02X-%02X",
            pet.dna()[0],
            pet.dna()[1],
            pet.dna()[2],
            pet.dna()[3]
        );
    } else {
        snprintf(code, sizeof(code), "DNA:-- -- -- --");
    }
    display_.fillRect(142, 29, 94, 17, kInk);
    display_.setTextColor(TFT_WHITE, kInk);
    // Use the full strip width (94 px) as the budget. At font 1
    // (6 px/char default), the 15-char code is 90 px — well within
    // the budget so drawLabel does not truncate the last hex byte.
    constexpr int16_t kDnaCodeStripX = 142;
    constexpr int16_t kDnaCodeStripW = 94;
    drawLabel(code, kDnaCodeStripX, 33, kDnaCodeStripW, 1);
    display_.setTextColor(kInk, kPanel);
    if (!pet.hasDna()) return;
    const char* names[] = {
        "HP", copy::mp(spanish), "OFF",
        copy::def(spanish), copy::spd(spanish), "BRN",
    };
    // BRN gets a real brain icon (the legacy pedia.vpa was a placeholder).
    const char* icons[] = {
        "/ui/icons/heart.vpa", "/ui/icons/energy.vpa",
        "/ui/icons/training.vpa", "/ui/icons/battle.vpa",
        "/ui/icons/rest.vpa", "/ui/icons/brain.vpa",
    };
    const CombatStat stats[] = {
        CombatStat::Hp, CombatStat::Mp, CombatStat::Off,
        CombatStat::Def, CombatStat::Spd, CombatStat::Brn,
    };
    // Compact row stride (13 px) so all six stats fit under the helix
    // without overlapping the code strip (y=29..46) or the panel border.
    // Keep combat value/bar and accumulated EV in separate columns.
    drawLabel("EV", kStatusDnaRowX + kStatusDnaEvOffset, 47, 18, 1);
    for (uint8_t i = 0; i < 6; ++i) {
        const int16_t y = 55 + i * 13;
        char num[4];
        snprintf(num, sizeof(num), "%02u", pet.combatStat(stats[i]));
        constexpr int16_t rowX = kStatusDnaRowX;
        constexpr int16_t rowW = kStatusDnaRowW;
        constexpr int16_t barW = kStatusDnaBarW;
        display_.fillRoundRect(rowX, y, rowW, 13, 2, kChip);
        display_.drawRoundRect(rowX, y, rowW, 13, 2, kInk);
        // Scaled 10x10 icon (parity with sim_renderer.py). The scratch
        // sprite is filled with the destination pixel at (x, y) so the
        // transparent areas of the icon blend with the card chip color.
        assets_.drawFrameScaled(
            display_, icons[i], 0,
            rowX + 2, y + 1,
            10, 10,
            false, -1, 50
        );
        display_.setTextColor(kInk, kChip);
        drawLabel(names[i], rowX + 14, y + 1, 18, 1);
        drawLabel(num, rowX + 34, y + 1, 18, 1);
        snprintf(num, sizeof(num), "%u", pet.evAt(stats[i]));
        display_.setTextDatum(TR_DATUM);
        drawLabel(num, rowX + kStatusDnaEvOffset + 18, y + 1, 18, 1);
        display_.setTextDatum(TL_DATUM);
        // Bar border: 7 px tall so the 5 px fill leaves 1 px padding
        // top and bottom.
        display_.drawRect(rowX + kStatusDnaBarOffset, y + 2, barW, 7, kInk);
        const int16_t filled = static_cast<int16_t>((pet.combatStat(stats[i]) * (barW - 2)) / pet.statLimit(stats[i]));
        if (filled > 0) display_.fillRect(rowX + kStatusDnaBarOffset + 1, y + 3, filled, 5, 0x94BF);
    }
    display_.setTextColor(kInk, kPanel);
}

void Panels::drawStatus(const PetState& pet, bool spanish, uint8_t page, uint32_t nowMs) {
    if ((page % Navigation::kStatusPages) == 3) {
        drawDnaPage(pet, spanish, nowMs);
        return;
    }
    if ((page % Navigation::kStatusPages) == 0) {
        drawVital("/ui/icons/heart.vpa", copy::hp(spanish), pet.health(), kStatusVitalY, 0xF800);
        drawVital("/ui/icons/feed.vpa", copy::hunger(spanish), pet.hunger(), kStatusVitalY + kStatusVitalRow, 0xFD20);
        drawVital("/ui/icons/energy.vpa", copy::energy(spanish), pet.energy(), kStatusVitalY + kStatusVitalRow * 2, 0x07FF);
        drawVital(cue::facePath(cue::forPet(pet).face), spanish ? "ANIMO" : "MOOD", pet.happiness(), kStatusVitalY + kStatusVitalRow * 3, 0x56D1, 0);
        return;
    }
    const int16_t x = kStatusListX;
    const bool carePage = (page % Navigation::kStatusPages) == 1;
    auto drawStatusRow = [&](const char* icon, const char* label, const char* value, uint8_t row) {
        const int16_t y = kStatusListY + row * (carePage ? kStatusCareRow : kStatusListRow);
        const int16_t height = carePage ? kStatusCareH : kStatusListH;
        const int16_t textY = y + (carePage ? 2 : 4);
        const int16_t iconSize = carePage ? 10 : 12;
        display_.fillRoundRect(x, y, kStatusListW, height, 3, kChip);
        display_.drawRoundRect(x, y, kStatusListW, height, 3, kInk);
        assets_.drawFrameScaled(display_, icon, 0, x + 2, y + 1, iconSize, iconSize, false, -1, 65);
        display_.setTextColor(kInk, kChip);
        drawLabel(label, x + 15, textY, carePage ? 78 : 82, 1);
        display_.setTextDatum(TR_DATUM);
        drawLabel(value, x + kStatusListW - 3, textY, carePage ? 30 : 27, 1);
        display_.setTextDatum(TL_DATUM);
    };
    char value[16];
    if ((page % Navigation::kStatusPages) == 2) {
        snprintf(value, sizeof(value), "%u", pet.weight());
        const uint8_t reference = referenceWeight(pet.species());
        char weightLabel[24];
        if (reference > 0) {
            const uint8_t low = static_cast<uint8_t>((80U * reference + 99U) / 100U);
            const uint8_t high = static_cast<uint8_t>((120U * reference) / 100U);
            snprintf(weightLabel, sizeof(weightLabel), spanish ? "PESO %u-%u" : "WEIGHT %u-%u", low, high);
        } else {
            snprintf(weightLabel, sizeof(weightLabel), "%s", spanish ? "PESO" : "WEIGHT");
        }
        drawStatusRow("/ui/icons/weight.vpa", weightLabel, value, 0);
        snprintf(value, sizeof(value), "%u/3", pet.dp());
        drawStatusRow("/ui/icons/battle.vpa", "DP", value, 1);
        if (pet.hasWinRatio()) {
            snprintf(value, sizeof(value), "%u%%", pet.winRatioPercent());
        } else {
            snprintf(value, sizeof(value), "--");
        }
        drawStatusRow("/ui/icons/trophy.vpa", spanish ? "VICTORIAS" : "WIN RATE", value, 2);
        snprintf(value, sizeof(value), "%u/7", pet.protein());
        drawStatusRow("/ui/icons/protein.vpa", spanish ? "PROTEINA" : "PROTEIN", value, 3);
        snprintf(value, sizeof(value), "%u-%u", pet.wins(), pet.losses());
        drawStatusRow("/ui/icons/versus.vpa", "W-L", value, 4);
        return;
    }
    const uint32_t ageSeconds = pet.stageAgeSeconds();
    if (ageSeconds >= 86400) {
        snprintf(value, sizeof(value), "%lud %02luh",
                 static_cast<unsigned long>(ageSeconds / 86400),
                 static_cast<unsigned long>((ageSeconds / 3600) % 24));
    } else if (ageSeconds >= 3600) {
        snprintf(value, sizeof(value), "%luh", static_cast<unsigned long>(ageSeconds / 3600));
    } else {
        snprintf(value, sizeof(value), "%lum", static_cast<unsigned long>(ageSeconds / 60));
    }
    drawStatusRow("/ui/icons/clock.vpa", spanish ? "EDAD" : "AGE", value, 0);
    snprintf(value, sizeof(value), "%u", pet.overfeeds());
    drawStatusRow("/ui/icons/feed.vpa", spanish ? "EXCESO" : "OVERFEED", value, 1);
    snprintf(value, sizeof(value), "%d", pet.careMistakes());
    drawStatusRow("/ui/icons/heart.vpa", spanish ? "CUIDADO" : "CARE", value, 2);
    snprintf(value, sizeof(value), "%u/4", pet.effortHearts());
    drawStatusRow("/ui/icons/training.vpa", spanish ? "ESFUERZO" : "EFFORT", value, 3);
    snprintf(value, sizeof(value), "%d", pet.battles());
    drawStatusRow("/ui/icons/battle.vpa", spanish ? "BATALLAS" : "BATTLES", value, 4);
    snprintf(value, sizeof(value), "%u/15", pet.injuries());
    drawStatusRow("/ui/icons/medkit.vpa", spanish ? "LESIONES" : "INJURIES", value, 5);
}

void Panels::drawInventory(uint8_t selected, bool spanish, const PetState& pet) {
    const uint8_t current = pet.clampVisibleInventoryIndex(selected);
    const uint8_t visible = pet.visibleInventoryCount();
    uint8_t pos = 0;
    for (; pos < visible; ++pos) {
        if (pet.inventoryIndexAt(pos) == current) break;
    }
    const uint8_t start = inventoryWindowStart(visible, pos);
    assets_.drawFrame(display_, copy::itemIcon(current), 0, 40, 70, false, -1, 72);
    display_.setTextColor(kInk, kPanel);
    display_.setTextDatum(MC_DATUM);
    if (current>=8) {
        String name(copy::itemName(current,spanish));
        int split=name.length();
        while (split>1 && display_.textWidth(name.substring(0,split),1)>88) --split;
        if (split<static_cast<int>(name.length())) {
            const int space=name.substring(0,split+1).lastIndexOf(' ');
            if (space>0) split=space;
        }
        String second=name.substring(split);
        second.trim();
        drawLabel(name.substring(0,split).c_str(),50,102,88,1);
        drawLabel(second.c_str(),50,112,88,1);
        drawLabel(copy::itemBlurb(current,spanish),50,124,88,1);
    } else {
        drawLabel(copy::itemName(current, spanish), 50, 104, 88, 2);
        drawLabel(copy::itemBlurb(current, spanish), 50, 118, 88, 1);
    }
    display_.setTextDatum(TL_DATUM);
    const int16_t x = kStatusSplitX + 4;
    const int16_t width = 232 - kStatusSplitX;
    const uint8_t shown = visible < kInventoryWindow ? visible : kInventoryWindow;
    for (uint8_t slot = 0; slot < shown; ++slot) {
        const uint8_t index = pet.inventoryIndexAt(start + slot);
        const int16_t y = kStatusCardY + slot * kStatusCardRow;
        const bool active = index == current;
        const uint16_t fill = active ? TFT_YELLOW : kChip;
        display_.fillRoundRect(x, y, width, kStatusCardH, 4, fill);
        display_.drawRoundRect(x, y, width, kStatusCardH, 4, active ? TFT_YELLOW : kInk);
        assets_.drawFrame(display_, copy::itemIcon(index), 0, x + 2, y + 2, false, -1, 72);
        display_.setTextColor(kInk, fill);
        if (index >= 8) {
            char stock[8];
            snprintf(stock,sizeof(stock),"x%u",pet.itemCount(index));
            drawLabel(copy::itemName(index,spanish),x+24,y+5,width-52,1);
            drawLabel(stock,x+width-25,y+5,23,1);
        } else if (index < 6) {
            char line[80];
            snprintf(line, sizeof(line), "%s x%u", copy::itemName(index, spanish), pet.itemCount(index));
            drawLabel(line, x + 24, y + 5, width - 28, 2);
        } else {
            drawLabel(copy::itemName(index, spanish), x + 24, y + 5, width - 28, 2);
        }
    }
}

void Panels::drawFeeding(uint8_t selected, bool spanish, const PetState& pet) {
    const char* meat = copy::itemName(0, spanish);
    const char* protein = copy::itemName(4, spanish);
    const char* back = spanish ? "VOLVER" : "BACK";
    const char* foodIcons[] = {"/ui/icons/itemmeat.vpa", "/ui/icons/itemprotein.vpa"};
    const char* names[] = {meat, protein};
    const char* effects[] = {copy::itemBlurb(0, spanish), copy::itemBlurb(4, spanish)};
    for (uint8_t index = 0; index < 2; ++index) {
        const int16_t x = 7 + index * 115;
        const bool active = selected == index;
        const uint16_t fill = active ? TFT_YELLOW : kChip;
        display_.fillRoundRect(x, 56, 109, 54, 4, fill);
        display_.drawRoundRect(x, 56, 109, 54, 4, active ? TFT_YELLOW : kInk);
        assets_.drawFrame(display_, foodIcons[index], 0, x + 5, 66, false, -1, 72);
        display_.setTextColor(kInk, fill);
        drawLabel(names[index], x + 31, 65, 73, 2);
        drawLabel(effects[index], x + 31, 87, 73, 1);
        const bool proteinResting = index == 1 &&
                                    (pet.proteinFedThisCycle() || pet.energy() > 100 - items::kProteinEnergy);
        display_.setTextColor(proteinResting ? TFT_DARKGREY : TFT_GREEN, fill);
        drawLabel(proteinResting
                      ? (spanish ? "EN DESCANSO" : "RESTING")
                      : (spanish ? "ILIMITADO" : "UNLIMITED"),
                  x + 31, 101, 73, 1);
    }
    const bool backSelected = selected == 2;
    display_.fillRoundRect(7, 116, 224, 15, 3, backSelected ? TFT_YELLOW : kChip);
    display_.drawRoundRect(7, 116, 224, 15, 3, backSelected ? TFT_YELLOW : kInk);
    display_.setTextColor(kInk, backSelected ? TFT_YELLOW : kChip);
    display_.setTextDatum(MC_DATUM);
    drawLabel(back, 119, 119, 214, 1);
    display_.setTextDatum(TL_DATUM);
}

void Panels::drawEvolutionNode(const Navigation& navigation, uint8_t index, bool spanish) {
    const uint8_t selected = navigation.panelIndex() % Navigation::kEvolutionNodeCount;
    const uint8_t node = index % Navigation::kEvolutionNodeCount;
    const uint8_t stage = Navigation::evolutionNodeStage(node);
    const SpeciesId species = kEvolutionStages[stage];
    const uint8_t start = inventoryWindowStart(Navigation::kEvolutionNodeCount, selected);
    const int16_t slot = node - start;
    const int16_t x = kEvoX0 + slot * (kEvoChip + kEvoGap);
    const int16_t y = kEvoColorY;
    const bool hidden = stage > navigation.currentStage();
    const bool active = node == selected;
    const uint16_t fill = active ? TFT_YELLOW : kChip;
    display_.fillRoundRect(x, y, kEvoChip, kEvoChip, 4, fill);
    display_.drawRoundRect(x, y, kEvoChip, kEvoChip, 4, active ? TFT_YELLOW : kInk);
    assets_.drawFrame(display_, portraitPath(species, true), 0, x, y, false, hidden ? TFT_BLACK : -1);
    display_.setTextDatum(MC_DATUM);
    display_.setTextColor(hidden ? TFT_DARKGREY : kInk, kPanel);
    display_.drawString(hidden ? "???" : (stage == 0 && spanish ? "HUEVO" : definition_.stage(species).shortName), x + kEvoChip / 2, y + kEvoChip + 7, 1);
    display_.setTextDatum(TL_DATUM);
}

void Panels::drawEvolutionTree(const Navigation& navigation, bool spanish) {
    const int16_t stride = kEvoChip + kEvoGap;
    const int16_t centerY = kEvoColorY + kEvoChip / 2;
    const uint8_t selected = navigation.panelIndex() % Navigation::kEvolutionNodeCount;
    const uint8_t start = inventoryWindowStart(Navigation::kEvolutionNodeCount, selected);
    for (uint8_t slot = 0; slot + 1 < kInventoryWindow; ++slot) {
        const uint8_t stage = static_cast<uint8_t>(start + slot);
        const int16_t x1 = kEvoX0 + slot * stride + kEvoChip;
        const int16_t x2 = x1 + kEvoGap;
        const uint16_t color = stage < navigation.currentStage() ? TFT_YELLOW : kInk;
        display_.drawLine(x1, centerY, x2 - 3, centerY, color);
        display_.drawLine(x2 - 6, centerY - 3, x2 - 3, centerY, color);
        display_.drawLine(x2 - 6, centerY + 3, x2 - 3, centerY, color);
    }
    for (uint8_t slot = 0; slot < kInventoryWindow; ++slot) {
        drawEvolutionNode(navigation, static_cast<uint8_t>(start + slot), spanish);
    }
    drawEvolutionProgress(navigation, spanish);
}

void Panels::drawEvolutionProgress(const Navigation& navigation, bool spanish) {
    const uint8_t selected = navigation.panelIndex() % Navigation::kEvolutionNodeCount;
    const bool hidden = selected > navigation.currentStage();
    display_.setTextDatum(MC_DATUM);
    display_.setTextColor(hidden ? TFT_DARKGREY : kInk, kPanel);
    char stageLabel[28];
    snprintf(stageLabel, sizeof(stageLabel), "%s  %u/5",
             hidden ? (spanish ? "POR DESCUBRIR" : "UNDISCOVERED") :
                 selected == navigation.currentStage() ? copy::evoNow(spanish) : copy::evoReached(spanish),
             selected + 1);
    display_.drawString(stageLabel, 120, 110, 1);
    display_.drawRoundRect(10, 122, 220, 7, 3, kInk);
    display_.fillRoundRect(11, 123, 218 * (navigation.currentStage() + 1) / Navigation::kEvolutionNodeCount, 5, 2, TFT_GREEN);
    display_.setTextDatum(TL_DATUM);
}

void Panels::drawEvolution(const Navigation& navigation, bool spanish, const PetState& pet, bool detail) {
    if (!detail) {
        drawEvolutionTree(navigation, spanish);
        return;
    }
    const auto progress = evolution_progress::forPet(pet, navigation.panelIndex());
    struct Canvas {
        TFT_eSprite& display;
        AssetStore& assets;
        const content::PetDefinition& definition;
        void fillRect(int x, int y, int w, int h, uint16_t color) { display.fillRect(x,y,w,h,color); }
        void portrait(uint8_t stage, bool hidden) {
            const char* path = definition.stage(kEvolutionStages[stage]).portrait;
            if (hidden) assets.drawFrame(display,path,0,18,64,false,evolution_ui::muted);
            else assets.drawFrameScaled(display,path,0,4,50,64,64,false,-1,0,36);
        }
    } canvas{display_, assets_, definition_};
    evolution_ui::View<Canvas>(canvas, progress, spanish, definition_).draw(navigation.evolutionDetailPage());
}

void Panels::drawOptionsChip(
    uint8_t index,
    uint8_t selected,
    BleStatus bluetoothStatus,
    bool spanish,
    const char* language,
    bool soundEnabled,
    bool cold
) {
    const char* bluetooth = "OFF";
    switch (bluetoothStatus) {
        case BleStatus::Advertising: bluetooth = "ADV"; break;
        case BleStatus::Connected: bluetooth = "ON"; break;
        case BleStatus::Error: bluetooth = "ERR"; break;
        case BleStatus::Off: break;
    }
    const char* shortLabels[] = {"BT", "LANG", "SOUND", "SAVE", "LOAD", "DATE", "TIME", "EVO", "BACK", copy::pausePet(spanish), spanish ? "COLECCION" : "COLLECTION"};
    const char* extras[] = {
        bluetooth,
        language,
        soundEnabled ? copy::on(spanish) : copy::off(spanish),
        "",
        "",
        "",
        "",
        "",
        "",
        cold ? copy::on(spanish) : copy::off(spanish),
        "",
    };
    const char* icons[] = {
        "/ui/icons/bluetooth.vpa",
        "/ui/icons/language.vpa",
        "/ui/icons/sound.vpa",
        "/ui/icons/save.vpa",
        "/ui/icons/load.vpa",
        "/ui/icons/date.vpa",
        "/ui/icons/clock.vpa",
        "/ui/icons/evolve.vpa",
        "/ui/icons/back.vpa",
        "/ui/icons/rest.vpa",
        "/ui/icons/pedia.vpa",
    };
    static_assert(sizeof(shortLabels) / sizeof(shortLabels[0]) == Navigation::kOptionCount, "Option labels");
    static_assert(sizeof(extras) / sizeof(extras[0]) == Navigation::kOptionCount, "Option extras");
    static_assert(sizeof(icons) / sizeof(icons[0]) == Navigation::kOptionCount, "Option icons");
    const uint8_t chip = index % Navigation::kOptionCount;
    const uint8_t current = selected % Navigation::kOptionCount;
    const uint8_t start = inventoryWindowStart(Navigation::kOptionCount, option_menu::slot(current));
    const uint8_t position = option_menu::slot(chip);
    if (position < start || position >= start + kInventoryWindow) return;
    const uint8_t slot = static_cast<uint8_t>(position - start);
    const int16_t x = 8;
    const int16_t y = kStatusCardY + slot * kStatusCardRow;
    const int16_t width = 224;
    const bool active = chip == current;
    const uint16_t fill = active ? TFT_YELLOW : kChip;
    display_.fillRoundRect(x, y, width, kStatusCardH, 4, fill);
    display_.drawRoundRect(x, y, width, kStatusCardH, 4, active ? TFT_YELLOW : kInk);
    assets_.drawFrame(display_, icons[chip], 0, x + 2, y + 2, false, -1, 72);
    display_.setTextColor(kInk, fill);
    if (extras[chip][0] != '\0') {
        char line[32];
        snprintf(line, sizeof(line), "%s  %s", shortLabels[chip], extras[chip]);
        drawLabel(line, x + 28, y + 5, 188, 2);
    } else {
        drawLabel(shortLabels[chip], x + 28, y + 5, 188, 2);
    }
}

void Panels::drawOptions(
    uint8_t selected,
    BleStatus bluetoothStatus,
    bool spanish,
    const char* language,
    bool soundEnabled,
    bool cold,
    uint8_t onlyIndex
) {
    if (onlyIndex != 255) {
        drawOptionsChip(onlyIndex, selected, bluetoothStatus, spanish, language, soundEnabled, cold);
        return;
    }
    const uint8_t current = selected % Navigation::kOptionCount;
    const uint8_t start = inventoryWindowStart(Navigation::kOptionCount, option_menu::slot(current));
    for (uint8_t slot = 0; slot < kInventoryWindow; ++slot) {
        drawOptionsChip(
            option_menu::at(start + slot),
            selected,
            bluetoothStatus,
            spanish,
            language,
            soundEnabled,
            cold
        );
    }
}

void Panels::drawRest(
    uint8_t selected,
    bool spanish,
    bool asleep
) {
    const char* rows[] = {
        copy::restLight(spanish,asleep),
        copy::restBack(spanish),
    };
    const uint8_t current = selected % Navigation::kRestCount;
    for (uint8_t index = 0; index < Navigation::kRestCount; ++index) {
        const int16_t y = 52 + index * 20;
        const bool active = index == current;
        if (active) display_.fillRect(5, y - 2, 230, 19, TFT_YELLOW);
        display_.setTextColor(kInk, active ? TFT_YELLOW : kPanel);
        drawLabel(rows[index], 10, y, 218, 2);
    }
}

void Panels::drawDateTime(const DateTimeMenu& dateMenu) {
    char label[20];
    const uint8_t current = dateMenu.cursor();
    const uint8_t windowStart = dateMenu.windowStart();
    for (uint8_t slot = 0; slot < 4; ++slot) {
        const uint8_t index = windowStart + slot;
        if (index >= dateMenu.count()) break;
        const int16_t y = 52 + slot * 20;
        const bool active = index == current;
        if (active) display_.fillRect(5, y - 2, 230, 19, TFT_YELLOW);
        display_.setTextColor(kInk, active ? TFT_YELLOW : kPanel);
        dateMenu.writeLabel(index, label, sizeof(label));
        drawLabel(label, 10, y, 218, 2);
    }
}

void Panels::draw(
    const Navigation& navigation,
    const PetState& pet,
    BleStatus bluetoothStatus,
    const DateTimeMenu& dateMenu,
    const char* language,
    bool soundEnabled,
    bool hasBackup,
    SpeciesId backupSpecies,
    uint32_t nowMs
) {
    output_.startWrite();
    const PanelId panel = navigation.panel();
    const bool spanish = languageIsSpanish(language);
    const bool calling = pet.callReason() != CallReason::None;
    const bool panelChanged = panel != lastPanel_ || spanish != lastSpanish_ || menuSpecies_ != pet.species();
    menuSpecies_ = pet.species();
    lastPanel_ = panel;
    lastSpanish_ = spanish;
    switch (panel) {
        case PanelId::Status: {
            const uint8_t page = navigation.panelIndex();
            const bool statusPageChanged = panelChanged || lastStatusPage_ != page;
            if (!statusPageChanged && nowMs - lastStatusDataMs_ < 1000) {
                display_.fillRect(0, 48, kStatusSplitX, 87, kPanel);
                drawStatusPet(pet, nowMs, spanish);
                constexpr uint32_t kHelixFrameIntervalMs = 100;
                if (page % Navigation::kStatusPages == 3 && nowMs - lastDnaHelixMs_ >= kHelixFrameIntervalMs) {
                    drawHelix(
                        kStatusSplitX + 2, 58, pet.dna(), helixSpin(nowMs),
                        kHelixWidth, 68
                    );
                    lastDnaHelixMs_ = nowMs;
                }
                break;
            }
            char title[20];
            snprintf(
                title,
                sizeof(title),
                "%s %u/%u",
                copy::statusTitle(spanish),
                (page % Navigation::kStatusPages) + 1,
                Navigation::kStatusPages
            );
            beginPanel(statusPageChanged, navigation.menuIndex(), title, calling);
            lastStatusPage_ = page;
            lastStatusDataMs_ = nowMs;
            drawStatusPet(pet, nowMs, spanish);
            drawStatus(pet, spanish, page, nowMs);
            if ((page % Navigation::kStatusPages) == 3) lastDnaHelixMs_ = nowMs;
            break;
        }
        case PanelId::Inventory: {
            const uint8_t selected = pet.clampVisibleInventoryIndex(navigation.panelIndex());
            // Transparent previews and changing labels require a clean background.
            beginPanel(panelChanged, navigation.menuIndex(), copy::inventoryTitle(spanish), calling);
            drawInventory(selected, spanish, pet);
            lastInventoryIndex_ = selected;
            break;
        }
        case PanelId::Feeding:
            beginPanel(panelChanged, navigation.menuIndex(), spanish ? "ALIMENTAR" : "FEED", calling);
            drawFeeding(navigation.panelIndex() % Navigation::kFeedingCount, spanish, pet);
            break;
        case PanelId::EvolutionTree: {
            const uint8_t selected = navigation.panelIndex() % Navigation::kEvolutionNodeCount;
            const uint8_t previousStart = inventoryWindowStart(Navigation::kEvolutionNodeCount, lastEvolutionIndex_);
            const uint8_t currentStart = inventoryWindowStart(Navigation::kEvolutionNodeCount, selected);
            if (cursorRedrawOnly(lastEvolutionIndex_, selected, false, panelChanged) && previousStart == currentStart) {
                drawEvolutionNode(navigation, lastEvolutionIndex_, spanish);
                drawEvolutionNode(navigation, selected, spanish);
                drawEvolutionProgress(navigation, spanish);
            } else {
                beginPanel(panelChanged, navigation.menuIndex(), copy::evolutionTitle(spanish), calling);
                drawEvolution(navigation, spanish, pet, false);
            }
            lastEvolutionIndex_ = selected;
            break;
        }
        case PanelId::EvolutionDetail: {
            if (panelChanged) drawChrome(navigation.menuIndex(), "", calling);
            else drawCallBadge(navigation.menuIndex(), calling);
            drawEvolution(navigation, spanish, pet, true);
            break;
        }
        case PanelId::Options: {
            const uint8_t selected = navigation.panelIndex();
            const uint8_t start = inventoryWindowStart(Navigation::kOptionCount, option_menu::slot(selected));
            const uint8_t lastStart = inventoryWindowStart(Navigation::kOptionCount, option_menu::slot(lastOptionsIndex_));
            const bool extrasChanged =
                bluetoothStatus != lastBluetoothStatus_ ||
                soundEnabled != lastSoundEnabled_ ||
                pet.cold() != lastCold_ ||
                language == nullptr ||
                strcmp(language, lastLanguage_) != 0 ||
                (lastOptionsIndex_ != 255 && start != lastStart);
            if (cursorRedrawOnly(lastOptionsIndex_, selected, extrasChanged, panelChanged)) {
                drawOptionsChip(
                    lastOptionsIndex_, selected, bluetoothStatus, spanish, language, soundEnabled, pet.cold()
                );
                drawOptionsChip(selected, selected, bluetoothStatus, spanish, language, soundEnabled, pet.cold());
            } else {
                beginPanel(panelChanged, navigation.menuIndex(), copy::optionsTitle(spanish), calling);
                drawOptions(selected, bluetoothStatus, spanish, language, soundEnabled, pet.cold());
            }
            lastOptionsIndex_ = selected;
            lastBluetoothStatus_ = bluetoothStatus;
            lastSoundEnabled_ = soundEnabled;
            lastCold_ = pet.cold();
            if (language != nullptr) {
                strncpy(lastLanguage_, language, sizeof(lastLanguage_) - 1);
                lastLanguage_[sizeof(lastLanguage_) - 1] = '\0';
            }
            break;
        }
        case PanelId::Rest:
            beginPanel(panelChanged, navigation.menuIndex(), copy::restTitle(spanish), calling);
            drawRest(navigation.panelIndex(), spanish, pet.sleep.asleep);
            break;
        case PanelId::DateTime:
            beginPanel(
                panelChanged,
                navigation.menuIndex(),
                dateMenu.editingDate() ? copy::dateTitle(spanish) : copy::timeTitle(spanish),
                calling
            );
            drawDateTime(dateMenu);
            break;
        case PanelId::Home:
            break;
    }
    display_.pushSprite(0, 0);
    output_.endWrite();
}

void Panels::drawPractice(const PracticeSession& s, const PetState& pet, uint32_t nowMs, const char* language) {
    if (s.page == PracticeSession::Page::Bag) {
        const bool es=languageIsSpanish(language);
        display_.fillSprite(TFT_BLACK);
        display_.setTextDatum(TL_DATUM);
        display_.setTextColor(TFT_WHITE,TFT_BLACK);
        display_.drawString(es ? "MOCHILA" : "BAG",6,3,2);
        char pools[48];
        snprintf(pools,sizeof(pools),"HP %d/%d  MP %d/%d",s.battle.player.hp,
            s.battle.player.maxHp,s.battle.player.mp,s.battle.player.maxMp);
        display_.drawString(pools,6,22,1);
        const int start=inventoryWindowStart(s.bagCount(pet),s.cursor);
        const int rows=s.bagCount(pet)<3 ? s.bagCount(pet) : 3;
        for (int row=0;row<rows;++row) {
            const int slot=start+row, item=s.bagItemAt(pet,slot), y=36+row*29;
            const uint16_t fill=slot==s.cursor ? TFT_YELLOW : TFT_DARKGREY;
            display_.fillRect(4,y,232,27,fill);
            assets_.drawFrame(display_,item<0 ? "/ui/icons/back.vpa" : copy::itemIcon(8+item),
                0,6,y+2,false,-1,72);
            display_.setTextColor(slot==s.cursor ? TFT_BLACK : TFT_WHITE,fill);
            char line[80];
            if (item<0) snprintf(line,sizeof(line),"%s",copy::back(es));
            else snprintf(line,sizeof(line),"%s",copy::itemName(8+item,es));
            drawLabel(line,32,y+2,164,1);
            if (item>=0) {
                char stock[8];
                snprintf(stock,sizeof(stock),"x%u",pet.adoptedStock.count(item));
                drawLabel(stock,205,y+2,27,1);
            }
            if (item>=0) drawLabel(copy::itemBlurb(8+item,es),32,y+15,198,1);
        }
        display_.pushSprite(0,0);
        return;
    }
    if (s.page == PracticeSession::Page::Tech || s.page == PracticeSession::Page::Detail) {
        struct Canvas {
            TFT_eSprite& pixels;
            AssetStore& assets;
            void fillRect(int x,int y,int w,int h,uint16_t color) { if(w>0 && h>0) pixels.fillRect(x,y,w,h,color); }
            void drawPixel(int x,int y,uint16_t color) { pixels.drawPixel(x,y,color); }
            void asset(const char* path,uint32_t frame,int x,int y) { assets.drawFrame(pixels,path,frame,x,y); }
        } canvas{display_,assets_};
        const TrainingSession unused;
        training_ui::View<Canvas>(canvas,unused,pet,nowMs,languageIsSpanish(language),definition_).techniques(s);
        display_.pushSprite(0,0);
        return;
    }
    const uint16_t ink = TFT_BLACK, accent = TFT_YELLOW;
    display_.fillSprite(ink);
    display_.setTextDatum(TL_DATUM);
    display_.setTextColor(TFT_WHITE, ink);
    if (s.page == PracticeSession::Page::Arena) {
        if (scene_) {
            if (sceneKind_ != Scene::Arena) {
                scene_->fillSprite(ink);
                assets_.drawFrame(*scene_,definition_.background,0,0,0);
                sceneKind_ = Scene::Arena;
                arenaFooterKey_ = 0xFFFF;
            }
            memcpy(display_.getPointer(),scene_->getPointer(),240*135*2);
        } else assets_.drawFrame(display_, definition_.background, 0, 0, 0);
        const uint32_t roundElapsed = nowMs - s.updatedAt;
        const bool active = s.battle.round > 0 && roundElapsed < practice::kImpactMs;
        int lunge = 0;
        if (active && roundElapsed >= 150 && roundElapsed < 400) lunge = (roundElapsed - 150) * 18 / 250;
        else if (active && roundElapsed >= 400 && roundElapsed < 650) lunge = 18;
        else if (active && roundElapsed >= 650 && roundElapsed < 950) lunge = 18 - (roundElapsed - 650) * 18 / 300;
        for (int i = 0; i < 2; ++i) {
            const auto& fighter = i == 0 ? s.battle.player : s.battle.rival;
            int action = active ? practice::presentationAction(s.battle, i) : -1;
            if (action == 3 && s.battle.actions[i] >= 0 && techniques::kCatalog[s.battle.actions[i]].mp) action = 1;
            const SpeciesId species = i == 0 ? pet.species() : SpeciesId::Rookie;
            const char* path = battleSpritePath(species, action);
            const uint32_t elapsed = active ? roundElapsed : nowMs;
            const int homeX = i == 0 ? 4 : 140;
            if (!s.battle.result)
                assets_.drawFrame(display_, path, elapsed / 80,
                                  homeX + (i == 0 ? lunge : -lunge), 38, i == 1);
            display_.fillRect(i * 120, 0, 120, 34, ink);
            display_.setTextColor(TFT_WHITE, ink);
            display_.drawString(i == 0 ? battleSpeciesLabel(species) : (languageIsSpanish(language) ? "PRACTICA" : "PRACTICE"), i * 120 + 4, 1, 1);
            for (int stat = 0; stat < 2; ++stat) {
                const int value = stat == 0 ? fighter.hp : fighter.mp;
                const int maximum = stat == 0 ? fighter.maxHp : fighter.maxMp;
                const int y = 13 + stat * 11, x = i * 120 + 4;
                display_.drawString(stat == 0 ? "HP" : "MP", x, y, 1);
                display_.fillRect(x + 16, y, 56, 7, TFT_DARKGREY);
                display_.fillRect(x + 16, y, 56 * value / maximum, 7, stat == 0 ? TFT_RED : TFT_CYAN);
                display_.drawNumber(value, x + 76, y, 1);
            }
        }
        if (s.battle.result) {
            const uint16_t resultColor = s.battle.result == 1 ? TFT_GREEN :
                s.battle.result == 2 ? TFT_RED : TFT_YELLOW;
            display_.fillRect(0, 33, 240, 82, ink);
            display_.fillRect(10, 36, 220, 75, TFT_DARKGREY);
            display_.drawRect(10, 36, 220, 75, resultColor);
            const char* reaction = definition_.clip(pet.species(), s.battle.result == 3 ? content::Action::Idle :
                s.battle.result == 1 ? content::Action::Happy : content::Action::Sad).path;
            assets_.drawFrameScaled(display_, reaction, (nowMs - s.updatedAt) / 100,
                                    164, 44, 64, 64, false, -1, 0, 88);
            display_.setTextColor(resultColor, TFT_DARKGREY);
            const bool es = languageIsSpanish(language);
            display_.drawString(s.battle.result == 1 ? (es ? "VICTORIA" : "VICTORY") :
                                s.battle.result == 2 ? (es ? "DERROTA" : "DEFEAT") : (es ? "EMPATE" : "DRAW"), 16, 40, 2);
            display_.setTextColor(TFT_WHITE, TFT_DARKGREY);
            display_.drawString(s.battle.result == 1 ? (es ? "RIVAL DERROTADO" : "RIVAL DEFEATED") :
                                s.battle.result == 2 ? (es ? "TE DERROTARON" : "YOU WERE DEFEATED") :
                                (es ? "LIMITE 30 RONDAS" : "30 ROUND LIMIT"), 16, 56, 1);
            char rounds[20];
            snprintf(rounds, sizeof(rounds), es ? "RONDAS %d" : "ROUNDS %d", s.battle.round);
            display_.setTextColor(TFT_LIGHTGREY, TFT_DARKGREY);
            display_.drawString(rounds, 16, 70, 1);
            if (*s.message) {
                display_.setTextColor(TFT_YELLOW, TFT_DARKGREY);
                drawLabel(s.message,16,94,150,1);
            } else if (s.rewardItem>=0) {
                String reward("+1 ");
                reward+=copy::itemName(8+s.rewardItem,es);
                int split=reward.length();
                while (split>1 && display_.textWidth(reward.substring(0,split),1)>150) --split;
                if (split<static_cast<int>(reward.length())) {
                    const int space=reward.substring(0,split+1).lastIndexOf(' ');
                    if (space>0) split=space;
                }
                String second=reward.substring(split);
                second.trim();
                display_.setTextColor(TFT_GREEN,TFT_DARKGREY);
                drawLabel(reward.substring(0,split).c_str(),16,84,150,1);
                drawLabel(second.c_str(),16,95,150,1);
            }
        }
        const bool es = languageIsSpanish(language);
        const uint16_t footerKey = s.cursor | (pet.practice.equipped << 4) | (s.battle.result ? 0x400 : 0);
        const bool compact=s.count(pet)>6;
        if (!scene_ || arenaFooterKey_ != footerKey) {
            TFT_eSprite& footer = scene_ ? *scene_ : display_;
            footer.fillRect(0,116,240,19,ink);
            for (int i=0;i<s.count(pet);++i) {
                const int x=2+i*(compact ? 18 : 20), size=compact ? 16 : 18;
                if (i==s.cursor) footer.fillRect(x,116,size,19,TFT_DARKGREY);
                const char* icon = s.actionIcon(pet,i);
                assets_.drawFrameScaled(footer,icon,0,x,116,size,size,false,-1,0,
                                        strncmp(icon,"/training/",10)==0 ? 16 : 20);
                if (i==s.cursor) footer.drawRect(x,116,size,19,accent);
            }
            arenaFooterKey_ = footerKey;
        }
        if (scene_) memcpy(static_cast<uint16_t*>(display_.getPointer())+240*116,
                           static_cast<uint16_t*>(scene_->getPointer())+240*116,240*19*2);
        display_.setTextColor(accent, ink);
        if (!s.battle.result && s.cursor > 0 && s.cursor < s.count(pet) - 2 &&
            s.equippedAt(pet, s.cursor - 1) == 2) {
            drawLabel(es ? "GUARDIA -50% +4MP" : "GUARD -50% +4MP", compact ? 132 : 128, 121, compact ? 104 : 108, 1);
        } else {
            const char* label = s.label(pet, s.cursor);
            if (!es) {
                if (strcmp(label, "RETIRARSE") == 0) label = "RETREAT";
                else if (strcmp(label,"MOCHILA")==0) label="BAG";
                else if (strcmp(label,"REINTENTAR")==0) label="RETRY";
                else if (strcmp(label, "VOLVER") == 0) label = "BACK";
                else if (strcmp(label, "GUARDIA") == 0) label = "GUARD";
                else if (strcmp(label, "GOLPE") == 0) label = "PUNCH";
                else if (strcmp(label, "LLAMA") == 0) label = "FLAME";
                else if (strcmp(label, "RAFAGA") == 0) label = "FLARE";
                else if (strcmp(label, "AUTO") == 0) label = "AUTO";
            }
            drawLabel(label, compact ? 132 : 128, 121, compact ? 104 : 108, 1);
        }
    } else {
        char title[36];
        snprintf(title, sizeof(title), "%s / %s", battleSpeciesLabel(pet.species()),
                 s.page == PracticeSession::Page::Menu ? "BATALLA" : "TECNICAS");
        display_.drawString(title, 6, 4, 2);
        int y = 44;
        if (s.page == PracticeSession::Page::Detail) {
            char line[40];
            display_.drawString(PracticeSession::name(s.technique), 6, 24, 1);
            snprintf(line, sizeof(line), "POT %d MP %d DOM %u/100", s.technique == 0 ? 12 : s.technique == 1 ? 24 : 0,
                     s.technique == 1 ? 8 : 0, pet.practice.mastery[s.technique]);
            display_.drawString(line, 6, 37, 1);
            snprintf(line, sizeof(line), "ENERGIA %d COSTE 4 TRAIN %u", pet.energy(), pet.practice.training);
            display_.drawString(line, 6, 50, 1);
            display_.drawString(s.message, 6, 63, 1);
            y = 80;
        } else {
            char line[32];
            snprintf(line, sizeof(line), "VINCULO %u", pet.practice.bond);
            display_.drawString(line, 6, 26, 1);
        }
        for (int i = 0; i < s.count(pet); ++i) {
            const bool selected = i == s.cursor;
            if (s.page == PracticeSession::Page::Menu) {
                static const char* icons[] = {"/ui/icons/pedia.vpa", "/ui/icons/battle.vpa", "/ui/icons/back.vpa"};
                display_.fillRect(4, y, 232, 26, selected ? accent : TFT_DARKGREY);
                assets_.drawFrame(display_, icons[i], 0, 8, y + 3);
                display_.setTextColor(selected ? ink : TFT_WHITE, selected ? accent : TFT_DARKGREY);
                display_.drawString(s.label(pet, i), 36, y + 9, 1);
                y += 28;
                continue;
            }
            display_.fillRect(4, y, 232, 14, selected ? accent : TFT_DARKGREY);
            display_.setTextColor(selected ? ink : TFT_WHITE, selected ? accent : TFT_DARKGREY);
            display_.drawString(s.label(pet, i), 8, y + 3, 1);
            if (s.page == PracticeSession::Page::Tech && pet.practice.isEquipped(i)) display_.drawString("*", 222, y + 3, 1);
            y += 17;
        }
    }
    display_.pushSprite(0, 0);
}

void Panels::drawTraining(
    const TrainingSession& s, const PetState& pet,
    uint32_t nowMs, const char* language
) {
    struct Canvas {
        TFT_eSprite& pixels;
        AssetStore& assets;
        void fillRect(int x, int y, int w, int h, uint16_t color) {
            if (w > 0 && h > 0) pixels.fillRect(x,y,w,h,color);
        }
        void drawPixel(int x, int y, uint16_t color) { pixels.drawPixel(x,y,color); }
        void asset(const char* path, uint32_t frame, int x, int y) {
            assets.drawFrame(pixels,path,static_cast<uint16_t>(frame),x,y);
        }
    } canvas{display_, assets_};
    const bool cachedFooter = scene_ && s.state == TrainingSession::State::Select;
    if (cachedFooter && (sceneKind_ != Scene::TrainingFooter || trainingFooterCursor_ != s.cursor)) {
        Canvas footer{*scene_, assets_};
        training_ui::View<Canvas>(footer,s,pet,nowMs,languageIsSpanish(language),definition_).selectFooter();
        trainingFooterCursor_ = s.cursor;
        sceneKind_ = Scene::TrainingFooter;
    }
    training_ui::View<Canvas>(canvas,s,pet,nowMs,languageIsSpanish(language),definition_).draw(!cachedFooter);
    if (cachedFooter) {
        // Reuse Home's scene buffer, as Arena does, without another allocation.
        memcpy(static_cast<uint16_t*>(display_.getPointer())+240*115,
               static_cast<uint16_t*>(scene_->getPointer())+240*115,240*20*2);
    }
    display_.pushSprite(0, 0);
}

}  // namespace vpet
