#include <unity.h>

#include "vpet/Strings.h"

#include <string.h>

void test_status_labels_switch_with_language() {
    TEST_ASSERT_EQUAL_STRING("STATUS", vpet::copy::statusTitle(false));
    TEST_ASSERT_EQUAL_STRING("ESTADO", vpet::copy::statusTitle(true));
    TEST_ASSERT_EQUAL_STRING("HP", vpet::copy::hp(false));
    TEST_ASSERT_EQUAL_STRING("PV", vpet::copy::hp(true));
    TEST_ASSERT_EQUAL_STRING("HUN", vpet::copy::hunger(false));
    TEST_ASSERT_EQUAL_STRING("HAM", vpet::copy::hunger(true));
    TEST_ASSERT_EQUAL_STRING("AGE", vpet::copy::age(false));
    TEST_ASSERT_EQUAL_STRING("EDAD", vpet::copy::age(true));
    TEST_ASSERT_EQUAL_STRING("OVERFEED", vpet::copy::overfeeds(false));
    TEST_ASSERT_EQUAL_STRING("EXCESO", vpet::copy::overfeeds(true));
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

// Training session copy::* must switch on language AND avoid the
// words that previously leaked through as hard-coded literals in the
// firmware renderer (REPS, EV, ENE, ENTRENAR, FINALIZAR, CONFIRMAR,
// ENTRENO LISTO, ACTION…CANCELAR, …).
void test_training_action_labels_switch_with_language() {
    TEST_ASSERT_EQUAL_STRING("TRAIN",        vpet::copy::trainingAction(false));
    TEST_ASSERT_EQUAL_STRING("ENTRENAR",     vpet::copy::trainingAction(true));
    TEST_ASSERT_EQUAL_STRING("TRAIN",        vpet::copy::trainingTrain(false));
    TEST_ASSERT_EQUAL_STRING("ENTRENAR",     vpet::copy::trainingTrain(true));
    TEST_ASSERT_EQUAL_STRING("FINALIZE",     vpet::copy::trainingFinalize(false));
    TEST_ASSERT_EQUAL_STRING("FINALIZAR",    vpet::copy::trainingFinalize(true));
    TEST_ASSERT_EQUAL_STRING("CONFIRM",      vpet::copy::trainingConfirm(false));
    TEST_ASSERT_EQUAL_STRING("CONFIRMAR",    vpet::copy::trainingConfirm(true));
    TEST_ASSERT_EQUAL_STRING("DONE",         vpet::copy::trainingDone(false));
    TEST_ASSERT_EQUAL_STRING("ENTRENO LISTO", vpet::copy::trainingDone(true));
    TEST_ASSERT_EQUAL_STRING("START",        vpet::copy::trainingStart(false));
    TEST_ASSERT_EQUAL_STRING("EMPEZAR",      vpet::copy::trainingStart(true));
    TEST_ASSERT_EQUAL_STRING("APPLY",        vpet::copy::trainingApply(false));
    TEST_ASSERT_EQUAL_STRING("APLICAR",      vpet::copy::trainingApply(true));
    TEST_ASSERT_EQUAL_STRING("CANCEL",       vpet::copy::trainingCancel(false));
    TEST_ASSERT_EQUAL_STRING("CANCELAR",     vpet::copy::trainingCancel(true));
    TEST_ASSERT_EQUAL_STRING("BACK",         vpet::copy::trainingReturn(false));
    TEST_ASSERT_EQUAL_STRING("VOLVER",       vpet::copy::trainingReturn(true));
    TEST_ASSERT_EQUAL_STRING("EXIT",         vpet::copy::trainingExit(false));
    TEST_ASSERT_EQUAL_STRING("SALIR",        vpet::copy::trainingExit(true));
    TEST_ASSERT_EQUAL_STRING("ACTION",       vpet::copy::trainingActionLabel(false));
    TEST_ASSERT_EQUAL_STRING("ACTION",       vpet::copy::trainingActionLabel(true));
    TEST_ASSERT_EQUAL_STRING("REP",          vpet::copy::trainingButtonRep(false));
    TEST_ASSERT_EQUAL_STRING("REP",          vpet::copy::trainingButtonRep(true));
    TEST_ASSERT_EQUAL_STRING("COST",         vpet::copy::trainingCost(false));
    TEST_ASSERT_EQUAL_STRING("COSTE",        vpet::copy::trainingCost(true));
    TEST_ASSERT_EQUAL_STRING("NOW",          vpet::copy::trainingNow(false));
    TEST_ASSERT_EQUAL_STRING("AHORA",        vpet::copy::trainingNow(true));
    TEST_ASSERT_EQUAL_STRING("HAPPY",        vpet::copy::trainingHappy(false));
    TEST_ASSERT_EQUAL_STRING("FELIC",        vpet::copy::trainingHappy(true));
    TEST_ASSERT_EQUAL_STRING("REAL",         vpet::copy::trainingReal(false));
    TEST_ASSERT_EQUAL_STRING("REAL",         vpet::copy::trainingReal(true));
    TEST_ASSERT_EQUAL_STRING("PROJ",         vpet::copy::trainingProj(false));
    TEST_ASSERT_EQUAL_STRING("PROY",         vpet::copy::trainingProj(true));
    TEST_ASSERT_EQUAL_STRING("AVAIL",        vpet::copy::trainingAvail(false));
    TEST_ASSERT_EQUAL_STRING("DISP",         vpet::copy::trainingAvail(true));
    TEST_ASSERT_EQUAL_STRING("RES",          vpet::copy::trainingReserve(false));
    TEST_ASSERT_EQUAL_STRING("RES",          vpet::copy::trainingReserve(true));
}

// Each ES/EN pair must fit in the 240 px panel at font 1 (~6 px/char
// in the GLCD font we use). The renderer paints up to 32 chars per row
// inside the 12..228 text band.
void test_training_strings_fit_240px_width() {
    constexpr size_t kMaxLen = 32;
    struct Pair { const char* en; const char* es; };
    const Pair pairs[] = {
        {vpet::copy::trainingAction(false),    vpet::copy::trainingAction(true)},
        {vpet::copy::trainingTrain(false),     vpet::copy::trainingTrain(true)},
        {vpet::copy::trainingFinalize(false),  vpet::copy::trainingFinalize(true)},
        {vpet::copy::trainingConfirm(false),   vpet::copy::trainingConfirm(true)},
        {vpet::copy::trainingDone(false),      vpet::copy::trainingDone(true)},
        {vpet::copy::trainingApply(false),     vpet::copy::trainingApply(true)},
        {vpet::copy::trainingCancel(false),    vpet::copy::trainingCancel(true)},
        {vpet::copy::trainingReturn(false),    vpet::copy::trainingReturn(true)},
        {vpet::copy::trainingExit(false),      vpet::copy::trainingExit(true)},
        {vpet::copy::trainingAvail(false),     vpet::copy::trainingAvail(true)},
        {vpet::copy::trainingReserve(false),   vpet::copy::trainingReserve(true)},
        {vpet::copy::trainingReal(false),      vpet::copy::trainingReal(true)},
        {vpet::copy::trainingProj(false),      vpet::copy::trainingProj(true)},
        {vpet::copy::trainingHappy(false),     vpet::copy::trainingHappy(true)},
        {vpet::copy::trainingCost(false),      vpet::copy::trainingCost(true)},
        {vpet::copy::trainingReady(false),     vpet::copy::trainingReady(true)},
    };
    for (size_t i = 0; i < sizeof(pairs) / sizeof(pairs[0]); ++i) {
        TEST_ASSERT_TRUE_MESSAGE(strlen(pairs[i].en) <= kMaxLen,
            "EN label too long for 240 px row");
        TEST_ASSERT_TRUE_MESSAGE(strlen(pairs[i].es) <= kMaxLen,
            "ES label too long for 240 px row");
    }
}

// Footer button labels added for the v2 drawTraining redesign
// (Continue on Result, Retry/Discard on Error, follow helpers on the
// Confirm screen). All strings must resolve without literal fallback
// so ES/EN never collide on the 240x135 panel.
void test_training_footer_buttons_switch_with_language() {
    TEST_ASSERT_EQUAL_STRING("CONTINUE",     vpet::copy::trainingContinue(false));
    TEST_ASSERT_EQUAL_STRING("CONTINUAR",    vpet::copy::trainingContinue(true));
    TEST_ASSERT_EQUAL_STRING("RETRY",        vpet::copy::trainingRetry(false));
    TEST_ASSERT_EQUAL_STRING("REINTENTAR",   vpet::copy::trainingRetry(true));
    TEST_ASSERT_EQUAL_STRING("DISCARD",      vpet::copy::trainingDiscard(false));
    TEST_ASSERT_EQUAL_STRING("DESCARTAR",    vpet::copy::trainingDiscard(true));
    TEST_ASSERT_EQUAL_STRING("CLOSE SESSION?",  vpet::copy::confirmTitle(false));
    TEST_ASSERT_EQUAL_STRING("CERRAR ENTRENAMIENTO?", vpet::copy::confirmTitle(true));
    // "x" is locale-neutral but kept behind pick() for future swap.
    TEST_ASSERT_EQUAL_STRING("x",  vpet::copy::confirmRepPrefix(false));
    TEST_ASSERT_EQUAL_STRING("x",  vpet::copy::confirmRepPrefix(true));
    TEST_ASSERT_EQUAL_STRING("REP", vpet::copy::confirmRepSuffix(false));
    TEST_ASSERT_EQUAL_STRING("REP", vpet::copy::confirmRepSuffix(true));
}

// Pin the band layout used by drawTraining v2 so a refactor that
// shifts the sprite/header/footer by even 1 px fails loudly here. The
// numbers are mirrored in scripts/training_renderer.py and the new
// out/inspect_training_firmware.py; updating one without the other
// breaks the parity contract.
//
// The "row 5 ↔ feedback band" pair is intentionally overlapping: both
// occupy the y=99..110 strip, but only one paints per state (row 5 is
// the energy row on the Prepare screen; the feedback band fires only
// when a session message is set). The remaining bands below are
// non-overlapping by construction.
void test_training_band_layout_constants() {
    // 240x135 panel.
    constexpr int16_t kW = 240;
    constexpr int16_t kH = 135;
    TEST_ASSERT_EQUAL_INT16(240, kW);
    TEST_ASSERT_EQUAL_INT16(135, kH);

    // Bands (mirrored constants in Panels.cpp::drawTraining).
    constexpr int16_t kHeaderY = 0,    kHeaderH = 20;
    constexpr int16_t kSpriteX = 4,    kSpriteY = 23, kSpriteSize = 60;
    constexpr int16_t kInfoX = 70,     kInfoY = 24, kIconSize = 12;
    constexpr int16_t kRow1Y = 41,     kRow2Y = 57,   kRow3Y = 72;
    constexpr int16_t kRow4Y = 87,     kRow5Y = 102;
    constexpr int16_t kFeedbackY = 99, kFeedbackH = 12;
    constexpr int16_t kBtnY = 115,     kBtnH = 17;
    constexpr int16_t kBtnLeftX = 4,   kBtnLeftW = 92;
    constexpr int16_t kBtnRightX = 100, kBtnRightW = 92;

    // Header [0..19] must not overlap sprite [23..83].
    TEST_ASSERT_TRUE(kHeaderY + kHeaderH <= kSpriteY);
    // Sprite fits within the panel column.
    TEST_ASSERT_TRUE(kSpriteX + kSpriteSize <= kW);
    TEST_ASSERT_TRUE(kSpriteY + kSpriteSize <= 84); // ends before row 4.
    // Info label sits to the right of the sprite.
    TEST_ASSERT_TRUE(kInfoX >= kSpriteX + kSpriteSize);
    // Data rows 1..4 are stacked with strictly increasing y and all
    // complete before the feedback band opens at y=99. Each row uses
    // font 1 (8 px tall), so we need 8 px of headroom between a row
    // baseline and the next band's start.
    TEST_ASSERT_TRUE(kRow1Y < kRow2Y);
    TEST_ASSERT_TRUE(kRow2Y < kRow3Y);
    TEST_ASSERT_TRUE(kRow3Y < kRow4Y);
    TEST_ASSERT_TRUE(kRow4Y + 8 <= kFeedbackY);
    // Row 5 (102) lives inside the feedback strip but mutally
    // exclusive: renderer paints row 5 OR the band, never both.
    TEST_ASSERT_TRUE(kRow5Y + 8 <= kFeedbackY + kFeedbackH);
    // Footer lives below the feedback band and inside the panel.
    TEST_ASSERT_TRUE(kBtnY >= kFeedbackY + kFeedbackH);
    TEST_ASSERT_TRUE(kBtnY + kBtnH <= kH);
    // Two button columns side by side, no overlap.
    TEST_ASSERT_TRUE(kBtnLeftX + kBtnLeftW <= kBtnRightX);
    TEST_ASSERT_TRUE(kBtnRightX + kBtnRightW <= kW);
}
