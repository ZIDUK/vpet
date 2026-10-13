"""Batched training renderer for the 240x135 simulator (2026-10-07 spec).

The renderer reads the orchestrator's state and paints one of:

* state A (select)        — six attribute icons plus techniques and back.
* state B (prepare)       — confirmed attribute, real vs projected, max reps.
* state C (session)       — active batch, real vs projected, reserved energy.
* sub-state confirm       — confirm / seguir before commit.
* sub-state cancel        — discard / seguir.
* state D (result)        — two navigable pages:
  - ``summary``: ANTES | CAMBIO | AHORA for the trained attribute.
  - ``stats``: six-attribute bar grid with the trained attribute
    highlighted and only the rows that actually changed shown with a
    delta column.
* state E (error)         — retry / discard after a save failure.

All sizes are 240x135. The renderer reuses the existing sprite and
icon helpers and never invents new glyphs or copies formulas. Text is
painted with the same default bitmap fonts the rest of the simulator
uses. No emoji or unicode punctuation is introduced; arrows are
``>`` and ``-`` (PIL-safe in the default font).

**i18n:** every visible string is read from :mod:`core.i18n`. The
renderer must not embed any hardcoded user-facing text. The session's
``pet.language`` ("ES" / "EN") drives the choice; the catalog falls
back to Spanish when the language flag is missing or unrecognised.
"""
from pathlib import Path

from PIL import Image, ImageDraw

from core.dna import combat_stat
from core.i18n import tr, tr_stat
from core.training import (TRAINING_ENERGY_COST, TRAINING_EV_GAIN, TRAINING_TYPES,
                            batch_projected_value, batch_plan_one_rep,
                            training_index_for)
from scripts.practice_icons import info_icon, technique_icon
from scripts.practice_renderer import (INK, WHITE, MUTED, YELLOW, GREEN, MP, HP, TEAL, PANEL,
                                        asset_icon, bar, icon_button, info_label,
                                        paste_icon, pet_sprite, render_practice, text)
from scripts.training_session import (TRAINING_ANIMATION_MS,
                                        STATE_SELECT, STATE_PREPARE, STATE_SESSION,
                                        STATE_CONFIRM, STATE_RESULT, STATE_CANCEL,
                                        STATE_ERROR)

TRAINING_FRAME_INTERVALS = {0: 50, 1: 50, 2: 50, 3: 50, 4: 50, 5: 50}


# ---------------------------------------------------------------------------
# Band layout (240x135). Keep in sync with the other simulators.
# ---------------------------------------------------------------------------

RESULT_PAGE_SUMMARY = "summary"
RESULT_PAGE_STATS = "stats"
RESULT_PAGES = (RESULT_PAGE_SUMMARY, RESULT_PAGE_STATS)


def render_training(build_dir, session, now_ms=0):
    """Dispatch to the right screen for the current state. The state A
    and B renderers preserve the original layout used by the legacy
    previews (header at y=0..20, sprite at left, action icons at the
    bottom). The new states (C, confirm, cancel, D, E) reuse the same
    bands without overlap."""
    build_dir = Path(build_dir)
    if session.techniques is not None:
        return render_practice(build_dir, session.techniques, now_ms)
    state = getattr(session, "state", STATE_SELECT)
    if state == STATE_SELECT:
        return _render_select(build_dir, session, now_ms)
    if state == STATE_PREPARE:
        return _render_prepare(build_dir, session, now_ms)
    if state == STATE_SESSION:
        return _render_session(build_dir, session, now_ms)
    if state == STATE_CONFIRM:
        return _render_confirm(build_dir, session, now_ms)
    if state == STATE_CANCEL:
        return _render_cancel(build_dir, session, now_ms)
    if state == STATE_RESULT:
        return _render_result(build_dir, session, now_ms)
    if state == STATE_ERROR:
        return _render_error(build_dir, session, now_ms)
    return _render_select(build_dir, session, now_ms)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _color_for_state(focus, target, color=YELLOW):
    return color if focus == target else MUTED


def _block_label(pet, reason):
    key = {"FALTA ENERGIA": "training.block.energy",
           "EV AL MAXIMO": "training.block.ev",
           "PET NO APTO": "training.block.pet"}.get(reason)
    return tr(pet, key) if key else reason


def _header(draw, build_dir, title, right):
    draw.rectangle((0, 0, 239, 19), fill=TEAL)
    paste_icon(frame=draw._image, icon=asset_icon(build_dir, "Training"),
                x=4, y=2)
    text(draw, (26, 4), title)
    text(draw, (210, 4), right, MUTED, small=True)


def _energy_row(draw, pet, x, y, real, reserved):
    """Draw the energy row showing AVAIL (real - reserved) and RES."""
    disp = max(0, int(real) - int(reserved))
    text(draw, (x, y), tr(pet, "training.session.energy_disp"), MP, small=True)
    text(draw, (x + 24, y),
         tr(pet, "training.session.energy_avail", disp), WHITE, small=True)
    text(draw, (x + 84, y),
         tr(pet, "training.session.energy_res", int(reserved)), YELLOW, small=True)


def _ev_row(draw, pet, x, y, current_ev, pending_ev):
    """Draw the EV row: 'EV 18 + 24 -> 42 / 252' style, omitting the
    delta when it is zero."""
    pending = int(pending_ev)
    base = int(current_ev)
    if pending > 0:
        line = tr(pet, "training.session.ev_delta", base, pending,
                  min(252, base + pending))
    else:
        line = tr(pet, "training.session.ev_static", base)
    text(draw, (x, y), line, GREEN if pending > 0 else WHITE, small=True)


def _stat_pair(draw, pet, x, y, stat_label, real, projected, color=WHITE):
    """Draw the 'DEF REAL 13  PROY 13' style row."""
    text(draw, (x, y),
         tr(pet, "training.session.real_proj", stat_label, int(real)),
         color, small=True)
    text(draw, (x + 100, y), tr(pet, "training.session.proj", int(projected)),
         GREEN if int(projected) != int(real) else color, small=True)


def _icon_name_for(stat):
    for item in TRAINING_TYPES:
        if item["stat"] == stat:
            return item["icon"]
    return "lock"


# ---------------------------------------------------------------------------
# State A: select
# ---------------------------------------------------------------------------


def _render_select(build_dir, session, now_ms):
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, 239, 19), fill=TEAL)
    paste_icon(frame, asset_icon(build_dir, "Training"), 4, 2)
    text(draw, (26, 4), tr(session.pet, "training.title"))
    text(draw, (210, 4),
         tr(session.pet, "training.session_count", session.index + 1),
         MUTED, small=True)
    # Sprite on the left, animation depending on the focused attribute.
    item = TRAINING_TYPES[session.index] if session.index < len(TRAINING_TYPES) else None
    animation = item["animation"] if item else None
    pet_sprite(frame, build_dir, 0, 30, 68, animation, now_ms,
               species=session.pet.species,
               frame_interval_ms=TRAINING_FRAME_INTERVALS.get(session.index, 75))
    if session.index < len(TRAINING_TYPES):
        info_label(frame, draw, item["icon"], 70, 24,
                   tr_stat(session.pet, item["stat"]), YELLOW)
        real, projected = batch_projected_value(session.pet, item["stat"], TRAINING_EV_GAIN)
        draw.rectangle((66, 41, 67, 59), fill=YELLOW)
        text(draw, (72, 41), "%d > %d (+%d)" % (real, projected,
                                                 max(0, projected - real)),
             GREEN)
        ev = session.pet.ev_at(item["stat"])
        draw.rectangle((70, 61, 234, 62), fill=PANEL)
        fill_width = ev * 165 // 252
        if fill_width:
            draw.rectangle((70, 61, 69 + fill_width, 62), fill=GREEN)
        max_reps, reason = _max_reps_with_reason(session.pet, item["stat"])
        tiles = ((70, GREEN), (126, YELLOW), (182, MP))
        for x, accent in tiles:
            draw.rectangle((x, 73, x + 51, 103), fill=PANEL)
            draw.rectangle((x, 73, x + 51, 74), fill=accent)
        text(draw, (73, 77), "EV", MUTED, small=True)
        text(draw, (73, 89), "%d/252" % ev, GREEN, small=True)
        text(draw, (129, 77), "SES" if session.pet.language == "ES" else "SETS",
             MUTED, small=True)
        text(draw, (129, 89), str(max_reps), YELLOW, small=True)
        text(draw, (185, 77), "COSTE" if session.pet.language == "ES" else "COST",
             MUTED, small=True)
        text(draw, (185, 89), "%d ENE" % TRAINING_ENERGY_COST, MP, small=True)
        if reason:
            text(draw, (70, 105), _block_label(session.pet, reason), HP, small=True)
    elif session.index >= len(TRAINING_TYPES):
        text(draw, (70, 24), tr(session.pet, "training.techniques"), YELLOW)
        es = session.pet.language == "ES"
        progress = session.pet.techniques
        learned = sum(progress.learned(i) for i in range(3))
        text(draw, (70, 41), ("APRENDIDAS " if es else "LEARNED ") + "%d/3" % learned,
             GREEN, small=True)
        names = ("GOLPE", "LLAMA", "GUARDIA") if session.pet.language == "ES" else ("PUNCH", "FLAME", "GUARD")
        for i, key in enumerate(("punch", "flame", "guard")):
            paste_icon(frame, technique_icon(key), 82 + i * 54, 64)
            text(draw, (74 + i * 54, 86), names[i], (YELLOW, HP, MP)[i], small=True)
        text(draw, (70, 101), ("EQUIPADAS " if es else "EQUIPPED ") + "%d/2" % len(progress.equipped), MUTED, small=True)
    # The inline eligibility reason is authoritative on this screen. Do not
    # paint the action feedback band over the same pixels.
    if session.message and not (session.index < len(TRAINING_TYPES) and reason):
        _feedback_band(draw, session.pet, session.message, color=HP)
    # Action icons for the six attributes + techniques + back.
    icons = [info_icon(t["icon"]) for t in TRAINING_TYPES]
    icons += [asset_icon(build_dir, "Pedia"), asset_icon(build_dir, "Back")]
    for i, icon in enumerate(icons):
        icon_button(frame, draw, icon, 4 + i * 29, 115, i == session.index, size=20)
    return frame


def _max_reps_with_reason(pet, stat):
    """Wrap batch_max_reps so the state A renderer can show the
    block reason inline (e.g. 'FALTA ENERGIA') next to the sprite."""
    from core.training import batch_max_reps
    return batch_max_reps(pet, stat)


# ---------------------------------------------------------------------------
# State B: prepare
# ---------------------------------------------------------------------------


def _metric(draw, y, title, value, color):
    draw.rectangle((70, y, 237, y + 13), outline=PANEL)
    draw.line((160, y, 160, y + 13), fill=PANEL)
    text(draw, (74, y + 1), title, color, small=True)
    text(draw, (166, y + 1), value, WHITE, small=True)


def _render_prepare(build_dir, session, now_ms):
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, 239, 19), fill=TEAL)
    paste_icon(frame, asset_icon(build_dir, "Training"), 4, 2)
    stat = session._chosen_stat
    name = tr_stat(session.pet, stat)
    text(draw, (26, 4), tr(session.pet, "training.prepare.title", name))
    text(draw, (210, 4), "B", MUTED, small=True)
    # Sprite idle on the left.
    pet_sprite(frame, build_dir, 0, 30, 68, None, now_ms,
               species=session.pet.species, frame_interval_ms=75)
    info_label(frame, draw, _icon_name_for(stat), 70, 24, name, YELLOW)
    real, projected = batch_projected_value(session.pet, stat, TRAINING_EV_GAIN)
    es = session.pet.language == "ES"
    _metric(draw, 40, "VALOR" if es else "VALUE", "%d > %d" % (real, projected), GREEN)
    _metric(draw, 54, "ENTRENO" if es else "TRAINING", "%d/252" % session.pet.ev_at(stat), GREEN)
    _metric(draw, 68, "ENERGIA" if es else "ENERGY", "%d/100" % session.pet.get("e"), MP)
    _metric(draw, 82, "COSTE" if es else "COST", "-8", HP)
    _metric(draw, 96, "TIEMPO" if es else "TIME", "10s", YELLOW)
    if session.max_reps() <= 0:
        _feedback_band(draw, session.pet, session.train_block_reason() or tr(session.pet, "training.no_reps"), color=HP)
    # Two-option focus: INICIAR / VOLVER.
    if session._focus == "start":
        _action_button(draw, 4, 115, tr(session.pet, "training.prepare.start"), YELLOW)
        _action_button(draw, 100, 115, tr(session.pet, "training.prepare.back"), MUTED)
    else:
        _action_button(draw, 4, 115, tr(session.pet, "training.prepare.start"), MUTED)
        _action_button(draw, 100, 115, tr(session.pet, "training.prepare.back"), YELLOW)
    if session.message:
        _feedback_band(draw, session.pet, session.message, color=HP)
    return frame


# ---------------------------------------------------------------------------
# State C: session
# ---------------------------------------------------------------------------


def _render_session(build_dir, session, now_ms):
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, 239, 19), fill=TEAL)
    paste_icon(frame, asset_icon(build_dir, "Training"), 4, 2)
    stat = session._chosen_stat
    name = tr_stat(session.pet, stat)
    text(draw, (26, 4),
         tr(session.pet, "training.timed.title"))
    text(draw, (210, 4), "10s", MUTED, small=True)
    # Sprite with the training animation if a rep is in flight.
    progress = session.animation_progress(now_ms)
    if progress is not None and session._animation_index is not None:
        animation = TRAINING_TYPES[session._animation_index]["animation"]
        pet_sprite(frame, build_dir, 0, 30, 68, animation, now_ms,
                   species=session.pet.species,
                   frame_interval_ms=TRAINING_FRAME_INTERVALS.get(session._animation_index, 75))
    else:
        pet_sprite(frame, build_dir, 0, 30, 68, None, now_ms,
                   species=session.pet.species, frame_interval_ms=75)
    info_label(frame, draw, _icon_name_for(stat), 70, 24, name, YELLOW)
    real, projected = session.current_view(now_ms)
    es = session.pet.language == "ES"
    _metric(draw, 40, "VALOR" if es else "VALUE", "%d > %d" % (real, projected), GREEN)
    _metric(draw, 54, "GANANCIA" if es else "GAIN", "+%d EV" % session.pending_ev, GREEN)
    _metric(draw, 68, "ENERGIA" if es else "ENERGY",
            "%d > %d" % (session.pet.get("e"), session.pet.get("e") - session.energy_reserved), MP)
    elapsed = max(0, now_ms - (session._animation_started_ms or 0))
    remaining = max(0, (TRAINING_ANIMATION_MS - elapsed + 999) // 1000)
    text(draw, (70, 87), tr(session.pet, "training.timed.remaining", remaining), YELLOW, small=True)
    bar(draw, 70, 103, 164, min(elapsed, TRAINING_ANIMATION_MS), TRAINING_ANIMATION_MS, GREEN, height=3)
    _action_button(draw, 4, 115, tr(session.pet, "training.timed.cancel"), YELLOW)
    if session.message:
        _feedback_band(draw, session.pet, session.message, color=HP)
    return frame


# ---------------------------------------------------------------------------
# Sub-state confirm
# ---------------------------------------------------------------------------


def _render_confirm(build_dir, session, now_ms):
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, 239, 19), fill=TEAL)
    text(draw, (26, 4), tr(session.pet, "training.confirm.title"))
    text(draw, (200, 4), tr(session.pet, "training.result.ok"), MUTED, small=True)
    stat = session._chosen_stat
    name = tr_stat(session.pet, stat)
    pet_sprite(frame, build_dir, 0, 30, 68, None, now_ms,
               species=session.pet.species, frame_interval_ms=75)
    info_label(frame, draw, _icon_name_for(stat), 70, 24,
               tr(session.pet, "training.confirm.x_rep", name, session.reps),
               YELLOW)
    real, projected = session.current_view(now_ms)
    _stat_pair(draw, session.pet, 70, 41, name, real, projected, WHITE)
    text(draw, (70, 57),
         tr(session.pet, "training.confirm.ev_added", session.pending_ev),
         GREEN, small=True)
    text(draw, (70, 72),
         tr(session.pet, "training.confirm.ene_delta", session.energy_reserved),
         HP, small=True)
    text(draw, (70, 87),
         tr(session.pet, "training.confirm.effort", session.reps * 8),
         MUTED, small=True)
    # Focus: CONFIRMAR (default) / SEGUIR.
    if session._focus == "confirm":
        _action_button(draw, 4, 115, tr(session.pet, "training.confirm.confirm"), YELLOW)
        _action_button(draw, 100, 115, tr(session.pet, "training.confirm.follow"), MUTED)
    else:
        _action_button(draw, 4, 115, tr(session.pet, "training.confirm.confirm"), MUTED)
        _action_button(draw, 100, 115, tr(session.pet, "training.confirm.follow"), YELLOW)
    return frame


# ---------------------------------------------------------------------------
# Sub-state cancel
# ---------------------------------------------------------------------------


def _render_cancel(build_dir, session, now_ms):
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, 239, 19), fill=HP)
    text(draw, (26, 4),
         tr(session.pet, "training.timed.cancel_title"), WHITE)
    text(draw, (24, 24), tr(session.pet, "training.cancel.body"), MUTED, small=True)
    # Two-option focus: SEGUIR (default) / DESCARTAR.
    if session._focus == "follow":
        _action_button(draw, 4, 115, tr(session.pet, "training.cancel.follow"), YELLOW)
        _action_button(draw, 100, 115, tr(session.pet, "training.cancel.discard"), HP)
    else:
        _action_button(draw, 4, 115, tr(session.pet, "training.cancel.follow"), MUTED)
        _action_button(draw, 100, 115, tr(session.pet, "training.cancel.discard"), YELLOW)
    return frame


# ---------------------------------------------------------------------------
# State D: result (two navigable pages: RESUMEN / STATS)
# ---------------------------------------------------------------------------


def _render_result(build_dir, session, now_ms):
    if getattr(session, "_result_page", "summary") == RESULT_PAGE_STATS:
        return _render_result_stats(build_dir, session, now_ms)
    return _render_result_summary(build_dir, session, now_ms)


def _render_result_summary(build_dir, session, now_ms):
    """Compact summary for the trained attribute: ANTES / CAMBIO / AHORA
    for stat-pool + EV + energy + effort, with the delta column shown
    only on rows that actually changed. The 6-stat overview lives on
    the next page (RESUMEN -> STATS via NEXT)."""
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, 239, 19), fill=GREEN)
    paste_icon(frame, asset_icon(build_dir, "Training"), 4, 2)
    text(draw, (26, 4), tr(session.pet, "training.result.title"))
    text(draw, (210, 4), tr(session.pet, "training.result.ok"), MUTED, small=True)
    # Pet on the left, idle animation.
    pet_sprite(frame, build_dir, 0, 30, 68, None, now_ms,
               species=session.pet.species, frame_interval_ms=75)
    summary = session._result_snapshot or {}
    stat = session._chosen_stat
    if stat is None:
        _render_result_empty(draw, session)
    else:
        idx = training_index_for(stat)
        name = TRAINING_TYPES[idx]["name"]
        local_name = tr_stat(session.pet, stat)
        ev_after = session.pet.ev_at(stat)
        ev_added = int(summary.get("ev_added", 0))
        ev_before = max(0, ev_after - ev_added)
        draw.rectangle((69, 23, 238, 101), outline=PANEL)
        for x in (121, 159, 199):
            draw.line((x, 23, x, 101), fill=PANEL)
        for y in (37, 53, 69, 85):
            draw.line((69, y, 238, y), fill=PANEL)
        spanish = session.pet.language == "ES"
        for x, heading in zip((124, 162, 202),
                              ("ANTES", "CAMBIO", "AHORA") if spanish
                              else ("BEFORE", "CHANGE", "AFTER")):
            text(draw, (x, 25), heading, MUTED, small=True)

        def row(y, label, before, change, after, color):
            for x, value in zip((72, 126, 164, 204),
                                (label, str(before), "%+d" % change, str(after))):
                text(draw, (x, y), value, color, small=True)
        # Stat pool row (HP/MP conversion applied).
        cs_before = combat_stat(session.pet.dna,
                                  {**session.pet.ev, stat: ev_before}, stat)
        cs_after = combat_stat(session.pet.dna, session.pet.ev, stat)
        before_pool, after_pool = _stat_pool(stat, cs_before, cs_after)
        delta = after_pool - before_pool
        row(40, local_name, before_pool, delta, after_pool, WHITE)
        row(56, tr(session.pet, "training.result.label.ev"),
            ev_before, ev_added, ev_after, GREEN)
        energy_charged = int(summary.get("energy_charged", 0))
        if energy_charged:
            row(72, tr(session.pet, "training.result.label.ene"),
                session.pet.get("e") + energy_charged, -energy_charged,
                session.pet.get("e"), HP)
        effort_added = int(summary.get("effort_added", 0))
        if effort_added:
            row(88, tr(session.pet, "training.result.label.effort"),
                max(0, session.pet.effort - effort_added), effort_added,
                session.pet.effort, MUTED)
    # Page indicator + CONTINUAR button.
    _page_indicator(draw, session, y=104)
    _result_buttons(draw, session)
    return frame


def _render_result_stats(build_dir, session, now_ms):
    """Six-attribute bar overview. Each row is the localized stat name
    plus a compact bar scaled to the post-train EV (capped at 252). The
    trained attribute is highlighted (yellow bar + YELLOW label); rows
    that did not change are drawn with the pre-train value and no
    delta column. The bar scale is documented below in
    :func:`_stat_bar_width`."""
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, 239, 19), fill=GREEN)
    paste_icon(frame, asset_icon(build_dir, "Training"), 4, 2)
    text(draw, (26, 4), tr(session.pet, "training.result.title"))
    text(draw, (210, 4), tr(session.pet, "training.result.ok"), MUTED, small=True)
    pet_sprite(frame, build_dir, 0, 30, 68, None, now_ms, frame_interval_ms=75)
    summary = session._result_snapshot or {}
    stat = session._chosen_stat
    # Column header for the stats page (a 6-row grid that lives in the
    # sprite area to the right of the pet).
    _page_indicator(draw, session, y=24)
    # Six rows: each row is 12 px tall starting at y=40. Last row ends
    # at y=40 + 5*12 + 10 = 110 (room for the action button at 115).
    trained = stat if stat is not None else None
    ev_after_total = dict(session.pet.ev)
    ev_before_total = dict(session.pet.ev)
    if trained is not None:
        ev_before_total[trained] = max(0, ev_after_total[trained] - int(summary.get("ev_added", 0)))
    rows_y = 40
    for i, item in enumerate(TRAINING_TYPES):
        s = item["stat"]
        ev_before = ev_before_total.get(s, 0)
        ev_after = ev_after_total.get(s, 0)
        local_name = tr_stat(session.pet, s)
        delta = ev_after - ev_before
        highlight = (s == trained)
        _stat_bar_row(draw, local_name, ev_before, ev_after, delta,
                       rows_y + i * 12, highlight=highlight)
    _result_buttons(draw, session)
    return frame


def _render_result_empty(draw, session):
    """Fallback when the chosen stat cannot be resolved (defensive)."""
    text(draw, (70, 40), tr(session.pet, "training.result.empty"), MUTED)


def pet_or_session(session):
    """Convenience for the helpers above: always pass the pet to tr()."""
    return session.pet


def _stat_pool(stat, cs_before, cs_after):
    """Apply the canonical HP / MP pool conversion. The renderer never
    invents a stat value: this delegates to the same conversion the
    domain uses for the summary table."""
    if stat == "hp":
        return 40 + cs_before * 2, 40 + cs_after * 2
    if stat == "mp":
        return 10 + cs_before, 10 + cs_after
    return cs_before, cs_after


def _stat_bar_width(ev, max_ev=252, max_width=96):
    """Scale an EV value to a pixel width.

    ``max_ev`` is the canonical cap (252). ``max_width`` is the
    horizontal span reserved for the bar in the stats page (96 px on
    the 240x135 frame, leaving room for the label + delta column).
    Values are clamped to ``[0, max_ev]`` so a malformed EV cannot
    overflow the bar."""
    if max_ev <= 0 or max_width <= 0:
        return 0
    clamped = max(0, min(int(ev), int(max_ev)))
    return int(round((clamped / float(max_ev)) * max_width))


def _stat_bar_row(draw, label, ev_before, ev_after, delta, y, highlight=False):
    """Render one row of the six-attribute overview. Layout in 240x135:

    * x=70..104 : localised stat name (up to 4 chars at the default font).
    * x=108..204: compact EV bar (96 px max width, 6 px tall).
    * x=208..236: delta value (only painted when there is a delta).
    """
    color = YELLOW if highlight else WHITE
    text(draw, (70, y), label[:4], color, small=True)
    width_before = _stat_bar_width(ev_before)
    width_after = _stat_bar_width(ev_after)
    # Outline + bar.
    draw.rectangle((108, y, 108 + 96, y + 6), outline=MUTED)
    if width_before > 0:
        draw.rectangle((108, y, 108 + width_before, y + 6), fill=MUTED)
    if width_after > 0:
        bar_color = YELLOW if highlight else GREEN
        draw.rectangle((108, y, 108 + width_after, y + 6), fill=bar_color)
    # Delta column: only paint when there was a change.
    if delta != 0:
        delta_color = YELLOW if highlight else GREEN
        text(draw, (208, y), "%+d" % delta, delta_color, small=True)
    else:
        text(draw, (208, y), "%d" % ev_after, MUTED, small=True)


def _page_indicator(draw, session, y=104):
    """Two-segment page indicator at the right of the result screen:
    ``RESUMEN | STATS`` with the active page painted in YELLOW. NEXT
    toggles the active page; the indicator is the only visual cue."""
    active = getattr(session, "_result_page", "summary")
    summary_color = YELLOW if active == "summary" else MUTED
    stats_color = YELLOW if active == "stats" else MUTED
    text(draw, (140, y),
         tr(session.pet, "training.result.page_summary"), summary_color, small=True)
    text(draw, (200, y),
         tr(session.pet, "training.result.page_stats"), stats_color, small=True)


# ---------------------------------------------------------------------------
# State E: error
# ---------------------------------------------------------------------------


def _render_error(build_dir, session, now_ms):
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, 239, 19), fill=HP)
    text(draw, (26, 4), tr(session.pet, "training.error.title"), WHITE)
    text(draw, (200, 4), "E", MUTED, small=True)
    text(draw, (24, 24), tr(session.pet, "training.error.body"), MUTED, small=True)
    if session._focus == "retry":
        _action_button(draw, 4, 115, tr(session.pet, "training.error.retry"), YELLOW)
        _action_button(draw, 100, 115, tr(session.pet, "training.error.discard"), HP)
    else:
        _action_button(draw, 4, 115, tr(session.pet, "training.error.retry"), MUTED)
        _action_button(draw, 100, 115, tr(session.pet, "training.error.discard"), YELLOW)
    return frame


# ---------------------------------------------------------------------------
# Shared action button + feedback band
# ---------------------------------------------------------------------------


def _result_buttons(draw, session):
    _action_button(draw, 4, 115, tr(session.pet, "training.timed.repeat"),
                   YELLOW if session._focus == "repeat" else MUTED)
    _action_button(draw, 100, 115, tr(session.pet, "training.prepare.back"),
                   YELLOW if session._focus == "back" else MUTED)
    color = YELLOW if session._focus == "stats" else MUTED
    draw.rectangle((196, 115, 239, 132), fill=INK, outline=color)
    text(draw, (200, 118), tr(session.pet, "training.result.page_stats"), color)


def _action_button(draw, x, y, label, color):
    """Render a small 90x18 inline button with the action label."""
    draw.rectangle((x, y, x + 89, y + 17), fill=INK, outline=color)
    text(draw, (x + 4, y + 3), label, color)


def _feedback_band(draw, pet, message, color=HP):
    """Persistent feedback band at y=99..110 (12 px)."""
    draw.rectangle((0, 99, 239, 110), fill=INK)
    text(draw, (6, 99), _block_label(pet, message), color, small=True)
