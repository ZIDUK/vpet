"""Bilingual string catalog for the simulator UI.

The catalog is the single source of truth for every visible string the
training flow (and the practice UI) paints. The renderer asks for a
string by key via :func:`tr` and the catalog resolves the value to the
active language, falling back to Spanish when the language is not
recognised (the project's default in the legacy screens).

The catalog is intentionally flat (no nested namespaces) so tests can
assert that every visible string the renderer touches exists in BOTH
languages. New UI text MUST be added here in both languages; the
renderer is forbidden from emitting hardcoded visible text.

The mapping follows the vPet naming:

* ``HP`` / ``MP`` are abbreviations shared by both languages.
* ``CARGANDO`` / ``LOADING`` mirror the two-word labels of the
  existing status page.
* The training flow keys cover every screen the
  ``2026-10-07-batched-training-session`` spec defines (select,
  prepare, session, confirm, cancel, result, error).
"""

# ---------------------------------------------------------------------------
# Training flow strings
# ---------------------------------------------------------------------------

TRAINING_STRINGS = {
    "training.timed.title": {"ES": "ENTRENANDO", "EN": "TRAINING"},
    "training.timed.duration": {"ES": "DURACION 10 S", "EN": "DURATION 10 S"},
    "training.timed.remaining": {"ES": "FALTAN %d S", "EN": "%d S LEFT"},
    "training.timed.cancel": {"ES": "CANCELAR", "EN": "CANCEL"},
    "training.timed.repeat": {"ES": "OTRA SESION", "EN": "TRAIN AGAIN"},
    "training.timed.cost": {"ES": "COSTE %d ENE", "EN": "COST %d ENE"},
    "training.timed.available": {"ES": "SESIONES %d", "EN": "SESSIONS %d"},
    "training.timed.cancel_title": {"ES": "CANCELAR SESION?", "EN": "CANCEL SESSION?"},
    # ---- state A: select ------------------------------------------------
    "training.title":              {"ES": "ENTRENAR",       "EN": "TRAIN"},
    "training.slot":               {"ES": "ATRIBUTO",        "EN": "STAT"},
    "training.techniques":         {"ES": "TECNICAS",        "EN": "TECHNIQUES"},
    "training.techniques_sub":     {"ES": "APRENDIZAJE / DOMINIO",
                                    "EN": "LEARN / MASTER"},
    "training.back":               {"ES": "VOLVER",          "EN": "BACK"},
    "training.next_attr":          {"ES": "NEXT: ATRIBUTO",  "EN": "NEXT: STAT"},
    "training.action_choose":      {"ES": "ACTION: ELEGIR",  "EN": "ACTION: PICK"},
    "training.cost_per_rep":       {"ES": "COSTE %d ENE / REP",
                                    "EN": "COST %d ENE / REP"},
    "training.max_reps":           {"ES": "MAX %d REP",      "EN": "MAX %d REP"},
    "training.no_reps":            {"ES": "SIN REPS",        "EN": "NO REPS"},
    "training.block.energy":       {"ES": "FALTA ENERGIA",   "EN": "NO ENERGY"},
    "training.block.ev":           {"ES": "EV AL MAXIMO",    "EN": "EV MAX"},
    "training.block.pet":          {"ES": "PET NO APTO",     "EN": "PET NOT FIT"},
    "training.session_count":      {"ES": "%d/8",            "EN": "%d/8"},
    # ---- state B: prepare ----------------------------------------------
    "training.prepare.title":      {"ES": "PREPARAR: %s",    "EN": "PREPARE: %s"},
    "training.prepare.start":      {"ES": "INICIAR",         "EN": "START"},
    "training.prepare.back":       {"ES": "VOLVER",          "EN": "BACK"},
    "training.prepare.real_proj":  {"ES": "REAL %d  PROY %d", "EN": "REAL %d  PROJ %d"},
    "training.prepare.max":        {"ES": "MAXIMO %d REP",   "EN": "MAX %d REP"},
    "training.prepare.max_blocked":{"ES": "MAX 0  %s",       "EN": "MAX 0  %s"},
    "training.prepare.energy":     {"ES": "ENE %d/100",      "EN": "ENE %d/100"},
    # ---- state C: session -----------------------------------------------
    "training.session.title":      {"ES": "SESION %d/%d  %s",
                                    "EN": "SESSION %d/%d  %s"},
    "training.session.train":      {"ES": "ENTRENAR",        "EN": "TRAIN"},
    "training.session.finalize":   {"ES": "FINALIZAR",       "EN": "FINISH"},
    "training.session.reps":       {"ES": "REPS %d",         "EN": "REPS %d"},
    "training.session.limit":      {"ES": "LIMITE: %s",      "EN": "LIMIT: %s"},
    "training.session.ev":         {"ES": "EV %d",           "EN": "EV %d"},
    "training.session.ev_delta":   {"ES": "EV %d + %d -> %d / %d",
                                    "EN": "EV %d + %d -> %d / %d"},
    "training.session.ev_static":  {"ES": "EV %d / %d",     "EN": "EV %d / %d"},
    "training.session.energy_disp":{"ES": "ENE",             "EN": "ENE"},
    "training.session.energy_avail":{"ES": "DISP %d",        "EN": "AVAIL %d"},
    "training.session.energy_res": {"ES": "RES %d",          "EN": "RES %d"},
    "training.session.real_proj":  {"ES": "%s REAL %d",      "EN": "%s REAL %d"},
    "training.session.proj":       {"ES": "PROY %d",         "EN": "PROJ %d"},
    # ---- state confirm sub-state ---------------------------------------
    "training.confirm.title":      {"ES": "CERRAR ENTRENAMIENTO?",
                                    "EN": "CLOSE SESSION?"},
    "training.confirm.confirm":    {"ES": "CONFIRMAR",       "EN": "CONFIRM"},
    "training.confirm.follow":     {"ES": "SEGUIR",          "EN": "CONTINUE"},
    "training.confirm.x_rep":      {"ES": "%s x%d REP",      "EN": "%s x%d REP"},
    "training.confirm.ev_added":   {"ES": "EV +%d",          "EN": "EV +%d"},
    "training.confirm.ene_delta":  {"ES": "ENE -%d",         "EN": "ENE -%d"},
    "training.confirm.effort":     {"ES": "ESFUERZO +%d",    "EN": "EFFORT +%d"},
    # ---- state cancel sub-state ----------------------------------------
    "training.cancel.title":       {"ES": "DESCARTAR %d REPS?",
                                    "EN": "DISCARD %d REPS?"},
    "training.cancel.body":        {"ES": "No se cobrara energia ni cambiaran EV.",
                                    "EN": "No energy or EV will be charged."},
    "training.cancel.follow":      {"ES": "SEGUIR",          "EN": "CONTINUE"},
    "training.cancel.discard":     {"ES": "DESCARTAR",       "EN": "DISCARD"},
    # ---- state D: result -----------------------------------------------
    "training.result.title":       {"ES": "ENTRENAMIENTO GUARDADO",
                                    "EN": "TRAINING SAVED"},
    "training.result.heading":     {"ES": "RESULTADO",       "EN": "RESULT"},
    "training.result.ok":          {"ES": "OK",              "EN": "OK"},
    "training.result.page_summary":{"ES": "RESUMEN",         "EN": "SUMMARY"},
    "training.result.page_stats":  {"ES": "STATS",           "EN": "STATS"},
    "training.result.continue":    {"ES": "CONTINUAR",       "EN": "CONTINUE"},
    "training.result.headers":     {"ES": "         ANTES  +CAMBIO  AHORA",
                                    "EN": "         BEFORE  +CHANGE  AFTER"},
    "training.result.row":         {"ES": "%-4s %5d   %+d   %5d",
                                    "EN": "%-4s %5d   %+d   %5d"},
    "training.result.row_no_delta":{"ES": "%-4s %5d          %5d",
                                    "EN": "%-4s %5d          %5d"},
    "training.result.label.ev":    {"ES": "EV",              "EN": "EV"},
    "training.result.label.ene":   {"ES": "ENE",             "EN": "ENE"},
    "training.result.label.effort":{"ES": "ESF",             "EN": "EFF"},
    "training.result.empty":       {"ES": "Sin cambios.",    "EN": "No changes."},
    # ---- state E: error ------------------------------------------------
    "training.error.title":        {"ES": "NO SE GUARDO",    "EN": "NOT SAVED"},
    "training.error.body":         {"ES": "Ningun cambio fue aplicado.",
                                    "EN": "No change was applied."},
    "training.error.retry":        {"ES": "REINTENTAR",      "EN": "RETRY"},
    "training.error.discard":      {"ES": "DESCARTAR",       "EN": "DISCARD"},
    # ---- common / shared -----------------------------------------------
    "common.ev_short":             {"ES": "EV",              "EN": "EV"},
    "common.ene_short":            {"ES": "ENE",             "EN": "ENE"},
    "common.hp_short":             {"ES": "HP",              "EN": "HP"},
    "common.mp_short":             {"ES": "MP",              "EN": "MP"},

    # ---- status menu (T-Display 240x135) -------------------------------
    # 1/4 vital: HP de crianza, alimentacion, energia. No compartir label
    # con HP de combate (el del combate vive en la pagina 4/4 con el
    # codigo DNA y la helice).
    "status.vital.hp_care.label":  {"ES": "HP",              "EN": "HP"},
    "status.vital.hp_care.value":  {"ES": "%d",              "EN": "%d"},
    "status.vital.feed.label":     {"ES": "HAM",             "EN": "HUN"},
    "status.vital.feed.value":     {"ES": "%d",              "EN": "%d"},
    "status.vital.energy.label":   {"ES": "ENE",             "EN": "ENE"},
    "status.vital.energy.value":   {"ES": "%d",              "EN": "%d"},
    "status.vital.mood.label":     {"ES": "ANIMO",           "EN": "MOOD"},
    "status.vital.mood.value":     {"ES": "%d",              "EN": "%d"},
    # 2/4 care: edad legible, sobrealimentos, errores de cuidado,
    # esfuerzo, batallas. Sin siglas tipo OF/CM.
    "status.care.age.label":       {"ES": "EDAD",            "EN": "AGE"},
    "status.care.age.seconds":     {"ES": "%ds",             "EN": "%ds"},
    "status.care.age.minutes":     {"ES": "%dm",             "EN": "%dm"},
    "status.care.age.hours":       {"ES": "%dh",             "EN": "%dh"},
    "status.care.age.days":        {"ES": "%dd",             "EN": "%dd"},
    "status.care.overfeed.label":  {"ES": "EXCESO",         "EN": "OVERFEED"},
    "status.care.care_err.label":  {"ES": "CUIDADO",         "EN": "CARE"},
    "status.care.effort.label":    {"ES": "ESFUERZO",        "EN": "EFFORT"},
    "status.care.effort.value":    {"ES": "%d/4",            "EN": "%d/4"},
    "status.care.battles.label":   {"ES": "BATALLAS",        "EN": "BATTLES"},
    "status.care.battles.value":   {"ES": "%d",              "EN": "%d"},
    "status.care.injuries.label":  {"ES": "LESIONES",        "EN": "INJURIES"},
    "status.care.injuries.value":  {"ES": "%d/15",           "EN": "%d/15"},
    # 3/4 battle: peso, DP (no renombrar), %victorias, proteina, V-D.
    "status.battle.weight.label":  {"ES": "PESO",            "EN": "WEIGHT"},
    "status.battle.weight.value":  {"ES": "%d",              "EN": "%d"},
    "status.battle.dp.label":      {"ES": "DP",              "EN": "DP"},
    "status.battle.dp.value":      {"ES": "%d/3",            "EN": "%d/3"},
    "status.battle.winrate.label": {"ES": "VICTORIAS",       "EN": "WIN RATE"},
    "status.battle.winrate.value": {"ES": "%d%%",            "EN": "%d%%"},
    "status.battle.winrate.empty": {"ES": "--",              "EN": "--"},
    "status.battle.protein.label": {"ES": "PROTEINA",        "EN": "PROTEIN"},
    "status.battle.protein.value": {"ES": "%d/7",            "EN": "%d/7"},
    "status.battle.wl.label":      {"ES": "V-D",             "EN": "W-L"},
    "status.battle.wl.value":      {"ES": "%d-%d",           "EN": "%d-%d"},
    "status.battle.wl.empty":      {"ES": "--",              "EN": "--"},
    # 4/4 DNA: codigo completo, helix rotando, 6 stats con barras 0..99.
    "status.dna.code":             {"ES": "DNA",             "EN": "DNA"},
    "status.dna.empty":            {"ES": "SIN ADN",         "EN": "NO DNA"},
    "status.dna.stat.hp":          {"ES": "HP",              "EN": "HP"},
    "status.dna.stat.mp":          {"ES": "MP",              "EN": "MP"},
    "status.dna.stat.off":         {"ES": "OF",              "EN": "OFF"},
    "status.dna.stat.def":         {"ES": "DEF",             "EN": "DEF"},
    "status.dna.stat.spd":         {"ES": "VEL",             "EN": "SPD"},
    "status.dna.stat.brn":         {"ES": "MEN",             "EN": "BRN"},
    "status.header":               {"ES": "STATUS %d/%d",    "EN": "STATUS %d/%d"},
}

# ---------------------------------------------------------------------------
# Stat name keys (one entry per stat in TRAINING_TYPES)
# ---------------------------------------------------------------------------

STAT_STRINGS = {
    "hp":  {"ES": "VIDA",     "EN": "HP"},
    "mp":  {"ES": "MP",       "EN": "MP"},
    "off": {"ES": "ATAQUE",   "EN": "ATTACK"},
    "def": {"ES": "DEFENSA",  "EN": "DEFENSE"},
    "spd": {"ES": "VELOCIDAD","EN": "SPEED"},
    "brn": {"ES": "MENTE",    "EN": "MIND"},
}

TRAINING_STRINGS.update({
    "rest.title": {"ES": "DESCANSO", "EN": "REST"},
    "rest.cue.energy": {"ES": "POCA ENERGIA", "EN": "LOW ENERGY"},
    "rest.cue.bedtime": {"ES": "HORA DE DORMIR", "EN": "BEDTIME"},
    "rest.off": {"ES": "APAGAR LUZ", "EN": "LIGHTS OFF"},
    "rest.on": {"ES": "ENCENDER LUZ", "EN": "LIGHTS ON"},
    "rest.back": {"ES": "VOLVER", "EN": "BACK"},
    "options.pause": {"ES": "PAUSAR CRIANZA", "EN": "PAUSE PET"},
    "options.on": {"ES": "SI", "EN": "ON"},
    "options.off": {"ES": "NO", "EN": "OFF"},
    "explore.title": {"ES": "EXPLORAR", "EN": "EXPLORE"},
    "explore.patio": {"ES": "PATIO", "EN": "PATIO"},
    "explore.jornada": {"ES": "JORNADA", "EN": "SHIFT"},
    "explore.noche": {"ES": "NOCHE", "EN": "NIGHT"},
    "explore.stats": {"ES": "ELEGIR ATRIBUTO", "EN": "CHOOSE A STAT"},
    "explore.confirm": {"ES": "PREPARAR SALIDA", "EN": "READY TO LEAVE"},
    "explore.start": {"ES": "ENVIAR", "EN": "SEND"},
    "explore.back": {"ES": "VOLVER", "EN": "BACK"},
    "explore.done": {"ES": "CONTINUAR", "EN": "CONTINUE"},
    "explore.claim": {"ES": "RECLAMAR", "EN": "CLAIM"},
    "explore.recall": {"ES": "REGRESAR YA", "EN": "RETURN NOW"},
    "explore.recall_title": {"ES": "REGRESO ANTICIPADO", "EN": "EARLY RETURN"},
    "explore.away": {"ES": "DE EXPLORACION", "EN": "ON EXPEDITION"},
    "explore.ready": {"ES": "DE VUELTA", "EN": "BACK FROM TRIP"},
    "explore.receipt": {"ES": "RECOMPENSAS GUARDADAS", "EN": "REWARDS SAVED"},
    "explore.good": {"ES": "BIEN CUIDADO", "EN": "WELL CARED FOR"},
    "explore.poor": {"ES": "NECESITA CUIDADOS", "EN": "NEEDS CARE"},
    "explore.home_only": {"ES": "EXPLORA DESDE ROOKIE", "EN": "EXPLORE FROM ROOKIE"},
    "explore.energy": {"ES": "+%d ENERGIA", "EN": "+%d ENERGY"},
    "explore.ev": {"ES": "+%d EV %s", "EN": "+%d EV %s"},
    "explore.mastery": {"ES": "+%d DOMINIO LLAMA", "EN": "+%d FLAME MASTERY"},
    "explore.learning": {"ES": "LLAMA %d/2 NOCHES", "EN": "FLAME %d/2 NIGHTS"},
    "explore.learned": {"ES": "LLAMA APRENDIDA", "EN": "FLAME LEARNED"},
    "explore.guide": {"ES": "GUIA: +1 EV AL ENTRENAR", "EN": "GUIDE: +1 EV NEXT TRAIN"},
    "explore.none": {"ES": "SIN PREMIO EN ESTE REGRESO", "EN": "NO REWARD THIS RETURN"},
    "explore.week": {"ES": "SEMANA  EV %d/8  DOM %d/4", "EN": "WEEK  EV %d/8  MAST %d/4"},
    "explore.patio_reward": {"ES": "RECUPERA ENERGIA", "EN": "RESTORES ENERGY"},
    "explore.jornada_reward": {"ES": "+2 EV Y GUIA", "EN": "+2 EV AND GUIDE"},
    "explore.noche_reward": {"ES": "APRENDE / DOMINA LLAMA", "EN": "LEARN / MASTER FLAME"},
    "explore.free": {"ES": "COSTE: 0 ENERGIA", "EN": "COST: 0 ENERGY"},
    "explore.save_failed": {"ES": "NO SE GUARDO. REINTENTAR", "EN": "SAVE FAILED. RETRY"},
    "explore.blocked": {"ES": "SALIDA NO DISPONIBLE", "EN": "TRIP UNAVAILABLE"},
})

DEFAULT_LANGUAGE = "ES"
SUPPORTED_LANGUAGES = ("ES", "EN")


def tr(pet, key, *args):
    """Return the localized string for ``key``.

    The language is read from ``pet.language``; anything that is not
    ``"EN"`` falls back to ``DEFAULT_LANGUAGE`` ("ES") to keep the
    legacy screens readable. The catalog is flat: missing keys raise
    ``KeyError`` so the test suite can pin the complete vocabulary
    used by the renderer.
    """
    if key not in TRAINING_STRINGS:
        raise KeyError("missing i18n key: %r" % key)
    lang = getattr(pet, "language", DEFAULT_LANGUAGE)
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    template = TRAINING_STRINGS[key][lang]
    if args:
        return template % args
    return template


def tr_stat(pet, stat):
    """Return the localized display name for a stat. The language
    switch mirrors :func:`tr`; the canonical stat name (e.g. "off")
    is used for routing while this name is used for display only."""
    if stat not in STAT_STRINGS:
        return stat.upper()
    lang = getattr(pet, "language", DEFAULT_LANGUAGE)
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    return STAT_STRINGS[stat][lang]


def tr_status_dna_label(pet, stat):
    """Return the 3-char status page label for a stat (HP, MP, ATQ, ...).
    Used by the DNA page so the six rows fit a 240 px wide frame
    without truncating the DNA code on the right of the helix."""
    key = "status.dna.stat." + stat
    return tr(pet, key)


def format_age(pet, total_seconds):
    """Pick the most readable unit for ``total_seconds``. Order of
    precedence: seconds (<60s), minutes (<60min), hours (<24h), days.
    The semantics of the stored value are unchanged; the format is
    the only thing that adapts. The unit is encoded as a short
    suffix that fits the 4-char label space of the chip."""
    seconds = max(0, int(total_seconds))
    if seconds < 60:
        return tr(pet, "status.care.age.seconds", seconds)
    if seconds < 3600:
        return tr(pet, "status.care.age.minutes", seconds // 60)
    if seconds < 86400:
        return tr(pet, "status.care.age.hours", seconds // 3600)
    return tr(pet, "status.care.age.days", seconds // 86400)


def tr_languages():
    """Return the list of supported language codes. Exposed for the
    previews / test setup; the renderer does not branch on the list."""
    return list(SUPPORTED_LANGUAGES)
