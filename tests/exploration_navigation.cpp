#include <cassert>
#include "vpet/Navigation.h"

int main() {
    using namespace vpet;
    Navigation n;
    for (int i = 0; i < 9; ++i) {
        assert(n.menuIndex() == i);
        n.dispatch(InputEvent::Next);
    }
    assert(n.menuIndex() == 0);
    const uint8_t menus[] = {0, 1, 3, 5, 6, 7, 8};
    const PanelId panels[] = {PanelId::Status, PanelId::Feeding,
        static_cast<PanelId>(9), PanelId::Rest, PanelId::Inventory,
        PanelId::EvolutionTree, PanelId::Options};
    for (unsigned i = 0; i < sizeof(menus); ++i) {
        n.setPanel(PanelId::Home);
        n.setMenuIndex(menus[i]);
        n.dispatch(InputEvent::Action);
        assert(n.panel() == panels[i]);
    }
}
