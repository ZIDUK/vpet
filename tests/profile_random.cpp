#include <cassert>
#include "vpet/ProfileRandom.h"
bool entropyEnabled=false,seedFails=false,randomFails=false;
int enables=0,disables=0,seeds=0,generations=0;
int main() {
    vpet::ProfileRandom rng;
    assert(!rng.next().assigned());
    assert(rng.begin() && !entropyEnabled && enables==1 && disables==1);
    const auto first=rng.next();
    assert(first.assigned() && rng.next().petId()!=first.petId());
    assert(rng.begin() && seeds==1);
    randomFails=true; assert(!rng.next().assigned()); randomFails=false;
    vpet::ProfileRandom failed;
    seedFails=true; assert(!failed.begin() && !entropyEnabled && enables==2 && disables==2);
    assert(!failed.next().assigned());
}
