#include <unity.h>

#include "vpet/Input.h"

using vpet::ButtonSample;
using vpet::Input;
using vpet::InputEvent;

void test_feed_updates_stats_once_when_animation_completes();
void test_training_updates_effort_once();
void test_new_pet_starts_as_egg_and_baby_cannot_attack();
void test_persisted_species_values_remain_compatible();
void test_dragfiremon_moves_with_fly_state();
void test_action_animation_returns_to_idle();
void test_sleep_loops_until_explicit_wake();
void test_sparkmon_evolution_uses_sixteen_frames();
void test_menu_opens_expected_panels();
void test_next_moves_options_cursor();
void test_options_next_wraps_like_header_menu();
void test_back_in_options_is_ignored();
void test_force_next_form_walks_the_line();
void test_hidden_branch_does_not_reveal_identity();
void test_held_next_does_not_auto_advance();
void test_back_returns_from_detail_to_same_tree_node();
void test_missing_save_keeps_current_species_discovered();
void test_settings_persist_bluetooth_preference();
void test_first_advertise_configures_payload_later_restarts_only();

void test_short_next_press() {
    Input input(25, 2000);
    TEST_ASSERT_EQUAL(InputEvent::Next, input.poll({true, false}, 100));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 130));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 160));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({false, false}, 180));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({false, false}, 210));
}

void test_deliberate_next_press_under_two_seconds_stays_next() {
    Input input(25, 2000);
    TEST_ASSERT_EQUAL(InputEvent::Next, input.poll({true, false}, 100));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 1600));
    input.poll({false, false}, 1600);
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({false, false}, 1630));
}

void test_held_next_does_not_auto_advance() {
    Input input(25, 2000);
    TEST_ASSERT_EQUAL(InputEvent::Next, input.poll({true, false}, 100));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 349));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 350));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 490));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 1600));
}

void test_long_next_press_becomes_back() {
    Input input(25, 2000);
    TEST_ASSERT_EQUAL(InputEvent::Next, input.poll({true, false}, 100));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 2099));
    TEST_ASSERT_EQUAL(InputEvent::Back, input.poll({true, false}, 2100));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 2200));
    input.poll({false, false}, 2230);
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({false, false}, 2260));
}

void test_action_has_no_long_press_mapping() {
    Input input(25, 700);
    TEST_ASSERT_EQUAL(InputEvent::Action, input.poll({false, true}, 100));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({false, true}, 1000));
    input.poll({false, false}, 1000);
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({false, false}, 1030));
}

void test_noisy_next_press_is_emitted_once() {
    Input input(25, 2000);
    TEST_ASSERT_EQUAL(InputEvent::Next, input.poll({true, false}, 100));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({false, false}, 105));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 110));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({true, false}, 160));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({false, false}, 190));
    TEST_ASSERT_EQUAL(InputEvent::None, input.poll({false, false}, 220));
    TEST_ASSERT_EQUAL(InputEvent::Next, input.poll({true, false}, 230));
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_short_next_press);
    RUN_TEST(test_deliberate_next_press_under_two_seconds_stays_next);
    RUN_TEST(test_held_next_does_not_auto_advance);
    RUN_TEST(test_long_next_press_becomes_back);
    RUN_TEST(test_action_has_no_long_press_mapping);
    RUN_TEST(test_noisy_next_press_is_emitted_once);
    RUN_TEST(test_feed_updates_stats_once_when_animation_completes);
    RUN_TEST(test_training_updates_effort_once);
    RUN_TEST(test_new_pet_starts_as_egg_and_baby_cannot_attack);
    RUN_TEST(test_persisted_species_values_remain_compatible);
    RUN_TEST(test_dragfiremon_moves_with_fly_state);
    RUN_TEST(test_action_animation_returns_to_idle);
    RUN_TEST(test_sleep_loops_until_explicit_wake);
    RUN_TEST(test_sparkmon_evolution_uses_sixteen_frames);
    RUN_TEST(test_menu_opens_expected_panels);
    RUN_TEST(test_next_moves_options_cursor);
    RUN_TEST(test_options_next_wraps_like_header_menu);
    RUN_TEST(test_back_in_options_is_ignored);
    RUN_TEST(test_force_next_form_walks_the_line);
    RUN_TEST(test_hidden_branch_does_not_reveal_identity);
    RUN_TEST(test_back_returns_from_detail_to_same_tree_node);
    RUN_TEST(test_missing_save_keeps_current_species_discovered);
    RUN_TEST(test_settings_persist_bluetooth_preference);
    RUN_TEST(test_first_advertise_configures_payload_later_restarts_only);
    return UNITY_END();
}
