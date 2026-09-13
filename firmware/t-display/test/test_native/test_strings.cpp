#include <unity.h>

#include "vpet/Strings.h"

void test_status_labels_switch_with_language() {
    TEST_ASSERT_EQUAL_STRING("STATUS", vpet::copy::statusTitle(false));
    TEST_ASSERT_EQUAL_STRING("ESTADO", vpet::copy::statusTitle(true));
    TEST_ASSERT_EQUAL_STRING("HP", vpet::copy::hp(false));
    TEST_ASSERT_EQUAL_STRING("PV", vpet::copy::hp(true));
    TEST_ASSERT_EQUAL_STRING("HUN", vpet::copy::hunger(false));
    TEST_ASSERT_EQUAL_STRING("HAM", vpet::copy::hunger(true));
    TEST_ASSERT_EQUAL_STRING("AGE", vpet::copy::age(false));
    TEST_ASSERT_EQUAL_STRING("EDAD", vpet::copy::age(true));
    TEST_ASSERT_EQUAL_STRING("OF", vpet::copy::overfeeds(false));
    TEST_ASSERT_EQUAL_STRING("OF", vpet::copy::overfeeds(true));
    TEST_ASSERT_EQUAL_STRING("WT", vpet::copy::weight(false));
    TEST_ASSERT_EQUAL_STRING("PES", vpet::copy::weight(true));
    TEST_ASSERT_EQUAL_STRING("DP", vpet::copy::dp(false));
    TEST_ASSERT_EQUAL_STRING("DP", vpet::copy::dp(true));
    TEST_ASSERT_EQUAL_STRING("WR", vpet::copy::winRatio(false));
    TEST_ASSERT_EQUAL_STRING("WR", vpet::copy::winRatio(true));
}

void test_options_labels_switch_with_language() {
    TEST_ASSERT_EQUAL_STRING("LANGUAGE", vpet::copy::language(false));
    TEST_ASSERT_EQUAL_STRING("IDIOMA", vpet::copy::language(true));
    TEST_ASSERT_EQUAL_STRING("SAVE", vpet::copy::save(false));
    TEST_ASSERT_EQUAL_STRING("GUARDAR", vpet::copy::save(true));
    TEST_ASSERT_TRUE(vpet::languageIsSpanish("ES"));
    TEST_ASSERT_FALSE(vpet::languageIsSpanish("EN"));
}
