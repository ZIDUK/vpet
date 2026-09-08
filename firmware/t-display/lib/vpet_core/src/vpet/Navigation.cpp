#include "vpet/Navigation.h"

namespace vpet {

void Navigation::setDiscovered(bool champion, bool ultimate) {
    championDiscovered_ = champion;
    ultimateDiscovered_ = ultimate;
}

void Navigation::openEvolutionTree() {
    panel_ = PanelId::EvolutionTree;
    panelIndex_ = 0;
    selectedSpecies_ = SpeciesId::Rookie;
}

void Navigation::select(SpeciesId species) {
    selectedSpecies_ = species;
    panelIndex_ = static_cast<uint8_t>(species);
}

EvolutionNode Navigation::selectedEvolutionNode() const {
    const bool hidden =
        (selectedSpecies_ == SpeciesId::Champion && !championDiscovered_) ||
        (selectedSpecies_ == SpeciesId::Ultimate && !ultimateDiscovered_);
    const char* label = "FIREMON";
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
            panelIndex_ = (panelIndex_ + 1) % 3;
            selectedSpecies_ = static_cast<SpeciesId>(panelIndex_);
        } else {
            panelIndex_ = (panelIndex_ + 1) % 8;
        }
    } else if (event == InputEvent::Action) {
        if (panel_ == PanelId::EvolutionTree) panel_ = PanelId::EvolutionDetail;
        else if (panel_ == PanelId::Status || panel_ == PanelId::Inventory) panel_ = PanelId::Home;
    }
}

}  // namespace vpet
