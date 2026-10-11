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
inline const char* restTitle(bool spanish) { return pick(spanish, "REST", "DESCANSO"); }
inline const char* sleep(bool spanish) { return pick(spanish, "SLEEP", "DORMIR"); }
inline const char* cold(bool spanish) { return pick(spanish, "COLD", "FRIO"); }
inline const char* backup(bool spanish) { return pick(spanish, "BACKUP", "RESERVA"); }
inline const char* emptySlot(bool spanish) { return pick(spanish, "EMPTY", "VACIO"); }
inline const char* dateTitle(bool spanish) { return pick(spanish, "DATE", "FECHA"); }
inline const char* timeTitle(bool spanish) { return pick(spanish, "TIME", "HORA"); }

inline const char* hp(bool spanish) { return pick(spanish, "HP", "PV"); }
inline const char* mp(bool) { return "MP"; }
inline const char* offense(bool) { return "OFF"; }
inline const char* def(bool) { return "DEF"; }
inline const char* spd(bool spanish) { return pick(spanish, "SPD", "VEL"); }
inline const char* brn(bool spanish) { return pick(spanish, "BRN", "CER"); }
inline const char* dna(bool) { return "ADN"; }
inline const char* hunger(bool spanish) { return pick(spanish, "HUN", "HAM"); }
inline const char* energy(bool spanish) { return pick(spanish, "ENE", "ENE"); }
inline const char* age(bool spanish) { return pick(spanish, "AGE", "EDAD"); }
inline const char* effort(bool spanish) { return pick(spanish, "EFF", "ESF"); }
inline const char* battles(bool spanish) { return pick(spanish, "BAT", "BAT"); }
inline const char* mood(bool spanish) { return pick(spanish, "MOOD", "ANIMO"); }
inline const char* careMistakes(bool spanish) { return pick(spanish, "CM", "CM"); }
inline const char* overfeeds(bool spanish) { return pick(spanish, "OVERFEED", "EXCESO"); }
inline const char* protein(bool spanish) { return pick(spanish, "PROTEIN", "PROTEINA"); }
inline const char* medkit(bool spanish) { return pick(spanish, "MEDKIT", "BOTIQUIN"); }
inline const char* proteinOverdose(bool spanish) { return pick(spanish, "PR", "PR"); }
inline const char* weight(bool spanish) { return pick(spanish, "WT", "PES"); }
inline const char* dp(bool spanish) { return pick(spanish, "DP", "DP"); }
inline const char* winRatio(bool spanish) { return pick(spanish, "WR", "WR"); }

// Training stat labels. The legacy copy::offense/spd/etc. stay in place
// for the Status DNA row; the batched training session uses full words.
inline const char* trainingName(int index, bool spanish) {
    switch (index) {
        case 0: return spanish ? "ATAQUE"    : "ATTACK";
        case 1: return spanish ? "DEFENSA"   : "DEFENSE";
        case 2: return spanish ? "VELOCIDAD" : "SPEED";
        case 3: return spanish ? "VIDA"      : "HP";
        case 4: return "MP";
        case 5: return spanish ? "MENTE"     : "MIND";
    }
    return "?";
}

inline const char* trainingAction(bool spanish) {
    return pick(spanish, "TRAIN", "ENTRENAR");
}
// Training state actions and labels. Every string the player-facing
// renderer (Panels::drawTraining) prints must resolve through one of
// these helpers; the previous firmware left several literals (REPS,
// EV, ENE, ENTRENAR, FINALIZAR, CONFIRMAR, ENTRENO LISTO,
// ACTION…CANCELAR, …) hard-coded, which made the screen render a
// mixed-language line and ship visibly broken text on a Spanish
// device. The new entries keep both variants the same length where
// practical so the 240×135 layout does not shift when the language
// toggle is flipped.
inline const char* trainingTrain(bool spanish)      { return pick(spanish, "TRAIN",      "ENTRENAR"); }
inline const char* trainingFinalize(bool spanish)   { return pick(spanish, "FINALIZE",   "FINALIZAR"); }
inline const char* trainingConfirm(bool spanish)    { return pick(spanish, "CONFIRM",    "CONFIRMAR"); }
inline const char* trainingDone(bool spanish)       { return pick(spanish, "DONE",       "ENTRENO LISTO"); }
inline const char* trainingStart(bool spanish)      { return pick(spanish, "START",      "EMPEZAR"); }
inline const char* trainingApply(bool spanish)      { return pick(spanish, "APPLY",      "APLICAR"); }
inline const char* trainingCancel(bool spanish)     { return pick(spanish, "CANCEL",     "CANCELAR"); }
inline const char* trainingReturn(bool spanish)     { return pick(spanish, "BACK",       "VOLVER"); }
inline const char* trainingExit(bool spanish)       { return pick(spanish, "EXIT",       "SALIR"); }
inline const char* trainingError(void)              { return "ERROR"; }
inline const char* trainingNow(bool spanish)        { return pick(spanish, "NOW",        "AHORA"); }
inline const char* trainingAvail(bool spanish)      { return pick(spanish, "AVAIL",      "DISP"); }
inline const char* trainingReserve(bool)            { return "RES"; }
inline const char* trainingReal(bool spanish)       { return pick(spanish, "REAL",       "REAL"); }
inline const char* trainingProj(bool spanish)       { return pick(spanish, "PROJ",       "PROY"); }
inline const char* trainingHappy(bool spanish)      { return pick(spanish, "HAPPY",      "FELIC"); }
inline const char* trainingCost(bool spanish)       { return pick(spanish, "COST",       "COSTE"); }
inline const char* trainingActionLabel(bool spanish){ return pick(spanish, "ACTION",     "ACTION"); }
inline const char* trainingButtonRep(bool spanish)  { return pick(spanish, "REP",        "REP"); }
inline const char* trainingReady(bool spanish)      { return pick(spanish, "READY",      "LISTO"); }

// Footer button labels (used in Confirm, Result, Cancel, Error).
// Continue closes the result screen; Retry re-attempts after a save
// failure; Discard cancels without applying changes.
inline const char* trainingContinue(bool spanish)   { return pick(spanish, "CONTINUE",   "CONTINUAR"); }
inline const char* trainingRetry(bool spanish)      { return pick(spanish, "RETRY",      "REINTENTAR"); }
inline const char* trainingDiscard(bool spanish)    { return pick(spanish, "DISCARD",    "DESCARTAR"); }

// Confirm-screen copy used at the subtitle line. The hardware cannot
// safely format inside a single `pick` literal, so the renderer calls
// snprintf with the templated prefix/suffix and the chosen stat name.
inline const char* confirmTitle(bool spanish)       { return pick(spanish, "CLOSE SESSION?", "CERRAR ENTRENAMIENTO?"); }
inline const char* confirmRepPrefix(bool spanish)   { return pick(spanish, "x",  "x"); }
inline const char* confirmRepSuffix(bool spanish)   { return pick(spanish, "REP", "REP"); }
inline const char* injured(bool spanish) { return pick(spanish, "HURT", "HERIDO"); }
inline const char* dead(bool spanish) { return pick(spanish, "DEAD", "MUERTO"); }
inline const char* frozen(bool spanish) { return pick(spanish, "COLD", "FRIO"); }
inline const char* callHunger(bool spanish) { return pick(spanish, "CALL HUN", "LLAM HAM"); }
inline const char* callStrength(bool spanish) { return pick(spanish, "CALL STR", "LLAM FUE"); }
inline const char* callLights(bool spanish) { return pick(spanish, "CALL LIT", "LLAM LUZ"); }
inline const char* callNone(bool spanish) { return pick(spanish, "CALL --", "LLAM --"); }

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
inline const char* fireRing(bool spanish) { return pick(spanish, "RING", "ANILLO"); }
inline const char* itemName(uint8_t index, bool spanish) {
    switch (index) {
        case 0: return meat(spanish);
        case 1: return itemEnergy(spanish);
        case 2: return exp(spanish);
        case 3: return fireRing(spanish);
        case 4: return protein(spanish);
        case 5: return medkit(spanish);
        default: return back(spanish);
    }
}
inline const char* itemBlurb(uint8_t index, bool spanish) {
    switch (index) {
        case 0: return pick(spanish, "+20 HUN", "+20 HAM");
        case 1: return pick(spanish, "+25 ENE", "+25 ENE");
        case 2: return pick(spanish, "+8 EFF", "+8 ESF");
        case 3: return pick(spanish, "+15 POW", "+15 POD");
        case 4: return pick(spanish, "+20 ENE", "+20 ENE");
        case 5: return pick(spanish, "HEAL HURT", "CURA");
        default: return pick(spanish, "CLOSE BAG", "CERRAR");
    }
}
inline const char* yourLine(bool spanish) { return pick(spanish, "YOUR LINE", "TU LINEA"); }
inline const char* evoShort(uint8_t stage, bool spanish) {
    switch (stage) {
        case 0: return pick(spanish, "EGG", "HUEVO");
        case 1: return "SPARK";
        case 2: return "FIRE";
        case 3: return "FLAME";
        case 4: return "DRAG";
        default: return "???";
    }
}
inline const char* evoNow(bool spanish) { return pick(spanish, "NOW", "AHORA"); }
inline const char* evoReached(bool spanish) { return pick(spanish, "REACHED", "LOGRADO"); }

}  // namespace copy
}  // namespace vpet
