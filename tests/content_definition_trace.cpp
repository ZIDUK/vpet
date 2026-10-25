#include <cstdio>
#include <cstdlib>
#include <cassert>
#include "vpet/PetDefinition.h"
#include "vpet/Motion.h"
#include "OtherPet.h"

int main(int argc, char** argv) {
    using namespace vpet;
    const auto& definition = argc > 1 && std::atoi(argv[1]) ? content::otherDefinition() : content::builtinDefinition();
    for (int role = 0; role < 5; ++role) for (int context = 0; context < 4; ++context)
        for (int action = 0; action < static_cast<int>(content::Action::Count); ++action) {
            const auto& clip = definition.clip(static_cast<SpeciesId>(role), static_cast<content::Action>(action), static_cast<content::Context>(context));
            std::printf("%s %u %u %u %u %u\n", clip.path, clip.frames, clip.intervalMs, clip.loopStart, clip.loopEnd, clip.canvas);
        }
    Motion motion(240, 135, 24, 88, definition);
    motion.setSpecies(SpeciesId::Rookie);
    motion.alignClock(0);
    motion.setTired(true, 0);
    const auto& idle = definition.clip(SpeciesId::Rookie, content::Action::Idle);
    motion.tick(idle.intervalMs * (idle.frames + 2));
    assert(motion.frame() == 2);
    motion.startAction(Action::Rest, 0);
    const auto& sleep = definition.clip(SpeciesId::Rookie, content::Action::Sleep);
    motion.tick(sleep.intervalMs * 30);
    assert(motion.frame() >= sleep.loopStart && motion.frame() <= sleep.loopEnd);
}
