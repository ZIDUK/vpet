#include <unity.h>

#include "vpet/Input.h"

using vpet::ButtonSample;
using vpet::Input;
using vpet::InputEvent;

void test_feed_updates_stats_once_when_animation_completes();
void test_training_updates_effort_once();
void test_dragfiremon_moves_with_fly_state();
void test_action_animation_returns_to_idle();
void test_menu_opens_expected_panels();
void test_hidden_branch_does_not_reveal_identity();
void test_back_returns_from_detail_to_same_tree_node();
void test_missing_save_keeps_current_species_discovered();
void test_credentials_are_saved_only_after_internet_capable_connection();
void test_password_editor_cycles_groups_and_submits_masked_value();

void test_short_next_press() {
    Input input(25, 700);
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 100));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 130));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({false, false}, 180));
    TEST_ASSERT_EQUAL(InputEvent::Next, input.poll({false, false}, 210));
}

void test_long_next_press_becomes_back() {
    Input input(25, 700);
    input.poll({true, false}, 100);
    input.poll({true, false}, 130);
    input.poll({false, false}, 900);
    TEST_ASSERT_EQUAL(InputEvent::Back, input.poll({false, false}, 930));
}

void test_action_has_no_long_press_mapping() {
    Input input(25, 700);
    input.poll({false, true}, 100);
    input.poll({false, true}, 130);
    input.poll({false, false}, 1000);
    TEST_ASSERT_EQUAL(InputEvent::Action, input.poll({false, false}, 1030));
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_short_next_press);
    RUN_TEST(test_long_next_press_becomes_back);
    RUN_TEST(test_action_has_no_long_press_mapping);
    RUN_TEST(test_feed_updates_stats_once_when_animation_completes);
    RUN_TEST(test_training_updates_effort_once);
    RUN_TEST(test_dragfiremon_moves_with_fly_state);
    RUN_TEST(test_action_animation_returns_to_idle);
    RUN_TEST(test_menu_opens_expected_panels);
    RUN_TEST(test_hidden_branch_does_not_reveal_identity);
    RUN_TEST(test_back_returns_from_detail_to_same_tree_node);
    RUN_TEST(test_missing_save_keeps_current_species_discovered);
    RUN_TEST(test_credentials_are_saved_only_after_internet_capable_connection);
    RUN_TEST(test_password_editor_cycles_groups_and_submits_masked_value);
    return UNITY_END();
}
