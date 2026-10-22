#include <iostream>
#include "vpet/UiCue.h"
int main() {
    int trait,energy,minute,bedtime,tired,hidden,x;
    while(std::cin>>trait>>energy>>minute>>bedtime>>tired>>hidden>>x) {
        vpet::PetState pet; pet.evolveTo(vpet::SpeciesId::Rookie);
        const uint8_t dna[]={1,2,3,static_cast<uint8_t>(trait)};
        pet.restoreDna(dna); pet.setHunger(hidden==4 ? 0 : 80); pet.setEnergy(energy);
        pet.sleep.bedtime=bedtime;
        if(hidden==1) pet.sleep.asleep=true;
        if(hidden==2) pet.setCold(true);
        if(hidden==3) pet.restoreInjury(true,1,false);
        if(hidden==5) pet.resetToEgg();
        const auto detail=vpet::cue::restDetail(pet,tired,minute);
        std::cout<<int(detail.kind)<<' '<<detail.current<<' '<<detail.target<<' '
                 <<detail.bedtime<<' '<<vpet::cue::restLabelX(x)<<'\n';
    }
}
