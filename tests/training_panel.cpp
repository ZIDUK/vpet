#include <cassert>
#include <iostream>
#include <LittleFS.h>
#include "vpet/Panels.h"

int main(int argc, char** argv) {
    assert(argc == 4);
    assetRoot = argv[1];
    vpet::PetState pet;
    pet.evolveTo(static_cast<vpet::SpeciesId>(std::stoi(argv[2])));
    const char* language = argv[3];
    TFT_eSPI output;
    TFT_eSprite canvas, reference, scene;
    canvas.setSwapBytes(true);
    reference.setSwapBytes(true);
    scene.setSwapBytes(true);
    vpet::AssetStore assets;
    assert(assets.begin().mounted);
    vpet::Panels panels(output, canvas, assets, &scene);
    vpet::Panels uncached(output, reference, assets);
    vpet::TrainingSession session;
    // Include both Techniques and Back, then revisit stats after cache pressure.
    for (int cursor : {0, 1, 2, 3, 4, 5, 6, 7, 6, 0}) {
        session.cursor = cursor;
        panels.drawTraining(session, pet, 1000, language);
        uncached.drawTraining(session, pet, 1000, language);
        assert(canvas.pixels == reference.pixels);
        panels.drawTraining(session, pet, 1100, language);
        for (uint32_t ms = 1200; ms < 2000; ms += 100) {
            const size_t opens = assetOpens;
            panels.drawTraining(session, pet, ms, language);
            const size_t delta = assetOpens - opens;
            if (delta != 1) std::cerr << "cursor=" << cursor << " opens=" << delta << '\n';
            assert(delta == 1); // Only the animated portrait should read flash.
            uncached.drawTraining(session, pet, ms, language);
            assert(canvas.pixels == reference.pixels);
            // Warm after the deliberately uncached reference draw.
            panels.drawTraining(session, pet, ms, language);
        }
    }
    // Simulate shared framebuffer reuse by Home and other panels.
    panels.invalidate();
    scene.fillSprite(TFT_RED);
    panels.drawTraining(session, pet, 2100, language);
    uncached.drawTraining(session, pet, 2100, language);
    assert(canvas.pixels == reference.pixels);
    vpet::PracticeSession practice;
    practice.page = vpet::PracticeSession::Page::Tech;
    for (int cursor = 0; cursor < 6; ++cursor) {
        practice.cursor = cursor;
        panels.drawPractice(practice, pet, 2200, language);
        uncached.drawPractice(practice, pet, 2200, language);
        assert(canvas.pixels == reference.pixels);
        const auto opens = assetOpens;
        panels.drawPractice(practice, pet, 2300, language);
        assert(assetOpens == opens + 1);
    }
    panels.drawTraining(session, pet, 2400, language);
    uncached.drawTraining(session, pet, 2400, language);
    assert(canvas.pixels == reference.pixels);
    vpet::ExplorationSession exploration;
    panels.drawExploration(exploration, pet, 1791979200, 2500, language);
    panels.drawTraining(session, pet, 2600, language);
    uncached.drawTraining(session, pet, 2600, language);
    assert(canvas.pixels == reference.pixels);
    for (auto state : {vpet::TrainingSession::State::Prepare,
                       vpet::TrainingSession::State::Session,
                       vpet::TrainingSession::State::Select}) {
        session.state = state;
        session.chosenStatValid = true;
        session.chosenStat = vpet::CombatStat::Off;
        panels.drawTraining(session, pet, 2700, language);
        uncached.drawTraining(session, pet, 2700, language);
        assert(canvas.pixels == reference.pixels);
    }
    for (uint8_t stat = 0; stat < vpet::kTrainingStatCount; ++stat) {
        auto resultPet = pet;
        resultPet.setEnergy(80);
        resultPet.setEvAt(vpet::trainingTypeAt(stat).stat, 30);
        session = vpet::TrainingSession{};
        session.state = vpet::TrainingSession::State::Result;
        session.cursor = stat;
        session.chosenStatValid = true;
        session.chosenStat = vpet::trainingTypeAt(stat).stat;
        session.repsCompleted = 1;
        session.captureSnapshot(resultPet);
        session.lastSummary = vpet::trainingApply(resultPet, session.chosenStat, 1);
        session.saving = true;
        std::vector<uint16_t> previous;
        for (bool stats : {false, true, false}) {
            session.resultStats = stats;
            for (uint8_t choice : {0, 1, 2}) {
                session.resultChoice = choice;
                for (uint32_t ms : {10000u, 10150u}) {
                    auto ordinary = session;
                    ordinary.saving = false;
                    panels.drawTraining(session, resultPet, ms, language);
                    uncached.drawTraining(ordinary, resultPet, ms, language);
                    assert(canvas.pixels == reference.pixels);
                }
                if (!previous.empty()) assert(canvas.pixels != previous);
                previous = canvas.pixels;
            }
        }
        panels.invalidate();
        scene.fillSprite(TFT_RED);
        canvas.fillSprite(TFT_RED);
        panels.drawTraining(session, resultPet, 14000, language);
        auto ordinary = session;
        ordinary.saving = false;
        uncached.drawTraining(ordinary, resultPet, 14000, language);
        assert(canvas.pixels == reference.pixels);
        session.saving = false;
        panels.drawTraining(session, resultPet, 14033, language);
        uncached.drawTraining(session, resultPet, 14033, language);
        assert(canvas.pixels == reference.pixels);
    }
    std::cout << "TRAINING_PANEL_OK\n";
}
