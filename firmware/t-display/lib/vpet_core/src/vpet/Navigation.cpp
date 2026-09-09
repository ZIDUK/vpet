#include "vpet/Navigation.h"

namespace vpet {
namespace {
constexpr SpeciesId kEvolutionStages[] = {
    SpeciesId::Egg, SpeciesId::Baby, SpeciesId::Rookie,
    SpeciesId::Champion, SpeciesId::Ultimate,
};

uint8_t stageIndex(SpeciesId species) {
    for (uint8_t index = 0; index < 5; ++index) {
        if (kEvolutionStages[index] == species) return index;
    }
    return 0;
}
}

void Navigation::setDiscovered(bool champion, bool ultimate) {
    championDiscovered_ = champion;
    ultimateDiscovered_ = ultimate;
    currentStage_ = ultimate ? 4 : (champion ? 3 : 2);
}

void Navigation::setCurrentSpecies(SpeciesId species) {
    currentStage_ = stageIndex(species);
    championDiscovered_ = currentStage_ >= 3;
    ultimateDiscovered_ = currentStage_ >= 4;
}

void Navigation::openEvolutionTree() {
    panel_ = PanelId::EvolutionTree;
    panelIndex_ = 0;
    selectedSpecies_ = kEvolutionStages[0];
}

void Navigation::select(SpeciesId species) {
    selectedSpecies_ = species;
    panelIndex_ = stageIndex(species);
}

EvolutionNode Navigation::selectedEvolutionNode() const {
    const bool hidden = stageIndex(selectedSpecies_) > currentStage_;
    const char* label = "EGG";
    if (!hidden && selectedSpecies_ == SpeciesId::Baby) label = "SPARKMON";
    if (!hidden && selectedSpecies_ == SpeciesId::Rookie) label = "FIREMON";
    if (!hidden && selectedSpecies_ == SpeciesId::Champion) label = "FLAMEMON";
    if (!hidden && selectedSpecies_ == SpeciesId::Ultimate) label = "DRAGFIREMON";
    if (hidden) label = "???";
    return {selectedSpecies_, label, hidden};
}

void Navigation::openSelectedMenu() {
    switch (menuIndex_) {
        case 0: panel_ = PanelId::Status; break;
        case 5: panel_ = PanelId::Inventory; break;
        case 6: openEvolutionTree(); break;
        case 7: panel_ = PanelId::Options; break;
        default: break;
    }
}

void Navigation::dispatch(InputEvent event) {
    if (event == InputEvent::None) return;
    if (panel_ == PanelId::Home) {
        if (event == InputEvent::Next) menuIndex_ = (menuIndex_ + 1) % 8;
        else if (event == InputEvent::Action) openSelectedMenu();
        return;
    }
    if (event == InputEvent::Back) {
        panel_ = panel_ == PanelId::EvolutionDetail ? PanelId::EvolutionTree : PanelId::Home;
        return;
    }
    if (event == InputEvent::Next) {
        if (panel_ == PanelId::EvolutionTree) {
            panelIndex_ = (panelIndex_ + 1) % 5;
            selectedSpecies_ = kEvolutionStages[panelIndex_];
        } else {
            panelIndex_ = (panelIndex_ + 1) % 8;
        }
    } else if (event == InputEvent::Action) {
        if (panel_ == PanelId::EvolutionTree) panel_ = PanelId::EvolutionDetail;
        else if (panel_ == PanelId::Status || panel_ == PanelId::Inventory) panel_ = PanelId::Home;
    }
}

}  // namespace vpet
