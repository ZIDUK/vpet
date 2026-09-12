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

void test_next_moves_options_cursor() {
    vpet::Navigation navigation;
    navigation.setMenuIndex(7);
    navigation.dispatch(vpet::InputEvent::Action);

    TEST_ASSERT_EQUAL(vpet::PanelId::Options, navigation.panel());
    TEST_ASSERT_EQUAL(0, navigation.panelIndex());

    navigation.dispatch(vpet::InputEvent::Next);
    TEST_ASSERT_EQUAL(1, navigation.panelIndex());
}

void test_options_next_wraps_like_header_menu() {
    vpet::Navigation navigation;
    navigation.setMenuIndex(7);
    navigation.dispatch(vpet::InputEvent::Action);

    for (uint8_t step = 0; step < 9; ++step) {
        TEST_ASSERT_EQUAL(step, navigation.panelIndex());
        navigation.dispatch(vpet::InputEvent::Next);
    }

    TEST_ASSERT_EQUAL(vpet::PanelId::Options, navigation.panel());
    TEST_ASSERT_EQUAL(0, navigation.panelIndex());
}

void test_back_in_options_is_ignored() {
    vpet::Navigation navigation;
    navigation.setMenuIndex(7);
    navigation.dispatch(vpet::InputEvent::Action);
    navigation.dispatch(vpet::InputEvent::Next);
    navigation.dispatch(vpet::InputEvent::Next);

    TEST_ASSERT_EQUAL(2, navigation.panelIndex());
    navigation.dispatch(vpet::InputEvent::Back);
    TEST_ASSERT_EQUAL(vpet::PanelId::Options, navigation.panel());
    TEST_ASSERT_EQUAL(2, navigation.panelIndex());
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

void test_next_wraps_inventory_like_options() {
    vpet::Navigation navigation;
    navigation.setMenuIndex(5);
    navigation.dispatch(vpet::InputEvent::Action);
    TEST_ASSERT_EQUAL(vpet::PanelId::Inventory, navigation.panel());
    TEST_ASSERT_EQUAL(0, navigation.panelIndex());
    for (uint8_t step = 0; step < 5; ++step) {
        TEST_ASSERT_EQUAL(step, navigation.panelIndex());
        navigation.dispatch(vpet::InputEvent::Next);
    }
    TEST_ASSERT_EQUAL(0, navigation.panelIndex());
}

void test_action_on_inventory_item_stays_in_menu() {
    vpet::Navigation navigation;
    navigation.setMenuIndex(5);
    navigation.dispatch(vpet::InputEvent::Action);
    TEST_ASSERT_EQUAL(vpet::PanelId::Inventory, navigation.panel());

    navigation.dispatch(vpet::InputEvent::Action);
    TEST_ASSERT_EQUAL(vpet::PanelId::Inventory, navigation.panel());
    TEST_ASSERT_EQUAL(0, navigation.panelIndex());

    navigation.dispatch(vpet::InputEvent::Next);
    navigation.dispatch(vpet::InputEvent::Action);
    TEST_ASSERT_EQUAL(vpet::PanelId::Inventory, navigation.panel());
    TEST_ASSERT_EQUAL(1, navigation.panelIndex());

    navigation.setPanelIndex(vpet::Navigation::kInventoryCount - 1);
    navigation.dispatch(vpet::InputEvent::Action);
    TEST_ASSERT_EQUAL(vpet::PanelId::Home, navigation.panel());
}

void test_status_next_cycles_two_pages() {
    vpet::Navigation navigation;
    navigation.setMenuIndex(0);
    navigation.dispatch(vpet::InputEvent::Action);
    TEST_ASSERT_EQUAL(vpet::PanelId::Status, navigation.panel());
    TEST_ASSERT_EQUAL(0, navigation.panelIndex());
    navigation.dispatch(vpet::InputEvent::Next);
    TEST_ASSERT_EQUAL(vpet::PanelId::Status, navigation.panel());
    TEST_ASSERT_EQUAL(1, navigation.panelIndex());
    navigation.dispatch(vpet::InputEvent::Next);
    TEST_ASSERT_EQUAL(0, navigation.panelIndex());
    navigation.dispatch(vpet::InputEvent::Action);
    TEST_ASSERT_EQUAL(vpet::PanelId::Home, navigation.panel());
}
