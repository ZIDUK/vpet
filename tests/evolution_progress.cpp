#include <cassert>
#include <cstdio>
#include <LittleFS.h>
#include "vpet/EvolutionProgress.h"
#include "vpet/Panels.h"

int main(int argc, char** argv) {
    assert(argc == 10);
    assetRoot = argv[1];
    const auto species = static_cast<vpet::SpeciesId>(atoi(argv[2]));
    const uint8_t selected = atoi(argv[3]);
    const uint8_t page = atoi(argv[4]);
    const bool spanish = std::string(argv[5]) == "ES";
    const bool met = atoi(argv[6]);
    vpet::PetState pet;
    pet.restore(species, met ? 80 : 40, 70, 60, 0, 90, 0);
    pet.setStageAgeSeconds(atoi(argv[7]));
    pet.setWeight(atoi(argv[8]));
    pet.setBattles(met ? 15 : 14);
    pet.setWins(met ? 9 : 8);
    pet.setLosses(met ? 6 : 7);
    pet.setCareMistakes(met ? 1 : 2);
    const auto before = pet.snapshot();
    const auto data = vpet::evolution_progress::forPet(pet, selected);
    assert(data.pages() <= 3);
    if (std::string(argv[9]) == "model") {
        printf("%u %u %u\n", static_cast<unsigned>(data.state), data.count, data.pages());
        for (uint8_t i = 0; i < data.count; ++i) {
            const auto& r = data.rows[i];
            printf("%u %u %u %u %u %u\n", static_cast<unsigned>(r.kind), r.current,
                   r.target, r.upper, r.remaining, r.met);
        }
        return 0;
    }
    TFT_eSPI display;
    TFT_eSprite canvas;
    canvas.setSwapBytes(true);
    vpet::AssetStore assets;
    assert(assets.begin().mounted);
    vpet::Panels panels(display, canvas, assets);
    vpet::Navigation nav;
    nav.setMenuIndex(7);
    nav.setCurrentSpecies(species);
    nav.setPanel(vpet::PanelId::EvolutionDetail, selected);
    nav.setEvolutionDetailPage(page);
    vpet::DateTimeMenu clock;
    panels.draw(nav, pet, vpet::BleStatus::Off, clock, spanish ? "ES" : "EN", false);
    const auto after = pet.snapshot();
    assert(memcmp(&before, &after, sizeof(before)) == 0);
    printf("P6\n240 135\n255\n");
    for (int y = 0; y < 135; ++y) for (int x = 0; x < 240; ++x) {
        const uint16_t pixel = canvas.readPixel(x, y);
        const unsigned char rgb[] = {static_cast<unsigned char>(((pixel >> 11) & 31) * 255 / 31),
            static_cast<unsigned char>(((pixel >> 5) & 63) * 255 / 63), static_cast<unsigned char>((pixel & 31) * 255 / 31)};
        fwrite(rgb, 1, 3, stdout);
    }
}
