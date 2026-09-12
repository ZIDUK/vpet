#include "vpet/Panels.h"
#include "vpet/Strings.h"

#include <stdio.h>
#include <time.h>

namespace vpet {
namespace {
constexpr const char* kMenuIcons[] = {
    "/ui/icons/status.vpa", "/ui/icons/feed.vpa", "/ui/icons/training.vpa",
    "/ui/icons/battle.vpa", "/ui/icons/rest.vpa", "/ui/icons/items.vpa",
    "/ui/icons/pedia.vpa", "/ui/icons/options.vpa",
};
constexpr uint16_t kPanel = 0xD6B4;
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
}

void Panels::drawLabel(const char* text, int16_t x, int16_t y, int16_t width, uint8_t font) {
    String fitted(text);
    while (fitted.length() > 1 && display_.textWidth(fitted, font) > width) {
        fitted.remove(fitted.length() - 1);
    }
    display_.drawString(fitted, x, y, font);
}

void Panels::drawChrome(uint8_t selected, const char* title) {
    display_.fillScreen(TFT_BLACK);
    for (uint8_t index = 0; index < 8; ++index) {
        assets_.drawFrame(display_, kMenuIcons[index], 0, index * 30 + 5, 2);
    }
    const int16_t selectorX = (selected % 8) * 30;
    display_.drawRect(selectorX, 0, 30, 24, TFT_YELLOW);
    display_.drawRect(selectorX + 1, 1, 28, 22, TFT_YELLOW);
    display_.fillRect(0, 24, 240, 111, kPanel);
    display_.fillRect(3, 27, 234, 20, kInk);
    display_.setTextDatum(MC_DATUM);
    display_.setTextColor(TFT_WHITE, kInk);
    drawLabel(title, 120, 37, 220, 2);
    display_.setTextDatum(TL_DATUM);
    display_.setTextColor(kInk, kPanel);
}

void Panels::beginPanel(bool panelChanged, uint8_t selected, const char* title) {
    if (panelChanged) {
        drawChrome(selected, title);
        return;
    }
    display_.fillRect(0, 48, 240, 87, kPanel);
    display_.setTextDatum(TL_DATUM);
    display_.setTextColor(kInk, kPanel);
}

void Panels::drawStat(const char* icon, const char* label, const char* value, int16_t x, int16_t y) {
    assets_.drawFrame(display_, icon, 0, x, y);
    display_.setTextColor(kInk, kPanel);
    char line[24];
    snprintf(line, sizeof(line), "%s %s", label, value);
    drawLabel(line, x + 22, y + 3, 88, 2);
}

void Panels::drawBar(const char* label, int value, int16_t y) {
    char line[16];
    snprintf(line, sizeof(line), "%s %d", label, value);
    drawLabel(line, 6, y, 50, 2);
    display_.fillRect(36, y + 4, 200, 8, 0x8C51);
    const int clamped = value < 0 ? 0 : (value > 100 ? 100 : value);
    const int16_t filled = static_cast<int16_t>((clamped * 200) / 100);
    if (filled > 0) display_.fillRect(36, y + 4, filled, 8, kInk);
}

void Panels::drawStatus(const PetState& pet, bool spanish, uint8_t page) {
    if ((page % 2) == 0) {
        drawBar(copy::hp(spanish), pet.health(), 54);
        drawBar(copy::hunger(spanish), pet.hunger(), 80);
        drawBar(copy::energy(spanish), pet.energy(), 106);
        return;
    }
    char value[16];
    snprintf(value, sizeof(value), "%lus", static_cast<unsigned long>(pet.ageSeconds()));
    drawStat("/ui/icons/clock.vpa", copy::age(spanish), value, 6, 50);
    snprintf(value, sizeof(value), "%d", pet.effort());
    drawStat("/ui/icons/training.vpa", copy::effort(spanish), value, 6, 72);
    snprintf(value, sizeof(value), "%d", pet.battles());
    drawStat("/ui/icons/battle.vpa", copy::battles(spanish), value, 6, 94);
    snprintf(value, sizeof(value), "%d", pet.happiness());
    drawStat("/ui/icons/heart.vpa", copy::mood(spanish), value, 126, 50);
    int clock[5] = {2026, 1, 1, 0, 0};
    const time_t now = time(nullptr);
    struct tm parts {};
    localtime_r(&now, &parts);
    if (parts.tm_year + 1900 >= 2024) {
        clock[0] = parts.tm_year + 1900;
        clock[1] = parts.tm_mon + 1;
        clock[2] = parts.tm_mday;
        clock[3] = parts.tm_hour;
        clock[4] = parts.tm_min;
    }
    char line[32];
    DateTimeMenu::writeClock(clock, line, sizeof(line));
    assets_.drawFrame(display_, "/ui/icons/clock.vpa", 0, 6, 114);
    display_.setTextColor(kInk, kPanel);
    drawLabel(line, 28, 117, 204, 2);
}

void Panels::drawInventory(uint8_t selected, bool spanish, const PetState& pet) {
    char meat[16];
    char energy[16];
    char exp[16];
    char ring[16];
    snprintf(meat, sizeof(meat), "%s x%u", copy::meat(spanish), pet.itemCount(0));
    snprintf(energy, sizeof(energy), "%s x%u", copy::itemEnergy(spanish), pet.itemCount(1));
    snprintf(exp, sizeof(exp), "%s x%u", copy::exp(spanish), pet.itemCount(2));
    snprintf(ring, sizeof(ring), "%s x%u", copy::fireRing(spanish), pet.itemCount(3));
    const char* labels[] = {meat, energy, exp, ring, copy::back(spanish)};
    const char* icons[] = {
        "/ui/icons/feed.vpa",
        "/ui/icons/rest.vpa",
        "/ui/icons/training.vpa",
        "/ui/icons/items.vpa",
        "/ui/icons/options.vpa",
    };
    const uint8_t current = pet.clampVisibleInventoryIndex(selected);
    const uint8_t visible = pet.visibleInventoryCount();
    uint8_t selectedSlot = 0;
    for (uint8_t slot = 0; slot < visible; ++slot) {
        if (pet.inventoryIndexAt(slot) == current) selectedSlot = slot;
    }
    const uint8_t windowStart = selectedSlot < 4 ? 0 : static_cast<uint8_t>(selectedSlot - 3);
    const uint8_t rows = visible < 4 ? visible : 4;
    for (uint8_t slot = 0; slot < rows; ++slot) {
        const uint8_t index = pet.inventoryIndexAt(windowStart + slot);
        const int16_t y = 52 + slot * 20;
        const bool active = index == current;
        if (active) display_.fillRect(5, y - 2, 230, 19, TFT_YELLOW);
        assets_.drawFrame(display_, icons[index], 0, 6, y - 1);
        display_.setTextColor(kInk, active ? TFT_YELLOW : kPanel);
        drawLabel(labels[index], 28, y + 2, 200, 2);
    }
}

void Panels::drawEvolution(const Navigation& navigation, bool detail, bool spanish) {
    (void)spanish;
    const EvolutionNode selected = navigation.selectedEvolutionNode();
    if (detail) {
        display_.drawRect(74, 51, 92, 72, TFT_YELLOW);
        if (selected.hidden) {
            assets_.drawFrame(display_, portraitPath(selected.species, false), 0, 76, 35, false, TFT_BLACK);
            display_.setTextColor(kInk, kPanel);
            display_.setTextDatum(MC_DATUM);
            display_.drawString("???", 120, 112, 2);
        } else {
            assets_.drawFrame(display_, portraitPath(selected.species, false), 0, 76, 35);
            display_.setTextColor(kInk, kPanel);
            display_.setTextDatum(MC_DATUM);
            display_.drawString(selected.label, 120, 108, 2);
        }
        display_.setTextDatum(TL_DATUM);
        return;
    }
    const uint8_t selectedIndex = navigation.panelIndex() % 5;
    const uint8_t windowStart = selectedIndex == 0 ? 0 : (selectedIndex >= 4 ? 2 : selectedIndex - 1);
    for (uint8_t slot = 0; slot < 3; ++slot) {
        const uint8_t index = windowStart + slot;
        const SpeciesId species = kEvolutionStages[index];
        Navigation copy = navigation;
        copy.select(species);
        const EvolutionNode node = copy.selectedEvolutionNode();
        const int16_t x = 5 + slot * 79;
        display_.drawRect(x, 52, 72, 70, index == selectedIndex ? TFT_YELLOW : kInk);
        if (node.hidden) {
            assets_.drawFrame(display_, portraitPath(species, true), 0, x + 18, 57, false, TFT_BLACK);
            display_.setTextColor(kInk, kPanel);
            drawLabel("???", x + 25, 99, 36, 1);
        } else {
            assets_.drawFrame(display_, portraitPath(species, true), 0, x + 18, 57);
            display_.setTextColor(kInk, kPanel);
            drawLabel(node.label, x + 4, 99, 64, 1);
        }
        if (index < 4 && slot < 2) drawLabel(">", x + 73, 73, 8, 2);
    }
}

void Panels::drawOptions(
    uint8_t selected,
    BleStatus bluetoothStatus,
    bool spanish,
    const char* language,
    bool soundEnabled
) {
    const char* bluetooth = copy::bluetoothOff(spanish);
    switch (bluetoothStatus) {
        case BleStatus::Advertising: bluetooth = copy::bluetoothAdvertising(spanish); break;
        case BleStatus::Connected: bluetooth = copy::bluetoothConnected(spanish); break;
        case BleStatus::Error: bluetooth = copy::bluetoothError(spanish); break;
        case BleStatus::Off: break;
    }
    char languageLine[24];
    char soundLine[24];
    snprintf(languageLine, sizeof(languageLine), "%s: %s", copy::language(spanish), language);
    snprintf(soundLine, sizeof(soundLine), "%s: %s", copy::sound(spanish), soundEnabled ? copy::on(spanish) : copy::off(spanish));
    const char* options[] = {
        bluetooth,
        languageLine,
        soundLine,
        copy::save(spanish),
        copy::load(spanish),
        copy::dateTitle(spanish),
        copy::timeTitle(spanish),
        copy::evolve(spanish),
        copy::back(spanish)
    };
    const uint8_t current = selected % 9;
    const uint8_t windowStart = current < 4 ? 0 : (current < 8 ? 4 : 5);
    for (uint8_t slot = 0; slot < 4; ++slot) {
        const uint8_t index = windowStart + slot;
        const int16_t y = 52 + slot * 20;
        const bool active = index == current;
        if (active) display_.fillRect(5, y - 2, 230, 19, TFT_YELLOW);
        display_.setTextColor(kInk, active ? TFT_YELLOW : kPanel);
        drawLabel(options[index], 10, y, 218, 2);
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
    bool soundEnabled
) {
    output_.startWrite();
    const PanelId panel = navigation.panel();
    const bool spanish = languageIsSpanish(language);
    const bool panelChanged = panel != lastPanel_ || spanish != lastSpanish_;
    lastPanel_ = panel;
    lastSpanish_ = spanish;
    switch (panel) {
        case PanelId::Status:
            beginPanel(panelChanged, navigation.menuIndex(), copy::statusTitle(spanish));
            drawStatus(pet, spanish, navigation.panelIndex());
            break;
        case PanelId::Inventory:
            beginPanel(panelChanged, navigation.menuIndex(), copy::inventoryTitle(spanish));
            drawInventory(navigation.panelIndex(), spanish, pet);
            break;
        case PanelId::EvolutionTree:
            beginPanel(panelChanged, navigation.menuIndex(), copy::evolutionTitle(spanish));
            drawEvolution(navigation, false, spanish);
            break;
        case PanelId::EvolutionDetail:
            beginPanel(panelChanged, navigation.menuIndex(), copy::evolutionDetailTitle(spanish));
            drawEvolution(navigation, true, spanish);
            break;
        case PanelId::Options:
            beginPanel(panelChanged, navigation.menuIndex(), copy::optionsTitle(spanish));
            drawOptions(navigation.panelIndex(), bluetoothStatus, spanish, language, soundEnabled);
            break;
        case PanelId::DateTime:
            beginPanel(
                panelChanged,
                navigation.menuIndex(),
                dateMenu.editingDate() ? copy::dateTitle(spanish) : copy::timeTitle(spanish)
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
