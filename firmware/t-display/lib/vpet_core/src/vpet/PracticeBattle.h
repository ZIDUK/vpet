#pragma once

#include <stdint.h>

namespace vpet {
namespace practice {
struct Fighter {
    int stats[6] = {25, 20, 24, 20, 22, 20};
    int hp = 90, mp = 30, maxHp = 90, maxMp = 30;
    int mastery[3] = {0, 0, 0};
    int cooldown[3] = {0, 0, 0};
    uint8_t equipped = 7;
    int personality = 1, bond = 50;

    void init(const int* values) {
        for (int i = 0; i < 6; ++i) stats[i] = values[i] < 1 ? 1 : (values[i] > 99 ? 99 : values[i]);
        hp = maxHp = 40 + stats[0] * 2;
        mp = maxMp = 10 + stats[1];
        for (int i = 0; i < 3; ++i) cooldown[i] = 0;
    }
    bool valid(int action) const {
        return action >= 0 && action < 3 && (equipped & (1 << action)) &&
               cooldown[action] == 0 && mp >= (action == 1 ? 8 : 0);
    }
};

inline int choose(const Fighter& f, int order = -1) {
    int best = 2, bestScore = -1;
    for (int i = 0; i < 3; ++i) {
        if (!f.valid(i)) continue;
        int score;
        if (i == 2) {
            score = 5 + (f.hp * 3 < f.maxHp ? 35 : 0) + (f.mp < 8 ? 25 : 0) +
                    (f.personality == 1 ? 15 : 0);
        } else {
            score = (i == 0 ? 12 : 24) + f.mastery[i] / 20 +
                    (f.personality == 0 ? 12 : 0) +
                    (f.personality == 2 && i == 1 ? 12 : 0) + (i == 1 ? f.stats[5] / 10 : 0);
        }
        if (order == i) score += 10 + f.bond / 2;
        if (score > bestScore) { bestScore = score; best = i; }
    }
    return best;
}

struct Battle {
    Fighter player, rival;
    int round = 0;
    int result = 0; // 0 active, 1 victory, 2 defeat, 3 draw
    int actions[2] = {-1, -1};
    int damage[2] = {0, 0};
    int uses[3] = {0, 0, 0};

    bool step(int order = -1) {
        if (result || (order != -1 && (order < 0 || order > 2 || !(player.equipped & (1 << order))))) return false;
        const int selected[] = {choose(player, order), choose(rival)};
        Fighter* fighters[] = {&player, &rival};
        ++round;
        for (int i = 0; i < 2; ++i) {
            actions[i] = -1;
            damage[i] = 0;
            for (int j = 0; j < 3; ++j) if (fighters[i]->cooldown[j] > 0) --fighters[i]->cooldown[j];
            if (selected[i] == 2) {
                fighters[i]->mp += 4;
                if (fighters[i]->mp > fighters[i]->maxMp) fighters[i]->mp = fighters[i]->maxMp;
            }
        }
        int first = player.stats[4] > rival.stats[4] ||
                    (player.stats[4] == rival.stats[4] && round % 2 == 1) ? 0 : 1;
        for (int n = 0; n < 2; ++n) {
            const int i = n == 0 ? first : 1 - first;
            Fighter& source = *fighters[i];
            Fighter& target = *fighters[1 - i];
            if (source.hp <= 0) continue;
            const int action = selected[i];
            actions[i] = action;
            if (i == 0) ++uses[action];
            source.mp -= action == 1 ? 8 : 0;
            source.cooldown[action] = action == 1 ? 1 : 0;
            if (action == 2) continue;
            int amount = (action == 0 ? 12 : 24) + source.stats[2] / 3 + source.mastery[action] / 20 - target.stats[3] / 4;
            if (amount < 1) amount = 1;
            if (selected[1 - i] == 2) amount /= 2;
            if (amount < 1) amount = 1;
            damage[i] = amount > target.hp ? target.hp : amount;
            target.hp -= damage[i];
        }
        if (rival.hp == 0) result = 1;
        else if (player.hp == 0) result = 2;
        else if (round >= 30) result = 3;
        return true;
    }
};
} // namespace practice
} // namespace vpet
