#pragma once
#include <algorithm>
#include "vpet/PetState.h"

namespace vpet {
namespace cue {
enum class Need : uint8_t { None, Food, Rest, Hurt, Sad, Angry };
enum class Face : uint8_t { Happy, Neutral, Sad, Angry };
struct Cue { Need need; Face face; bool angry; };
inline Cue classify(int hunger,int energy,int mood,bool injured=false,bool tired=false,
                    bool hungerCall=false,bool restCall=false) {
    Need need=injured ? Need::Hurt : hunger<=20 || hungerCall ? Need::Food :
        energy<=20 || tired || restCall ? Need::Rest : Need::None;
    const bool angry=mood<50 && (need==Need::Food || need==Need::Rest);
    const Face face=injured ? Face::Sad : mood<20 || angry ? Face::Angry :
        mood<50 ? Face::Sad : mood<75 ? Face::Neutral : Face::Happy;
    if(need==Need::None && mood<50) need=face==Face::Angry ? Need::Angry : Need::Sad;
    return {need,face,angry};
}
inline Cue forPet(const PetState& pet,bool tired=false) {
    Cue value=classify(pet.hunger(),pet.energy(),pet.happiness(),pet.injured(),tired,
        pet.callReason()==CallReason::Hunger,
        pet.callReason()==CallReason::Strength || pet.callReason()==CallReason::Lights);
    if(pet.species()==SpeciesId::Egg || pet.dead() || pet.cold() || pet.sleep.asleep || pet.exploration.away()) {
        value.need=Need::None; value.angry=false;
    }
    return value;
}
inline const char* facePath(Face face) {
    static const char* const paths[]={"/ui/mood/face_happy.vpa","/ui/mood/face_neutral.vpa",
        "/ui/mood/face_sad.vpa","/ui/mood/face_angry.vpa"};
    return paths[static_cast<uint8_t>(face)];
}
enum class RestKind : uint8_t { None, Energy, Bedtime };
struct RestDetail { RestKind kind; int current,target,bedtime; };
inline RestDetail restDetail(const PetState& pet,bool tired=false,int minute=-1) {
    const int trait=pet.dna()[3]%3;
    RestDetail detail{RestKind::None,pet.energy(),0,pet.sleep.preferred(trait)};
    if(forPet(pet,tired).need!=Need::Rest) return detail;
    const bool scheduled=minute>=0 && minute<1440 && (minute>=detail.bedtime || minute<360);
    detail.kind=scheduled ? RestKind::Bedtime : RestKind::Energy;
    detail.target=30+trait*5;
    return detail;
}
inline int restLabelX(int bubbleX) { return bubbleX>=104 ? bubbleX-102 : bubbleX+34; }
inline const char* bubblePath(Cue value) {
    switch(value.need) {
        case Need::Food: return value.angry ? "/ui/mood/food_angry.vpa" : "/ui/mood/food.vpa";
        case Need::Rest: return value.angry ? "/ui/mood/rest_angry.vpa" : "/ui/mood/rest.vpa";
        case Need::Hurt: return "/ui/mood/hurt.vpa";
        case Need::Sad: return "/ui/mood/sad.vpa";
        case Need::Angry: return "/ui/mood/angry.vpa";
        case Need::None: return nullptr;
    }
    return nullptr;
}
struct Position { int x,y; bool flip; };
inline Position position(int petX,int petY,int facing) {
    const int anchor=petX+(facing<0 ? 22 : 66);
    bool flip=facing<0;
    int x=flip ? anchor-34 : anchor+2;
    if(x<0) { x=anchor+2; flip=false; }
    else if(x>208) { x=anchor-34; flip=true; }
    return {std::max(0,std::min(208,x)),std::max(25,std::min(107,petY-16)),flip};
}
} // namespace cue
} // namespace vpet
