#pragma once
#include <stdint.h>
#include <string.h>
#include "vpet/PetState.h"

namespace vpet { namespace content {
enum class Action : uint8_t { Idle, Walk, Eat, Punch, Cast, Sleep, Evolution, Hatch,
    Hit, Hurt, Dodge, Block, Happy, Sad, Tired, Angry, HitReact, Count };
enum class Context : uint8_t { Home, Training, Battle, Exploration };
struct Clip {
    const char* path;
    uint16_t frames, intervalMs, loopStart, loopEnd, canvas;
};
struct Stage {
    const char* name;
    const char* shortName;
    const char* battleName;
    const char* portrait;
    const Clip* contexts[4];
    const uint16_t* motionFrames;
    const uint16_t* motionIntervals;
};
struct PetDefinition {
    const char* id;
    const char* version;
    const char* background;
    const char* nightBackground;
    const Stage* stages;
    const Stage& stage(SpeciesId role) const {
        const auto i = static_cast<uint8_t>(role);
        return stages[i < 5 ? i : 3];
    }
    const Clip& clip(SpeciesId role, Action action, Context context = Context::Home) const {
        const auto a = static_cast<uint8_t>(action), c = static_cast<uint8_t>(context);
        return stage(role).contexts[c < 4 ? c : 0][a < static_cast<uint8_t>(Action::Count) ? a : 0];
    }
};
inline Action actionFor(const char* name) {
    static const char* const names[] = {"idle","walk","eat","punch","cast","sleep","evolution","hatch",
        "hit","hurt","dodge","block","happy","sad","tired","angry","hit_react"};
    for (uint8_t i = 0; i < static_cast<uint8_t>(Action::Count); ++i)
        if (name && strcmp(name, names[i]) == 0) return static_cast<Action>(i);
    return Action::Idle;
}
} }

#include "vpet/BuiltinPet.generated.h"
