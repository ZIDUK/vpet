#pragma once
#include "vpet/PetDefinition.h"

#include <stdio.h>
#include "generated/TrainingArtwork.h"
#include "vpet/EvolutionProgress.h"

namespace vpet { namespace evolution_ui {
constexpr uint16_t rgb(int r, int g, int b) { return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3); }
constexpr uint16_t ink = rgb(19,23,27), white = rgb(242,244,238);
constexpr uint16_t muted = rgb(162,181,182), yellow = rgb(255,220,70);
constexpr uint16_t green = rgb(111,208,164), line = rgb(40,74,75);

inline const char* label(evolution_progress::Kind kind, bool es) {
    static const char* const labels[][2] = {
        {"TIME LEFT", "TIEMPO"}, {"CARE ERRORS", "ERRORES"}, {"BATTLES", "COMBATES"},
        {"WIN RATE", "VICTORIAS"}, {"FOOD", "COMIDA"}, {"ENERGY", "ENERGIA"},
        {"MOOD", "ANIMO"}, {"HEALTH", "SALUD"}, {"WEIGHT", "PESO"},
    };
    return labels[static_cast<uint8_t>(kind)][es ? 1 : 0];
}
inline void rowValue(const evolution_progress::Row& r, bool es, char* out, size_t size) {
    using Kind = evolution_progress::Kind;
    if (r.kind == Kind::Time) {
        if (r.met) snprintf(out, size, "%s", es ? "CUMPLIDO" : "MET");
        else if (r.remaining < 60) snprintf(out, size, "<1m");
        else {
            const uint32_t minutes = (r.remaining + 59) / 60;
            if (minutes < 60) snprintf(out, size, "%lum", static_cast<unsigned long>(minutes));
            else snprintf(out, size, "%luh%02lum", static_cast<unsigned long>(minutes / 60), static_cast<unsigned long>(minutes % 60));
        }
    } else if (r.kind == Kind::Mistakes) {
        snprintf(out, size, "%lu / <=%lu", static_cast<unsigned long>(r.current), static_cast<unsigned long>(r.target));
    } else if (r.kind == Kind::Weight) {
        snprintf(out, size, "%lu / %lu-%lu", static_cast<unsigned long>(r.current),
                 static_cast<unsigned long>(r.target), static_cast<unsigned long>(r.upper));
    } else if (r.kind == Kind::Wins) {
        if (!r.upper) snprintf(out, size, "-- / %lu%%", static_cast<unsigned long>(r.target));
        else snprintf(out, size, "%lu / %lu%%", static_cast<unsigned long>(r.current), static_cast<unsigned long>(r.target));
    } else snprintf(out, size, "%lu / %lu", static_cast<unsigned long>(r.current), static_cast<unsigned long>(r.target));
}

// Same raster/font data as Training; Canvas supplies only the current framebuffer.
template<class Canvas> class View {
    Canvas& c;
    const evolution_progress::Progress& p;
    bool es;
    const content::PetDefinition& definition;
    void rect(int x, int y, int w, int h, uint16_t color) { c.fillRect(x,y,w,h,color); }
    int width(const char* value, bool small = false) const {
        const auto* font = small ? training_assets::font9 : training_assets::font10;
        int result = 0;
        for (const unsigned char* s = reinterpret_cast<const unsigned char*>(value); *s; ++s)
            result += font[(*s >= 32 && *s <= 126 ? *s : '?') - 32].advance;
        return result;
    }
    void text(int x, int y, const char* value, uint16_t color = white, bool small = false) {
        const auto* font = small ? training_assets::font9 : training_assets::font10;
        int top = 16, rasterTop = 16;
        for (const unsigned char* s = reinterpret_cast<const unsigned char*>(value); *s; ++s) {
            const auto& g = font[(*s >= 32 && *s <= 126 ? *s : '?') - 32];
            for (int row = 0; row < 16; ++row) if (g.rows[row]) {
                if (g.top < top) top = g.top;
                if (g.rasterTop < rasterTop) rasterTop = g.rasterTop;
                break;
            }
        }
        y += top - rasterTop;
        for (const unsigned char* s = reinterpret_cast<const unsigned char*>(value); *s; ++s) {
            const auto& g = font[(*s >= 32 && *s <= 126 ? *s : '?') - 32];
            for (int row = 0; row < 16; ++row) for (int col = 0; col < 16; ++col)
                if (g.rows[row] & (1u << col)) rect(x + col - 2, y + row, 1, 1, color);
            x += g.advance;
        }
    }
    void centered(int center, int y, const char* value, uint16_t color = white, bool small = false) {
        text(center - width(value, small) / 2, y, value, color, small);
    }
    void marker(int y, bool met) {
        if (met) {
            for (int i = 0; i < 3; ++i) rect(75 + i, y + 3 + i, 2, 1, green);
            for (int i = 0; i < 6; ++i) rect(78 + i, y + 5 - i, 2, 1, green);
        } else {
            rect(76, y, 7, 7, yellow);
            rect(77, y + 1, 5, 5, ink);
        }
    }
public:
    View(Canvas& canvas, const evolution_progress::Progress& progress, bool spanish,
         const content::PetDefinition& contentDefinition = content::builtinDefinition())
        : c(canvas), p(progress), es(spanish), definition(contentDefinition) {}
    void draw(uint8_t requestedPage) {
        using namespace evolution_progress;
        rect(0, 24, 240, 111, ink);
        centered(120, 29, p.state == State::Progress ? (es ? "PROXIMA EVOLUCION" : "NEXT EVOLUTION") : (es ? "EVOLUCION" : "EVOLUTION"), white);
        rect(5, 44, 230, 1, line);
        c.portrait(p.stage, p.state == State::Hidden);
        const char* petName = p.state == State::Hidden ? "???" : definition.stage(stages[p.stage]).name;
        if (p.stage == 0 && es) petName = "HUEVO";
        centered(36, 119, petName, white, true);
        if (p.state != State::Progress) {
            const char* message = "";
            switch (p.state) {
                case State::Reached: message = es ? "ETAPA SUPERADA" : "STAGE REACHED"; break;
                case State::Hidden: message = es ? "POR DESCUBRIR" : "UNDISCOVERED"; break;
                case State::Final: message = es ? "ETAPA FINAL" : "FINAL STAGE"; break;
                case State::Egg: message = es ? "ECLOSIONANDO" : "HATCHING"; break;
                default: message = es ? "NO DISPONIBLE" : "UNAVAILABLE"; break;
            }
            centered(155, 77, message, yellow);
            return;
        }
        const uint8_t page = requestedPage % p.pages();
        for (uint8_t slot = 0; slot < rowsPerPage; ++slot) {
            const uint8_t index = page * rowsPerPage + slot;
            if (index >= p.count) break;
            const Row& r = p.rows[index];
            const int y = 50 + slot * 18;
            char value[32];
            rowValue(r, es, value, sizeof(value));
            marker(y + 3, r.met);
            text(88, y, label(r.kind, es), muted);
            text(235 - width(value), y, value, white);
            rect(88, y + 13, 147, 2, line);
            uint32_t percent = r.met ? 100 : 0;
            if (!r.met && r.kind != Kind::Mistakes && r.kind != Kind::Weight && r.target)
                percent = static_cast<uint64_t>(r.current) * 100 / r.target;
            if (percent > 100) percent = 100;
            if (percent) rect(88, y + 13, 147 * percent / 100, 2, r.met ? green : yellow);
        }
        char footer[32];
        snprintf(footer, sizeof(footer), "%s %u/%u", es ? "REQUISITOS" : "REQUIREMENTS", page + 1, p.pages());
        centered(161, 124, footer, muted, true);
    }
};
} }
