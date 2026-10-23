#include "vpet/Navigation.h"
#include "vpet/MenuAccess.h"

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
    panelIndex_ = currentStage_;
    selectedSpecies_ = kEvolutionStages[currentStage_];
}

void Navigation::openEvolutionTree(SpeciesId currentSpecies) {
    setCurrentSpecies(currentSpecies);
    openEvolutionTree();
}

void Navigation::select(SpeciesId species) {
    selectedSpecies_ = species;
    panelIndex_ = stageIndex(species);
}

bool Navigation::evolutionSelectedHidden() const {
    const uint8_t stage = evolutionNodeStage(panelIndex_);
    return stage > currentStage_;
}

EvolutionNode Navigation::selectedEvolutionNode() const {
    const uint8_t stage = evolutionNodeStage(panelIndex_);
    const SpeciesId species = kEvolutionStages[stage];
    const bool hidden = evolutionSelectedHidden();
    const char* label = "EGG";
    if (!hidden && species == SpeciesId::Baby) label = "SPARKMON";
    if (!hidden && species == SpeciesId::Rookie) label = "FIREMON";
    if (!hidden && species == SpeciesId::Champion) label = "FLAMEMON";
    if (!hidden && species == SpeciesId::Ultimate) label = "DRAGFIREMON";
    if (hidden) label = "???";
    return {species, label, hidden};
}

void Navigation::openSelectedMenu() {
    switch (menuIndex_) {
        case 0:
            panel_ = PanelId::Status;
            panelIndex_ = 0;
            break;
        case 1:
            panel_ = PanelId::Feeding;
            panelIndex_ = 0;
            break;
        case 3:
            panel_ = PanelId::Exploration;
            panelIndex_ = 0;
            break;
        case 5:
            panel_ = PanelId::Rest;
            panelIndex_ = 0;
            break;
        case 6:
            panel_ = PanelId::Inventory;
            panelIndex_ = 0;
            break;
        case 7: openEvolutionTree(); break;
        case 8:
            panel_ = PanelId::Options;
            panelIndex_ = 0;
            break;
        default: break;
    }
}

void Navigation::dispatch(InputEvent event) {
    if (event == InputEvent::None) return;
    if (panel_ == PanelId::Home) {
        if (event == InputEvent::Next)
            menuIndex_ = menu_access::next(kEvolutionStages[currentStage_], menuIndex_);
        else if (event == InputEvent::Action) openSelectedMenu();
        return;
    }
    if (event == InputEvent::Back) {
        if (panel_ == PanelId::Options) return;
        panel_ = panel_ == PanelId::EvolutionDetail ? PanelId::EvolutionTree : PanelId::Home;
        return;
    }
    if (event == InputEvent::Next) {
        if (panel_ == PanelId::EvolutionTree || panel_ == PanelId::EvolutionDetail) {
            panelIndex_ = static_cast<uint8_t>((panelIndex_ + 1) % Navigation::kEvolutionNodeCount);
            selectedSpecies_ = kEvolutionStages[evolutionNodeStage(panelIndex_)];
        } else if (panel_ == PanelId::Options) {
            panelIndex_ = option_menu::next(panelIndex_);
        } else if (panel_ == PanelId::Inventory) {
            panelIndex_ = static_cast<uint8_t>((panelIndex_ + 1) % Navigation::kInventoryCount);
        } else if (panel_ == PanelId::Feeding) {
            panelIndex_ = static_cast<uint8_t>((panelIndex_ + 1) % Navigation::kFeedingCount);
        } else if (panel_ == PanelId::Status) {
            panelIndex_ = static_cast<uint8_t>((panelIndex_ + 1) % Navigation::kStatusPages);
        } else if (panel_ == PanelId::Rest) {
            panelIndex_ = static_cast<uint8_t>((panelIndex_ + 1) % Navigation::kRestCount);
        } else {
            panelIndex_ = (panelIndex_ + 1) % 8;
        }
    } else if (event == InputEvent::Action) {
        if (panel_ == PanelId::EvolutionTree && !evolutionSelectedHidden()) {
            panel_ = PanelId::EvolutionDetail;
        } else if (panel_ == PanelId::EvolutionDetail || panel_ == PanelId::Status) {
            panel_ = panel_ == PanelId::EvolutionDetail ? PanelId::EvolutionTree : PanelId::Home;
        }
        else if (panel_ == PanelId::Rest && panelIndex_ == Navigation::kRestCount - 1) {
            panel_ = PanelId::Home;
        }
        else if (panel_ == PanelId::Inventory && panelIndex_ == Navigation::kInventoryCount - 1) {
            panel_ = PanelId::Home;
        }
    }
}

}  // namespace vpet
