#include <unity.h>
#include "vpet/UiCue.h"

void test_ui_cue_priority_and_faces() {
    using namespace vpet::cue;
    TEST_ASSERT_TRUE(classify(0,0,0,true,true).need==Need::Hurt);
    TEST_ASSERT_TRUE(classify(0,0,0,true,true).face==Face::Sad);
    TEST_ASSERT_TRUE(classify(20,0,49).need==Need::Food);
    TEST_ASSERT_TRUE(classify(20,0,49).angry);
    TEST_ASSERT_TRUE(classify(80,80,49).face==Face::Sad);
    TEST_ASSERT_TRUE(classify(80,80,19).face==Face::Angry);
    TEST_ASSERT_TRUE(classify(80,80,50).face==Face::Neutral);
    TEST_ASSERT_TRUE(classify(80,80,75).face==Face::Happy);
}

void test_ui_cues_are_read_only_and_hidden_asleep() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.setHunger(10);
    pet.setHappiness(30);
    const auto mistakes=pet.careMistakes();
    const auto calls=pet.callReason();
    for(int i=0;i<1000;++i) {
        const auto cue=vpet::cue::forPet(pet);
        TEST_ASSERT_TRUE(cue.need==vpet::cue::Need::Food);
        TEST_ASSERT_TRUE(cue.angry);
    }
    TEST_ASSERT_EQUAL(mistakes,pet.careMistakes());
    TEST_ASSERT_TRUE(calls==pet.callReason());
    TEST_ASSERT_EQUAL(10,pet.hunger());
    TEST_ASSERT_EQUAL(30,pet.happiness());
    pet.sleep.asleep=true;
    TEST_ASSERT_TRUE(vpet::cue::forPet(pet).need==vpet::cue::Need::None);
}

void test_ui_bubbles_fit_below_header_at_both_edges() {
    for(int x=0;x<=152;++x) for(int facing : {-1,1}) {
        const auto p=vpet::cue::position(x,43,facing);
        TEST_ASSERT_TRUE(p.x>=0 && p.x+32<=240);
        TEST_ASSERT_TRUE(p.y>=24 && p.y+28<=135);
    }
    const auto right=vpet::cue::position(152,43,1);
    TEST_ASSERT_EQUAL(184,right.x);
    TEST_ASSERT_TRUE(right.flip);
}
