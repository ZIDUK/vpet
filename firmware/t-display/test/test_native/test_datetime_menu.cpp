#include <unity.h>

#include "vpet/DateTimeMenu.h"

void test_date_year_minus_steps_down() {
    const int start[] = {2026, 9, 10, 21, 0};
    vpet::DateTimeMenu menu;
    menu.begin(true, start);
    menu.next();
    TEST_ASSERT_EQUAL(vpet::DateTimeAction::None, menu.activate());
    TEST_ASSERT_EQUAL(2025, menu.values()[0]);
}

void test_date_year_plus_wraps_from_max() {
    const int start[] = {2099, 1, 1, 0, 0};
    vpet::DateTimeMenu menu;
    menu.begin(true, start);
    TEST_ASSERT_EQUAL(vpet::DateTimeAction::None, menu.activate());
    TEST_ASSERT_EQUAL(2024, menu.values()[0]);
}

void test_date_year_minus_wraps_from_min() {
    const int start[] = {2024, 1, 1, 0, 0};
    vpet::DateTimeMenu menu;
    menu.begin(true, start);
    menu.next();
    TEST_ASSERT_EQUAL(vpet::DateTimeAction::None, menu.activate());
    TEST_ASSERT_EQUAL(2099, menu.values()[0]);
}

void test_date_next_wraps_like_options() {
    const int start[] = {2026, 1, 1, 0, 0};
    vpet::DateTimeMenu menu;
    menu.begin(true, start);
    TEST_ASSERT_EQUAL(8, menu.count());
    for (uint8_t i = 0; i < 7; ++i) menu.next();
    TEST_ASSERT_EQUAL(7, menu.cursor());
    menu.next();
    TEST_ASSERT_EQUAL(0, menu.cursor());
}

void test_date_save_and_back_rows() {
    const int start[] = {2026, 1, 1, 0, 0};
    vpet::DateTimeMenu menu;
    menu.begin(true, start);
    for (uint8_t i = 0; i < 6; ++i) menu.next();
    TEST_ASSERT_EQUAL(vpet::DateTimeAction::Saved, menu.activate());
    menu.next();
    TEST_ASSERT_EQUAL(vpet::DateTimeAction::Cancelled, menu.activate());
}

void test_time_hour_minus_wraps_to_23() {
    const int start[] = {2026, 1, 1, 0, 30};
    vpet::DateTimeMenu menu;
    menu.begin(false, start);
    TEST_ASSERT_EQUAL(6, menu.count());
    menu.next();
    TEST_ASSERT_EQUAL(vpet::DateTimeAction::None, menu.activate());
    TEST_ASSERT_EQUAL(23, menu.values()[3]);
}

void test_status_clock_uses_saved_date_and_time() {
    const int values[] = {2026, 9, 10, 21, 4};
    char line[20] = {};
    vpet::DateTimeMenu::writeClock(values, line, sizeof(line));
    TEST_ASSERT_EQUAL_STRING("2026/09/10 21:04", line);
}

void test_date_labels_use_spanish() {
    const int start[] = {2026, 1, 1, 0, 0};
    vpet::DateTimeMenu menu;
    menu.begin(true, start, true);
    for (uint8_t i = 0; i < 6; ++i) menu.next();
    char label[20] = {};
    menu.writeLabel(6, label, sizeof(label));
    TEST_ASSERT_EQUAL_STRING("GUARDAR", label);
}
