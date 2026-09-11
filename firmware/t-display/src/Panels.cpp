#include "vpet/Panels.h"

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

void Panels::drawStatus(const PetState& pet) {
    char line[32];
    snprintf(line, sizeof(line), "HP %d/100", pet.health());
    drawLabel(line, 8, 53, 104, 2);
    snprintf(line, sizeof(line), "HUN %d", pet.hunger());
    drawLabel(line, 8, 75, 104, 2);
    snprintf(line, sizeof(line), "ENE %d", pet.energy());
    drawLabel(line, 8, 97, 104, 2);
    snprintf(line, sizeof(line), "AGE %lus", static_cast<unsigned long>(pet.ageSeconds()));
    drawLabel(line, 126, 53, 106, 2);
    snprintf(line, sizeof(line), "EFF %d", pet.effort());
    drawLabel(line, 126, 75, 106, 2);
    snprintf(line, sizeof(line), "BAT %d", pet.battles());
    drawLabel(line, 126, 97, 106, 2);
    drawLabel("ACTION: CLOSE", 73, 121, 95, 1);
}

void Panels::drawInventory(uint8_t selected) {
    constexpr const char* items[] = {"MEAT x3", "ENERGY x2", "EXP x1", "FIRE RING x1", "BACK"};
    for (uint8_t index = 0; index < 5; ++index) {
        const int16_t x = 8 + (index % 3) * 77;
        const int16_t y = 53 + (index / 3) * 36;
        display_.drawRect(x, y, 70, 30, index == selected % 5 ? TFT_YELLOW : kInk);
        drawLabel(items[index], x + 4, y + 10, 62, 1);
    }
}

void Panels::drawEvolution(const Navigation& navigation, bool detail) {
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

void Panels::drawOptions(uint8_t selected, BleStatus bluetoothStatus) {
    const char* bluetooth = "BLUETOOTH: OFF";
    switch (bluetoothStatus) {
        case BleStatus::Advertising: bluetooth = "BLUETOOTH: ADVERTISING"; break;
        case BleStatus::Connected: bluetooth = "BLUETOOTH: CONNECTED"; break;
        case BleStatus::Error: bluetooth = "BLUETOOTH: ERROR"; break;
        case BleStatus::Off: break;
    }
    const char* options[] = {
        bluetooth, "LANGUAGE: ES", "SOUND: ON", "SAVE", "LOAD", "DATE", "TIME", "EVOLVE", "BACK"
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

void Panels::drawDateTime(const int* values, bool editingDate, uint8_t field) {
    char value[32];
    if (editingDate) snprintf(value, sizeof(value), "%04d / %02d / %02d", values[0], values[1], values[2]);
    else snprintf(value, sizeof(value), "%02d : %02d", values[3], values[4]);
    drawLabel(editingDate ? "EDIT DATE" : "EDIT TIME", 83, 57, 90, 1);
    display_.drawRect(20, 76, 200, 34, TFT_YELLOW);
    display_.setTextDatum(MC_DATUM);
    drawLabel(value, 120, 93, 184, 2);
    display_.setTextDatum(TL_DATUM);
    char hint[24];
    snprintf(hint, sizeof(hint), "FIELD %u  NEXT:+ ACTION:OK", field + 1);
    drawLabel(hint, 32, 119, 205, 1);
}

void Panels::draw(
    const Navigation& navigation,
    const PetState& pet,
    BleStatus bluetoothStatus,
    const int* dateTime,
    bool editingDate,
    uint8_t dateField
) {
    output_.startWrite();
    const PanelId panel = navigation.panel();
    const bool panelChanged = panel != lastPanel_;
    lastPanel_ = panel;
    switch (panel) {
        case PanelId::Status:
            drawChrome(navigation.menuIndex(), "STATUS");
            drawStatus(pet);
            break;
        case PanelId::Inventory:
            drawChrome(navigation.menuIndex(), "INVENTORY");
            drawInventory(navigation.panelIndex());
            break;
        case PanelId::EvolutionTree:
            drawChrome(navigation.menuIndex(), "EVOLUTION");
            drawEvolution(navigation, false);
            break;
        case PanelId::EvolutionDetail:
            drawChrome(navigation.menuIndex(), "EVOLUTION DETAIL");
            drawEvolution(navigation, true);
            break;
        case PanelId::Options:
            if (panelChanged) {
                drawChrome(navigation.menuIndex(), "OPTIONS");
            } else {
                display_.fillRect(0, 48, 240, 87, kPanel);
            }
            drawOptions(navigation.panelIndex(), bluetoothStatus);
            break;
        case PanelId::DateTime:
            drawChrome(navigation.menuIndex(), "DATE / TIME");
            drawDateTime(dateTime, editingDate, dateField);
            break;
        case PanelId::Home:
            break;
    }
    display_.pushSprite(0, 0);
    output_.endWrite();
}

}  // namespace vpet
