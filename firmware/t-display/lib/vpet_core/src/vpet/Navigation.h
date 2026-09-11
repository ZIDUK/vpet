#pragma once

#include <stdint.h>

#include "vpet/Input.h"
#include "vpet/PetState.h"

namespace vpet {

enum class PanelId : uint8_t {
    Home,
    Status,
    Inventory,
    EvolutionTree,
    EvolutionDetail,
    Options,
    DateTime,
};

struct EvolutionNode {
    SpeciesId species;
    const char* label;
    bool hidden;
};

class Navigation {
public:
    static constexpr uint8_t kOptionCount = 9;

    void dispatch(InputEvent event);
    void setMenuIndex(uint8_t index) { menuIndex_ = index % 8; }
    void setDiscovered(bool champion, bool ultimate);
    void setCurrentSpecies(SpeciesId species);
    void openEvolutionTree();
    void select(SpeciesId species);
    void setPanel(PanelId panel, uint8_t index = 0) { panel_ = panel; panelIndex_ = index; }
    void setPanelIndex(uint8_t index) { panelIndex_ = index; }
    EvolutionNode selectedEvolutionNode() const;

    PanelId panel() const { return panel_; }
    uint8_t menuIndex() const { return menuIndex_; }
    uint8_t panelIndex() const { return panelIndex_; }
    SpeciesId selectedSpecies() const { return selectedSpecies_; }

private:
    void openSelectedMenu();

    PanelId panel_ = PanelId::Home;
    uint8_t menuIndex_ = 0;
    uint8_t panelIndex_ = 0;
    SpeciesId selectedSpecies_ = SpeciesId::Egg;
    uint8_t currentStage_ = 0;
    bool championDiscovered_ = true;
    bool ultimateDiscovered_ = true;
};

}  // namespace vpet
