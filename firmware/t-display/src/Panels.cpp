#include "vpet/Panels.h"
#include "vpet/Evolution.h"
#include "vpet/Layout.h"
#include "vpet/Strings.h"

#include <stdio.h>
#include <string.h>
#include <time.h>

namespace vpet {
namespace {
constexpr const char* kMenuIcons[] = {
    "/ui/icons/status.vpa", "/ui/icons/feed.vpa", "/ui/icons/training.vpa",
    "/ui/icons/battle.vpa", "/ui/icons/rest.vpa", "/ui/icons/items.vpa",
    "/ui/icons/pedia.vpa", "/ui/icons/options.vpa",
};
constexpr uint16_t kPanel = 0xD6B4;
constexpr uint16_t kChip = 0xC52D;
constexpr uint16_t kInk = 0x31C7;
constexpr SpeciesId kEvolutionStages[] = {
    SpeciesId::Egg, SpeciesId::Baby, SpeciesId::Rookie,
    SpeciesId::Champion, SpeciesId::Ultimate,
};

const char* portraitPath(SpeciesId species, bool thumbnail) {
    switch (species) {
        case SpeciesId::Egg: return thumbnail ? "/ui/evolution/egg.vpa" : "/animations/egg/egg_idle.vpa";
        case SpeciesId::Baby: return thumbnail ? "/ui/evolution/sparkmon.vpa" : "/animations/baby/sparkmon_idle.vpa";
        case SpeciesId::Rookie: return thumbnail ? "/ui/evolution/firemon.vpa" : "/animations/rookie/firemon_idle.vpa";
        case SpeciesId::Champion: return thumbnail ? "/ui/evolution/flamemon.vpa" : "/animations/champion/flamemon_idle.vpa";
        case SpeciesId::Ultimate: return thumbnail ? "/ui/evolution/dragfiremon.vpa" : "/animations/ultimate/dragfiremon_idle.vpa";
    }
    return "/ui/evolution/egg.vpa";
}
}

Panels::Panels(TFT_eSPI& display, TFT_eSprite& canvas, AssetStore& assets)
    : output_(display), display_(canvas), assets_(assets) {}

void Panels::invalidate() {
    lastPanel_ = PanelId::Home;
    lastSpanish_ = true;
    lastStatusPage_ = 255;
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
    const int16_t selectorX = (selected % 8) * 30;
    display_.setTextDatum(TR_DATUM);
    display_.setTextColor(TFT_YELLOW, TFT_BLACK);
    display_.drawString("*", selectorX + 28, 1, 2);
    display_.setTextDatum(TL_DATUM);
}

void Panels::drawChrome(uint8_t selected, const char* title, bool calling) {
    display_.fillScreen(TFT_BLACK);
    for (uint8_t index = 0; index < 8; ++index) {
        assets_.drawFrame(display_, kMenuIcons[index], 0, index * 30 + 5, 2);
    }
    const int16_t selectorX = (selected % 8) * 30;
    display_.drawRect(selectorX, 0, 30, 24, TFT_YELLOW);
    display_.drawRect(selectorX + 1, 1, 28, 22, TFT_YELLOW);
    drawCallBadge(selected, calling);
    display_.fillRect(0, 24, 240, 111, kPanel);
    display_.fillRect(3, 27, 234, 20, kInk);
    display_.setTextDatum(MC_DATUM);
    display_.setTextColor(TFT_WHITE, kInk);
    drawLabel(title, 120, 37, 220, 2);
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

void Panels::drawStatusPet(const PetState& pet, uint32_t nowMs) {
    const int16_t x = statusPetX(88);
    const int16_t y = 47;
    if (pet.dead()) {
        assets_.drawFrame(display_, "/ui/fx/grave.vpa", 0, x + 6, 50);
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

void Panels::drawVital(const char* icon, const char* label, int value, int16_t y) {
    constexpr uint16_t kChip = 0xC52D;
    const int16_t x = kStatusSplitX + 4;
    const int16_t width = 232 - kStatusSplitX;
    const int clamped = value < 0 ? 0 : (value > 100 ? 100 : value);
    display_.fillRoundRect(x, y, width, kStatusCardH, 4, kChip);
    display_.drawRoundRect(x, y, width, kStatusCardH, 4, kInk);
    assets_.drawFrame(display_, icon, 0, x + 2, y + 2, false, -1, 72);
    display_.setTextColor(kInk, kChip);
    drawLabel(label, x + 24, y + 1, 36, 2);
    char num[8];
    snprintf(num, sizeof(num), "%d", clamped);
    display_.setTextDatum(TR_DATUM);
    drawLabel(num, x + width - 3, y + 1, 28, 2);
    display_.setTextDatum(TL_DATUM);
    display_.drawRect(x + 24, y + 14, width - 30, 7, kInk);
    const int16_t filled = static_cast<int16_t>((clamped * (width - 32)) / 100);
    if (filled > 0) display_.fillRect(x + 25, y + 15, filled, 5, kInk);
    display_.setTextColor(kInk, kPanel);
}

void Panels::drawBar(const char* label, int value, int16_t y) {
    drawLabel(label, 6, y, 56, 2);
    display_.fillRect(62, y + 4, 174, 8, 0x8C51);
    const int clamped = value < 0 ? 0 : (value > 100 ? 100 : value);
    const int16_t filled = static_cast<int16_t>((clamped * 174) / 100);
    if (filled > 0) display_.fillRect(62, y + 4, filled, 8, kInk);
}

void Panels::drawHelix(int16_t x, int16_t y, const uint8_t dna[4], float spin) {
    const uint16_t colorA = helixColor(dna, 0);
    const uint16_t colorB = helixColor(dna, 1);
    const bool empty = dna == nullptr || (dna[0] | dna[1] | dna[2] | dna[3]) == 0;
    const int width = kHelixWidth;
    const int height = kHelixHeight;
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
    const int16_t x = kStatusSplitX + 4;
    const int16_t width = 232 - kStatusSplitX;
    drawHelix(x + 2, kHelixY, pet.dna(), helixSpin(nowMs));
    char code[20];
    if (pet.hasDna()) {
        snprintf(
            code,
            sizeof(code),
            "DNA: %02X-%02X-%02X-%02X",
            pet.dna()[0],
            pet.dna()[1],
            pet.dna()[2],
            pet.dna()[3]
        );
    } else {
        snprintf(code, sizeof(code), "DNA: -- -- -- --");
    }
    display_.setTextColor(kInk, kPanel);
    drawLabel(code, x + 44, kStatusCardY, 90, 1);
    if (!pet.hasDna()) return;
    const char* names[] = {
        copy::hp(spanish), copy::mp(spanish), copy::offense(spanish),
        copy::def(spanish), copy::spd(spanish), copy::brn(spanish),
    };
    const CombatStat stats[] = {
        CombatStat::Hp, CombatStat::Mp, CombatStat::Off,
        CombatStat::Def, CombatStat::Spd, CombatStat::Brn,
    };
    for (uint8_t i = 0; i < 6; ++i) {
        const int16_t y = 62 + i * 11;
        char num[4];
        snprintf(num, sizeof(num), "%02u", pet.combatStat(stats[i]));
        drawLabel(names[i], x + 56, y, 26, 1);
        drawLabel(num, x + 82, y, 16, 1);
        const int16_t barW = width - 102;
        display_.drawRect(x + 100, y + 2, barW, 7, kInk);
        const int16_t filled = static_cast<int16_t>((pet.combatStat(stats[i]) * (barW - 2)) / 99);
        if (filled > 0) display_.fillRect(x + 101, y + 3, filled, 5, helixColor(pet.dna(), 0));
    }
}

void Panels::drawStatus(const PetState& pet, bool spanish, uint8_t page, uint32_t nowMs) {
    if ((page % Navigation::kStatusPages) == 3) {
        drawDnaPage(pet, spanish, nowMs);
        return;
    }
    if ((page % Navigation::kStatusPages) == 0) {
        drawVital("/ui/icons/heart.vpa", copy::hp(spanish), pet.health(), kStatusCardY);
        drawVital("/ui/icons/feed.vpa", copy::hunger(spanish), pet.hunger(), kStatusCardY + kStatusCardRow);
        drawVital("/ui/icons/energy.vpa", copy::energy(spanish), pet.energy(), kStatusCardY + kStatusCardRow * 2);
        return;
    }
    const int16_t left = kStatusSplitX + 4;
    const int16_t right = kStatusSplitX + 70;
    const int16_t wide = 232 - kStatusSplitX;
    char value[16];
    if ((page % Navigation::kStatusPages) == 2) {
        snprintf(value, sizeof(value), "%u", pet.weight());
        drawStat("/ui/icons/weight.vpa", copy::weight(spanish), value, left, kStatusCardY);
        snprintf(value, sizeof(value), "%u/3", pet.dp());
        drawStat("/ui/icons/battle.vpa", copy::dp(spanish), value, right, kStatusCardY);
        if (pet.hasWinRatio()) {
            snprintf(value, sizeof(value), "%u%%", pet.winRatioPercent());
        } else {
            snprintf(value, sizeof(value), "--");
        }
        drawStat("/ui/icons/trophy.vpa", copy::winRatio(spanish), value, left, kStatusCardY + kStatusCardRow);
        snprintf(value, sizeof(value), "%u/7", pet.protein());
        drawStat("/ui/icons/protein.vpa", copy::proteinOverdose(spanish), value, right, kStatusCardY + kStatusCardRow);
        snprintf(value, sizeof(value), "%u-%u", pet.wins(), pet.losses());
        drawStat("/ui/icons/versus.vpa", "W-L", value, left, kStatusCardY + kStatusCardRow * 2, wide);
        return;
    }
    snprintf(value, sizeof(value), "%lus", static_cast<unsigned long>(pet.stageAgeSeconds()));
    const char* extra = nullptr;
    char clockExtra[16] = {};
    if (pet.callReason() == CallReason::Hunger) extra = copy::callHunger(spanish);
    else if (pet.callReason() == CallReason::Strength) extra = copy::callStrength(spanish);
    else if (pet.callReason() == CallReason::Lights) extra = copy::callLights(spanish);
    else if (pet.cold()) extra = copy::frozen(spanish);
    else if (pet.dead()) extra = copy::dead(spanish);
    else if (pet.injured()) extra = copy::injured(spanish);
    else {
        int clock[5] = {2026, 1, 1, 0, 0};
        const time_t now = time(nullptr);
        struct tm parts {};
        localtime_r(&now, &parts);
        if (parts.tm_year + 1900 >= 2024) {
            clock[1] = parts.tm_mon + 1;
            clock[2] = parts.tm_mday;
            clock[3] = parts.tm_hour;
            clock[4] = parts.tm_min;
        }
        snprintf(clockExtra, sizeof(clockExtra), "%02d/%02d %02d:%02d", clock[1], clock[2], clock[3], clock[4]);
        extra = clockExtra;
    }
    drawStat("/ui/icons/clock.vpa", copy::age(spanish), value, left, kStatusCardY, wide, extra);
    snprintf(value, sizeof(value), "%u", pet.overfeeds());
    drawStat("/ui/icons/feed.vpa", copy::overfeeds(spanish), value, left, kStatusCardY + kStatusCardRow);
    snprintf(value, sizeof(value), "%d", pet.careMistakes());
    drawStat("/ui/icons/heart.vpa", copy::careMistakes(spanish), value, right, kStatusCardY + kStatusCardRow);
    snprintf(value, sizeof(value), "%u/4", pet.effortHearts());
    drawStat("/ui/icons/training.vpa", copy::effort(spanish), value, left, kStatusCardY + kStatusCardRow * 2);
    snprintf(value, sizeof(value), "%d", pet.battles());
    drawStat("/ui/icons/battle.vpa", copy::battles(spanish), value, right, kStatusCardY + kStatusCardRow * 2);
}

void Panels::drawInventory(uint8_t selected, bool spanish, const PetState& pet) {
    const char* icons[] = {
        "/ui/icons/feed.vpa",
        "/ui/icons/energy.vpa",
        "/ui/icons/training.vpa",
        "/ui/icons/items.vpa",
        "/ui/icons/protein.vpa",
        "/ui/icons/medkit.vpa",
        "/ui/icons/options.vpa",
    };
    const uint8_t current = pet.clampVisibleInventoryIndex(selected);
    const uint8_t visible = pet.visibleInventoryCount();
    uint8_t pos = 0;
    for (; pos < visible; ++pos) {
        if (pet.inventoryIndexAt(pos) == current) break;
    }
    const uint8_t start = inventoryWindowStart(visible, pos);
    assets_.drawFrame(display_, icons[current], 0, 40, 70, false, -1, 72);
    display_.setTextColor(kInk, kPanel);
    display_.setTextDatum(MC_DATUM);
    drawLabel(copy::itemName(current, spanish), 50, 104, 88, 2);
    drawLabel(copy::itemBlurb(current, spanish), 50, 118, 88, 1);
    display_.setTextDatum(TL_DATUM);
    const int16_t x = kStatusSplitX + 4;
    const int16_t width = 232 - kStatusSplitX;
    const uint8_t shown = visible < kInventoryWindow ? visible : kInventoryWindow;
    for (uint8_t slot = 0; slot < shown; ++slot) {
        const uint8_t index = pet.inventoryIndexAt(start + slot);
        const int16_t y = kStatusCardY + slot * kStatusCardRow;
        const bool active = index == current;
        display_.fillRoundRect(x, y, width, kStatusCardH, 4, kChip);
        display_.drawRoundRect(x, y, width, kStatusCardH, 4, active ? TFT_YELLOW : kInk);
        assets_.drawFrame(display_, icons[index], 0, x + 2, y + 2, false, -1, 72);
        display_.setTextColor(kInk, kChip);
        if (index < 6) {
            char line[20];
            snprintf(line, sizeof(line), "%s x%u", copy::itemName(index, spanish), pet.itemCount(index));
            drawLabel(line, x + 24, y + 5, width - 28, 2);
        } else {
            drawLabel(copy::itemName(index, spanish), x + 24, y + 5, width - 28, 2);
        }
    }
}

void Panels::drawEvolutionTree(const Navigation& navigation) {
    const uint8_t selected = navigation.panelIndex() % Navigation::kEvolutionNodeCount;
    const int16_t stride = kEvoChip + kEvoGap;
    const int16_t sparkX = kEvoX0 + stride;
    const int16_t fireX = kEvoX0 + stride * 2;
    display_.drawLine(sparkX + kEvoChip, kEvoColorY + kEvoChip / 2, fireX, kEvoColorY + kEvoChip / 2, kInk);
    display_.drawLine(fireX, kEvoColorY + kEvoChip / 2, fireX, kEvoDarkY + kEvoChip / 2, kInk);
    for (uint8_t index = 0; index < Navigation::kEvolutionNodeCount; ++index) {
        const uint8_t stage = Navigation::evolutionNodeStage(index);
        const bool dark = Navigation::evolutionNodeDark(index);
        const SpeciesId species = kEvolutionStages[stage];
        const int16_t x = kEvoX0 + stage * stride;
        const int16_t y = dark ? kEvoDarkY : kEvoColorY;
        const bool hidden = (dark && stage >= 2) || (!dark && stage > navigation.currentStage());
        const bool active = index == selected;
        display_.fillRoundRect(x, y, kEvoChip, kEvoChip, 4, kChip);
        display_.drawRoundRect(x, y, kEvoChip, kEvoChip, 4, active ? TFT_YELLOW : kInk);
        assets_.drawFrame(display_, portraitPath(species, true), 0, x + 2, y + 2, false, hidden ? TFT_BLACK : -1);
    }
}

void Panels::drawEvolution(const Navigation& navigation, bool spanish, const PetState& pet, bool detail) {
    if (!detail) {
        drawEvolutionTree(navigation);
        return;
    }
    const uint8_t selected = navigation.panelIndex() % Navigation::kEvolutionNodeCount;
    const uint8_t stage = Navigation::evolutionNodeStage(selected);
    const bool dark = Navigation::evolutionNodeDark(selected);
    const bool hidden = (dark && stage >= 2) || (!dark && stage > navigation.currentStage());
    const SpeciesId species = kEvolutionStages[stage];
    assets_.drawFrame(display_, portraitPath(species, true), 0, 32, 56, false, hidden ? TFT_BLACK : -1);
    display_.setTextColor(kInk, kPanel);
    display_.setTextDatum(MC_DATUM);
    drawLabel(hidden ? "???" : copy::evoShort(stage, spanish), 50, 96, 88, 2);
    if (hidden) {
        drawLabel("???", 50, 108, 88, 1);
    } else {
        const bool now = stage == navigation.currentStage();
        if (now) {
            char status[20];
            snprintf(
                status,
                sizeof(status),
                "%s %lus CM%u",
                copy::evoNow(spanish),
                static_cast<unsigned long>(pet.stageAgeSeconds()),
                pet.careMistakes()
            );
            drawLabel(status, 50, 108, 88, 1);
        } else {
            drawLabel(copy::evoReached(spanish), 50, 108, 88, 1);
        }
        char requirements[40];
        Evolution().writeReachRequirements(species, spanish, requirements, sizeof(requirements));
        if (requirements[0] != '\0') {
            char* space = strchr(requirements, ' ');
            if (space != nullptr) {
                *space = '\0';
                drawLabel(requirements, 50, 118, 88, 1);
                drawLabel(space + 1, 50, 126, 88, 1);
            } else {
                drawLabel(requirements, 50, 118, 88, 1);
            }
        }
    }
    display_.setTextDatum(TL_DATUM);
    const int16_t x = kStatusSplitX + 4;
    const int16_t width = 232 - kStatusSplitX;
    const uint8_t start = inventoryWindowStart(Navigation::kEvolutionNodeCount, selected);
    for (uint8_t slot = 0; slot < kInventoryWindow; ++slot) {
        const uint8_t index = static_cast<uint8_t>(start + slot);
        const uint8_t listStage = Navigation::evolutionNodeStage(index);
        const bool listDark = Navigation::evolutionNodeDark(index);
        const bool listHidden = (listDark && listStage >= 2) || (!listDark && listStage > navigation.currentStage());
        const int16_t y = kStatusCardY + slot * kStatusCardRow;
        const bool active = index == selected;
        display_.fillRoundRect(x, y, width, kStatusCardH, 4, kChip);
        display_.drawRoundRect(x, y, width, kStatusCardH, 4, active ? TFT_YELLOW : kInk);
        assets_.drawFrame(display_, "/ui/icons/pedia.vpa", 0, x + 2, y + 2);
        display_.setTextColor(kInk, kChip);
        drawLabel(listHidden ? "???" : copy::evoShort(listStage, spanish), x + 24, y + 5, width - 28, 2);
    }
}

void Panels::drawOptions(
    uint8_t selected,
    BleStatus bluetoothStatus,
    bool spanish,
    const char* language,
    bool soundEnabled
) {
    const char* bluetooth = "OFF";
    switch (bluetoothStatus) {
        case BleStatus::Advertising: bluetooth = "ADV"; break;
        case BleStatus::Connected: bluetooth = "ON"; break;
        case BleStatus::Error: bluetooth = "ERR"; break;
        case BleStatus::Off: break;
    }
    const uint8_t current = selected % 9;
    const char* shortLabels[] = {"BT", "LANG", "SND", "SAVE", "LOAD", "DATE", "TIME", "EVO", "BACK"};
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
    };
    for (uint8_t index = 0; index < 9; ++index) {
        const uint8_t col = index % 3;
        const uint8_t row = index / 3;
        const int16_t x = 8 + col * 76;
        const int16_t y = 54 + row * 26;
        const bool active = index == current;
        const uint16_t fill = active ? TFT_YELLOW : kChip;
        display_.fillRoundRect(x, y, 72, 24, 4, fill);
        display_.drawRoundRect(x, y, 72, 24, 4, active ? TFT_YELLOW : kInk);
        assets_.drawFrame(display_, icons[index], 0, x + 2, y + 2, false, -1, 72);
        display_.setTextColor(kInk, fill);
        if (extras[index][0] != '\0') {
            char line[16];
            snprintf(line, sizeof(line), "%s %s", shortLabels[index], extras[index]);
            drawLabel(line, x + 24, y + 5, 46, 1);
        } else {
            drawLabel(shortLabels[index], x + 24, y + 5, 46, 2);
        }
    }
}

void Panels::drawRest(
    uint8_t selected,
    bool spanish,
    bool cold,
    bool hasBackup,
    SpeciesId backupSpecies
) {
    const char* parked = copy::emptySlot(spanish);
    if (hasBackup) {
        switch (backupSpecies) {
            case SpeciesId::Baby: parked = "SPARKMON"; break;
            case SpeciesId::Rookie: parked = "FIREMON"; break;
            case SpeciesId::Champion: parked = "FLAMEMON"; break;
            case SpeciesId::Ultimate: parked = "DRAGFIREMON"; break;
            case SpeciesId::Egg: parked = "EGG"; break;
        }
    }
    char coldLine[24];
    char backupLine[28];
    snprintf(coldLine, sizeof(coldLine), "%s: %s", copy::cold(spanish), cold ? copy::on(spanish) : copy::off(spanish));
    snprintf(backupLine, sizeof(backupLine), "%s: %s", copy::backup(spanish), parked);
    const char* rows[] = {
        copy::sleep(spanish),
        coldLine,
        backupLine,
        copy::back(spanish),
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
    const bool panelChanged = panel != lastPanel_ || spanish != lastSpanish_;
    lastPanel_ = panel;
    lastSpanish_ = spanish;
    switch (panel) {
        case PanelId::Status: {
            const uint8_t page = navigation.panelIndex();
            char title[20];
            snprintf(
                title,
                sizeof(title),
                "%s %u/%u",
                copy::statusTitle(spanish),
                (page % Navigation::kStatusPages) + 1,
                Navigation::kStatusPages
            );
            beginPanel(panelChanged || lastStatusPage_ != page, navigation.menuIndex(), title, calling);
            lastStatusPage_ = page;
            drawStatusPet(pet, nowMs);
            drawStatus(pet, spanish, page, nowMs);
            break;
        }
        case PanelId::Inventory:
            beginPanel(panelChanged, navigation.menuIndex(), copy::inventoryTitle(spanish), calling);
            drawInventory(navigation.panelIndex(), spanish, pet);
            break;
        case PanelId::EvolutionTree:
            beginPanel(panelChanged, navigation.menuIndex(), copy::evolutionTitle(spanish), calling);
            drawEvolution(navigation, spanish, pet, false);
            break;
        case PanelId::EvolutionDetail:
            beginPanel(panelChanged, navigation.menuIndex(), copy::evolutionDetailTitle(spanish), calling);
            drawEvolution(navigation, spanish, pet, true);
            break;
        case PanelId::Options:
            beginPanel(panelChanged, navigation.menuIndex(), copy::optionsTitle(spanish), calling);
            drawOptions(navigation.panelIndex(), bluetoothStatus, spanish, language, soundEnabled);
            break;
        case PanelId::Rest:
            beginPanel(panelChanged, navigation.menuIndex(), copy::restTitle(spanish), calling);
            drawRest(navigation.panelIndex(), spanish, pet.cold(), hasBackup, backupSpecies);
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

}  // namespace vpet
