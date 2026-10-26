"""Ten-second attribute training with an atomic completion transaction.

START reserves one repetition. Tick input completes it automatically; cancel
pauses the clock until the player resumes or discards. Failed saves keep the
draft for retry after rollback. The legacy confirmation state is retained for
compatibility, but the normal flow never enters it.
"""
from core.training import (TRAINING_TYPES, TRAINING_ENERGY_COST, TRAINING_EV_GAIN,
                            batch_block_reason, batch_max_reps, batch_plan_one_rep,
                            batch_projected_value, batch_commit, BatchSaveError)
from scripts.practice_session import PracticeSession

TRAINING_ANIMATION_MS = 10000

# State constants (used internally; the renderer reads ``session.state``).
STATE_SELECT = "select"
STATE_PREPARE = "prepare"
STATE_SESSION = "session"
STATE_CONFIRM = "confirm"
STATE_RESULT = "result"
STATE_CANCEL = "cancel"
STATE_ERROR = "error"


class TrainingSession:
    def __init__(self, pet, save):
        self.pet, self.save = pet, save
        # State A: the index walks the six attributes plus the
        # techniques entry and the back arrow. Backwards-compat with
        # the pre-batch dumbbell renderer is preserved: the same
        # index positions are used in state A.
        self.index = 0
        self.state = STATE_SELECT
        # Subset of training types: 0..5 are the six dumbbell
        # attributes; index 6 is the techniques entry (unchanged
        # behaviour, opened via ``PracticeSession(training=True)``);
        # index 7 is the back arrow (returns False from input).
        self._last_message = ""
        # State C/D buffers.
        self._chosen_stat = None
        self._chosen_index = None
        self._reps_completed = 0
        self._pending_ev = 0
        self._energy_reserved = 0
        self._focus = "train"  # "train" | "finalize" in state C
        # Animation marker: when set, the renderer shows the
        # TRAINING_TYPES animation for ``TRAINING_ANIMATION_MS`` and
        # blocks new rep input. The orchestrator reads ``busy`` to
        # decide whether to accept another ACTION.
        self._animation_started_ms = None
        self._paused_at_ms = None
        self._animation_index = None
        # Result snapshot for the D screen. Captured *after* a
        # successful commit so the renderer can show the diffs.
        self._result_snapshot = None
        # Result page toggle: "summary" (default) shows the focused
        # stat, EV and energy diffs; "stats" shows the full six-attribute
        # overview with the trained attribute highlighted. NEXT
        # cycles between the two; ACTION/BACK return to the selector.
        self._result_page = "summary"
        # Techniques sub-session is preserved.
        self.techniques = None
        # Pre-batch fields kept for backward compatibility with the
        # old dumbbell renderer (used by the previews); harmless if
        # unused.
        self.message = ""
        self.updated_at = None
        self.gain = None

    # ------------------------------------------------------------------
    # Public API used by sim.py and the renderer
    # ------------------------------------------------------------------

    def busy(self, now_ms):
        """True if a rep animation is currently in flight. ACTION is
        ignored while busy to debounce and prevent double-counted
        reps."""
        if self._animation_started_ms is None:
            return False
        return now_ms - self._animation_started_ms < TRAINING_ANIMATION_MS

    def animation_progress(self, now_ms):
        """0..1 fraction of the current rep animation, or None when
        no animation is active."""
        if self._animation_started_ms is None:
            return None
        elapsed = now_ms - self._animation_started_ms
        if elapsed >= TRAINING_ANIMATION_MS:
            return None
        return min(1.0, max(0.0, elapsed / TRAINING_ANIMATION_MS))

    @property
    def message(self):
        return self._last_message

    @message.setter
    def message(self, value):
        self._last_message = value or ""

    @property
    def reps(self):
        return self._reps_completed

    @property
    def energy_reserved(self):
        return self._energy_reserved

    @property
    def pending_ev(self):
        return self._pending_ev

    def current_view(self, now_ms):
        """Return the (real, projected) pair for the chosen stat using
        the current pending EV. ``real`` uses the pet's current EV;
        ``projected`` adds ``pending_ev`` capped at 252."""
        if self._chosen_stat is None:
            return None, None
        return batch_projected_value(self.pet, self._chosen_stat,
                                       self._pending_ev)

    def chosen_stat_label(self):
        if self._chosen_index is None:
            return ""
        return TRAINING_TYPES[self._chosen_index]["name"]

    def can_train_more(self):
        """True if the next rep would be accepted (energy, EV headroom
        including pending draft, eligibility). False when the queue
        is full or the next rep would cross the 252 cap."""
        if self._chosen_stat is None:
            return False
        plan = batch_plan_one_rep(self.pet, self._chosen_stat)
        if not plan["can"]:
            return False
        if self._energy_reserved + plan["energy_cost"] > self.pet.get("e"):
            return False
        if self.pet.ev_at(self._chosen_stat) + self._pending_ev >= self.pet.ev_limit():
            return False
        return True

    def train_block_reason(self):
        """Empty if a rep is possible, else a short reason string for
        the UI."""
        if self._chosen_stat is None:
            return "TIPO INVALIDO"
        plan = batch_plan_one_rep(self.pet, self._chosen_stat)
        if not plan["can"]:
            return plan["reason"]
        if self._energy_reserved + plan["energy_cost"] > self.pet.get("e"):
            return "FALTA ENERGIA"
        if self.pet.ev_at(self._chosen_stat) + self._pending_ev >= self.pet.ev_limit():
            return "EV AL MAXIMO"
        return ""

    def max_reps(self):
        """Maximum number of *additional* reps the player can queue
        in the current draft. Counts both the energy headroom and
        the EV headroom (real + pending), so the UI can show the
        total cap for the session."""
        if self._chosen_stat is None:
            return 0
        max_reps_total, reason = batch_max_reps(self.pet, self._chosen_stat)
        if reason:
            return 0
        # batch_max_reps uses ceiling for EV headroom; subtract the
        # already-queued reps. This is the remaining rep capacity.
        return max(0, max_reps_total - self._reps_completed)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def input(self, event, now_ms):
        # Techniques sub-session: delegated as before.
        if self.techniques is not None:
            if not self.techniques.input(event, now_ms):
                self.techniques = None
                # Stay in the same state (A) at the techniques entry.
            return True

        if self.state == STATE_SELECT:
            return self._input_select(event, now_ms)
        if self.state == STATE_PREPARE:
            return self._input_prepare(event, now_ms)
        if self.state == STATE_SESSION:
            return self._input_session(event, now_ms)
        if self.state == STATE_CONFIRM:
            return self._input_confirm(event, now_ms)
        if self.state == STATE_RESULT:
            return self._input_result(event, now_ms)
        if self.state == STATE_CANCEL:
            return self._input_cancel(event, now_ms)
        if self.state == STATE_ERROR:
            return self._input_error(event, now_ms)
        return True

    # ------------------------------------------------------------------
    # State A: select
    # ------------------------------------------------------------------

    def _input_select(self, event, now_ms):
        if event == "back":
            # No progress pending → exit to home.
            return False
        if event == "next":
            self.index = (self.index + 1) % (len(TRAINING_TYPES) + 2)
            self.message = ""
            return True
        if event != "action":
            return True
        # Techniques entry.
        if self.index == len(TRAINING_TYPES):
            self.techniques = PracticeSession(self.pet, self.save, training=True)
            return True
        # Back arrow.
        if self.index == len(TRAINING_TYPES) + 1:
            return False
        # Attribute chosen: validate and move to state B.
        stat = TRAINING_TYPES[self.index]["stat"]
        reason = batch_block_reason(self.pet, stat)
        if reason:
            self.message = reason
            return True
        self._chosen_index = self.index
        self._chosen_stat = stat
        self._reset_draft_buffer()
        self.state = STATE_PREPARE
        self._focus = "start"
        self.message = ""
        return True

    # ------------------------------------------------------------------
    # State B: prepare
    # ------------------------------------------------------------------

    def _input_prepare(self, event, now_ms):
        if event == "back":
            self._back_to_select()
            return True
        if event == "next":
            # Two-option focus toggle: INICIAR (default) <-> VOLVER.
            # The renderer reads ``self._focus`` to highlight the
            # active option.
            self._focus = "back" if self._focus == "start" else "start"
            return True
        if event != "action":
            return True
        if self._focus == "back":
            self._back_to_select()
            return True
        # INICIAR
        if self.max_reps() <= 0:
            self.message = self.train_block_reason() or "SIN REPS"
            return True
        self.state = STATE_SESSION
        plan = batch_plan_one_rep(self.pet, self._chosen_stat)
        self._reps_completed = 1
        self._pending_ev = plan["ev_added"]
        self._energy_reserved = plan["energy_cost"]
        self._animation_started_ms = now_ms
        self._animation_index = self._chosen_index
        self._paused_at_ms = None
        self._focus = "cancel"
        self.message = ""
        return True

    # ------------------------------------------------------------------
    # State C: session (queue reps)
    # ------------------------------------------------------------------

    def _input_session(self, event, now_ms):
        if self._animation_started_ms is not None:
            if now_ms - self._animation_started_ms >= TRAINING_ANIMATION_MS:
                return self._try_commit()
            if event in ("back", "action"):
                self._paused_at_ms = now_ms
                self.state = STATE_CANCEL
                self._focus = "follow"
            return True
        # An incomplete transient state cannot grant training rewards.
        self._back_to_select()
        return True

    # ------------------------------------------------------------------
    # State C→D sub-state: confirm
    # ------------------------------------------------------------------

    def _input_confirm(self, event, now_ms):
        # Focus: "continue" (default) <-> "confirm".
        if event == "back":
            self.state = STATE_SESSION
            self._focus = "finalize"
            return True
        if event == "next":
            self._focus = "confirm" if self._focus == "continue" else "continue"
            return True
        if event != "action":
            return True
        if self._focus == "continue":
            self.state = STATE_SESSION
            self._focus = "finalize"
            return True
        # CONFIRMAR
        if self._reps_completed <= 0:
            self.state = STATE_SESSION
            return True
        return self._try_commit()

    def _try_commit(self):
        """Atomic commit. On success move to state D; on failure
        restore the pet, move to state E, keep the draft intact so
        the player can retry or discard."""
        stat = self._chosen_stat
        if stat is None:
            self.state = STATE_RESULT
            return True
        # Re-validate the draft against the current pet state.
        plan = batch_plan_one_rep(self.pet, stat)
        if not plan["can"]:
            self.message = plan["reason"] or "BLOQUEADO"
            self.state = STATE_ERROR
            self._focus = "retry"
            return True
        try:
            summary = batch_commit(self.pet, stat, self._reps_completed,
                                       self.save, learn=True)
        except BatchSaveError as exc:
            self.message = "NO SE GUARDO"
            self.state = STATE_ERROR
            self._focus = "retry"
            return True
        self._result_snapshot = summary
        self.state = STATE_RESULT
        self._focus = "repeat" if batch_plan_one_rep(self.pet, stat)["can"] else "back"
        self._result_page = "summary"
        return True

    # ------------------------------------------------------------------
    # State D: result
    # ------------------------------------------------------------------

    def _input_result(self, event, now_ms):
        choices = ["repeat", "back", "stats"] if batch_plan_one_rep(self.pet, self._chosen_stat)["can"] else ["back", "stats"]
        if event == "next":
            self._focus = choices[(choices.index(self._focus) + 1) % len(choices)] if self._focus in choices else choices[0]
            return True
        if event == "back" or (event == "action" and self._focus == "back"):
            self._back_to_select()
        elif event == "action" and self._focus == "repeat" and "repeat" in choices:
            self._reset_draft_buffer()
            self.state = STATE_PREPARE
            self._focus = "start"
        elif event == "action" and self._focus == "stats":
            self._result_page = "summary" if self._result_page == "stats" else "stats"
        return True

    # ------------------------------------------------------------------
    # State E: cancel confirm
    # ------------------------------------------------------------------

    def _input_cancel(self, event, now_ms):
        # Focus: "follow" (SEGUIR) <-> "discard" (DESCARTAR). Default
        # is SEGUIR for safety.
        if event == "back":
            self._resume_timer(now_ms)
            self.state = STATE_SESSION
            return True
        if event == "next":
            self._focus = "discard" if self._focus == "follow" else "follow"
            return True
        if event != "action":
            return True
        if self._focus == "follow":
            self._resume_timer(now_ms)
            self.state = STATE_SESSION
            self._focus = "cancel"
            return True
        # DESCARTAR
        self._reset_full()
        self.state = STATE_SELECT
        self._focus = "train"
        return True

    # ------------------------------------------------------------------
    # State E: error retry
    # ------------------------------------------------------------------

    def _input_error(self, event, now_ms):
        # Focus: "retry" (REINTENTAR) <-> "discard" (DESCARTAR).
        # Default is REINTENTAR.
        if event == "back":
            self._focus = "retry"
            return True
        if event == "next":
            self._focus = "discard" if self._focus == "retry" else "retry"
            return True
        if event != "action":
            return True
        if self._focus == "retry":
            return self._try_commit()
        # DISCARD
        self._reset_full()
        self.state = STATE_SELECT
        self._focus = "train"
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _back_to_select(self):
        self._reset_full()
        self.state = STATE_SELECT
        self._focus = "train"
        self._result_page = "summary"

    def _reset_draft_buffer(self):
        """Reset the in-progress batch (reps, pending EV, reservation)
        while keeping the chosen attribute. Used when entering a new
        attribute from state A."""
        self._reps_completed = 0
        self._pending_ev = 0
        self._energy_reserved = 0
        self._animation_started_ms = None
        self._paused_at_ms = None
        self._animation_index = None
        self._result_snapshot = None
        self.message = ""

    def _reset_full(self):
        """Full reset including the chosen attribute. Used when
        returning to state A after a finalise, cancel, or error
        discard."""
        self._reset_draft_buffer()
        self._chosen_stat = None
        self._chosen_index = None
    def _resume_timer(self, now_ms):
        if self._paused_at_ms is not None and self._animation_started_ms is not None:
            self._animation_started_ms += now_ms - self._paused_at_ms
        self._paused_at_ms = None
