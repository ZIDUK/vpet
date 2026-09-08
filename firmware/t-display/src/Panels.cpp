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
    display_.drawRect((selected % 8) * 30, 0, 30, 24, TFT_YELLOW);
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
            display_.fillRect(76, 53, 88, 68, TFT_BLACK);
            display_.setTextColor(TFT_WHITE, TFT_BLACK);
            display_.setTextDatum(MC_DATUM);
            display_.drawString("???", 120, 87, 2);
        } else {
            const char* portrait = selected.species == SpeciesId::Rookie
                ? "/animations/rookie/firemon_idle.vpa"
                : selected.species == SpeciesId::Champion
                    ? "/animations/champion/flamemon_idle.vpa"
                    : "/animations/ultimate/dragfiremon_idle.vpa";
            assets_.drawFrame(display_, portrait, 0, 76, 35);
            display_.setTextColor(kInk, kPanel);
            display_.setTextDatum(MC_DATUM);
            display_.drawString(selected.label, 120, 108, 2);
        }
        display_.setTextDatum(TL_DATUM);
        return;
    }
    for (uint8_t index = 0; index < 3; ++index) {
        const SpeciesId species = static_cast<SpeciesId>(index);
        Navigation copy = navigation;
        copy.select(species);
        const EvolutionNode node = copy.selectedEvolutionNode();
        const int16_t x = 5 + index * 79;
        display_.drawRect(x, 52, 72, 70, index == navigation.panelIndex() ? TFT_YELLOW : kInk);
        if (node.hidden) {
            display_.fillRect(x + 18, 57, 36, 36, TFT_BLACK);
            display_.setTextColor(TFT_WHITE, TFT_BLACK);
            display_.drawString("???", x + 25, 70, 1);
        } else {
            const char* portrait = index == 0 ? "/ui/evolution/firemon.vpa"
                : index == 1 ? "/ui/evolution/flamemon.vpa"
                : "/ui/evolution/dragfiremon.vpa";
            assets_.drawFrame(display_, portrait, 0, x + 18, 57);
            display_.setTextColor(kInk, kPanel);
            drawLabel(node.label, x + 4, 99, 64, 1);
        }
        if (index < 2) drawLabel(">", x + 73, 73, 8, 2);
    }
}

void Panels::drawOptions(uint8_t selected) {
    constexpr const char* options[] = {
        "LANGUAGE: ES", "SOUND: ON", "SAVE", "LOAD", "WIFI", "DATE / TIME", "BACK"
    };
    for (uint8_t index = 0; index < 7; ++index) {
        const int16_t y = 50 + index * 11;
        if (index == selected % 7) display_.fillRect(5, y - 1, 230, 11, TFT_YELLOW);
        display_.setTextColor(kInk, index == selected % 7 ? TFT_YELLOW : kPanel);
        drawLabel(options[index], 10, y, 218, 1);
    }
}

void Panels::drawWifi(const Navigation& navigation, const NetworkService& network) {
    if (!const_cast<NetworkService&>(network).scanComplete()) {
        drawLabel("SCANNING...", 75, 78, 100, 2);
        return;
    }
    const size_t count = network.networkCount();
    const size_t visible = count > 5 ? 5 : count;
    for (size_t index = 0; index < visible; ++index) {
        const int16_t y = 51 + index * 15;
        if (index == navigation.panelIndex() % (count + 1)) {
            display_.fillRect(5, y - 2, 230, 13, TFT_YELLOW);
        }
        drawLabel(network.networkName(index).c_str(), 10, y, 220, 1);
    }
    const int16_t y = 51 + visible * 15;
    drawLabel("BACK", 10, y, 220, 1);
}

void Panels::drawPassword(const PasswordEditor& password, const char* selectedSsid) {
    drawLabel(selectedSsid, 8, 52, 224, 1);
    display_.drawRect(8, 66, 224, 20, kInk);
    String masked;
    for (size_t index = 0; index < password.password().size(); ++index) masked += '*';
    drawLabel(masked.c_str(), 13, 72, 214, 1);
    drawLabel(password.groupLabel(), 8, 94, 55, 1);
    display_.drawRect(67, 91, 165, 31, TFT_YELLOW);
    display_.setTextDatum(MC_DATUM);
    drawLabel(password.keyLabel(), 149, 106, 150, 2);
    display_.setTextDatum(TL_DATUM);
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
    const NetworkService& network,
    const PasswordEditor& password,
    const char* selectedSsid,
    const int* dateTime,
    bool editingDate,
    uint8_t dateField
) {
    output_.startWrite();
    switch (navigation.panel()) {
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
            drawChrome(navigation.menuIndex(), "OPTIONS");
            drawOptions(navigation.panelIndex());
            break;
        case PanelId::WifiList:
            drawChrome(navigation.menuIndex(), "WIFI NETWORKS");
            drawWifi(navigation, network);
            break;
        case PanelId::Password:
            drawChrome(navigation.menuIndex(), "WIFI PASSWORD");
            drawPassword(password, selectedSsid);
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
