#include <unity.h>

#include "vpet/Navigation.h"

void test_menu_opens_expected_panels() {
    vpet::Navigation navigation;
    navigation.setMenuIndex(6);
    navigation.dispatch(vpet::InputEvent::Action);
    TEST_ASSERT_EQUAL(vpet::PanelId::EvolutionTree, navigation.panel());
    navigation.dispatch(vpet::InputEvent::Back);
    TEST_ASSERT_EQUAL(vpet::PanelId::Home, navigation.panel());
}

void test_hidden_branch_does_not_reveal_identity() {
    vpet::Navigation navigation;
    navigation.setDiscovered(false, false);
    navigation.openEvolutionTree();
    navigation.select(vpet::SpeciesId::Ultimate);
    const vpet::EvolutionNode node = navigation.selectedEvolutionNode();
    TEST_ASSERT_TRUE(node.hidden);
    TEST_ASSERT_EQUAL_STRING("???", node.label);
}

void test_back_returns_from_detail_to_same_tree_node() {
    vpet::Navigation navigation;
    navigation.openEvolutionTree();
    navigation.select(vpet::SpeciesId::Ultimate);
    navigation.dispatch(vpet::InputEvent::Action);
    navigation.dispatch(vpet::InputEvent::Back);
    TEST_ASSERT_EQUAL(vpet::PanelId::EvolutionTree, navigation.panel());
    TEST_ASSERT_EQUAL(vpet::SpeciesId::Ultimate, navigation.selectedSpecies());
}
