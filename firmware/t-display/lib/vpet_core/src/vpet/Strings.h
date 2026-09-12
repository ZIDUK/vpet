#pragma once

#include <string.h>

namespace vpet {

inline bool languageIsSpanish(const char* language) {
    return language != nullptr && strcmp(language, "ES") == 0;
}

namespace copy {

inline const char* pick(bool spanish, const char* english, const char* castellano) {
    return spanish ? castellano : english;
}

inline const char* statusTitle(bool spanish) { return pick(spanish, "STATUS", "ESTADO"); }
inline const char* inventoryTitle(bool spanish) { return pick(spanish, "INVENTORY", "INVENTARIO"); }
inline const char* evolutionTitle(bool spanish) { return pick(spanish, "EVOLUTION", "EVOLUCION"); }
inline const char* evolutionDetailTitle(bool spanish) { return pick(spanish, "EVOLUTION DETAIL", "DETALLE"); }
inline const char* optionsTitle(bool spanish) { return pick(spanish, "OPTIONS", "OPCIONES"); }
inline const char* dateTitle(bool spanish) { return pick(spanish, "DATE", "FECHA"); }
inline const char* timeTitle(bool spanish) { return pick(spanish, "TIME", "HORA"); }

inline const char* hp(bool spanish) { return pick(spanish, "HP", "PV"); }
inline const char* hunger(bool spanish) { return pick(spanish, "HUN", "HAM"); }
inline const char* energy(bool spanish) { return pick(spanish, "ENE", "ENE"); }
inline const char* age(bool spanish) { return pick(spanish, "AGE", "EDAD"); }
inline const char* effort(bool spanish) { return pick(spanish, "EFF", "ESF"); }
inline const char* battles(bool spanish) { return pick(spanish, "BAT", "BAT"); }
inline const char* mood(bool spanish) { return pick(spanish, "MOOD", "ANIMO"); }

inline const char* language(bool spanish) { return pick(spanish, "LANGUAGE", "IDIOMA"); }
inline const char* sound(bool spanish) { return pick(spanish, "SOUND", "SONIDO"); }
inline const char* save(bool spanish) { return pick(spanish, "SAVE", "GUARDAR"); }
inline const char* load(bool spanish) { return pick(spanish, "LOAD", "CARGAR"); }
inline const char* evolve(bool spanish) { return pick(spanish, "EVOLVE", "EVOLUCIONAR"); }
inline const char* back(bool spanish) { return pick(spanish, "BACK", "ATRAS"); }
inline const char* on(bool spanish) { return pick(spanish, "ON", "SI"); }
inline const char* off(bool spanish) { return pick(spanish, "OFF", "NO"); }

inline const char* bluetoothOff(bool spanish) { return pick(spanish, "BLUETOOTH: OFF", "BLUETOOTH: NO"); }
inline const char* bluetoothAdvertising(bool spanish) {
    return pick(spanish, "BLUETOOTH: ADVERTISING", "BLUETOOTH: ANUNCIANDO");
}
inline const char* bluetoothConnected(bool spanish) {
    return pick(spanish, "BLUETOOTH: CONNECTED", "BLUETOOTH: CONECTADO");
}
inline const char* bluetoothError(bool spanish) {
    return pick(spanish, "BLUETOOTH: ERROR", "BLUETOOTH: ERROR");
}

inline const char* year(bool spanish) { return pick(spanish, "YEAR", "ANO"); }
inline const char* month(bool spanish) { return pick(spanish, "MONTH", "MES"); }
inline const char* day(bool spanish) { return pick(spanish, "DAY", "DIA"); }
inline const char* hour(bool spanish) { return pick(spanish, "HOUR", "HORA"); }
inline const char* minute(bool spanish) { return pick(spanish, "MIN", "MIN"); }

inline const char* meat(bool spanish) { return pick(spanish, "MEAT", "CARNE"); }
inline const char* itemEnergy(bool spanish) { return pick(spanish, "ENERGY", "ENERGIA"); }
inline const char* exp(bool spanish) { return pick(spanish, "EXP", "EXP"); }
inline const char* fireRing(bool spanish) { return pick(spanish, "FIRE RING", "ANILLO"); }
inline const char* yourLine(bool spanish) { return pick(spanish, "YOUR LINE", "TU LINEA"); }

}  // namespace copy
}  // namespace vpet
