#include <unity.h>

#include "vpet/Input.h"

using vpet::ButtonSample;
using vpet::Input;
using vpet::InputEvent;

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
    return UNITY_END();
}
