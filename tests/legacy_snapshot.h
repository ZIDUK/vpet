#pragma once

#include <cassert>
#include <sstream>
#include <string>
#include <vector>

// Historical wire layouts, including the absence of the survival extension.
inline std::string legacySnapshot(const std::string& current, int version) {
    assert(version >= 1 && version <= 6);
    std::istringstream input(current);
    std::string line;
    assert(std::getline(input, line) && line == "6");
    std::string result = std::to_string(version) + '\n';
    while (std::getline(input, line) && line != "ES" && line != "EN") {
        const auto key = line.substr(0, line.find(' '));
        if (version < 6 && (key == "hunCritMs" || key == "eneCritMs" || key == "dna4")) continue;
        if (version < 3 && (key == "techM3" || key == "techM4")) continue;
        result += line + '\n';
    }
    assert(line == "ES" || line == "EN");
    result += line + '\n';
    std::vector<std::string> tail;
    while (std::getline(input, line)) tail.push_back(line);
    assert(tail.size() == 5 && tail.back() == "END");
    result += tail[0] + '\n';  // Shared adopted inventory.
    if (version >= 2) result += tail[1] + '\n';
    if (version >= 4) result += tail[2] + '\n';
    if (version >= 5) result += tail[3] + '\n';
    return result + "END\n";
}
