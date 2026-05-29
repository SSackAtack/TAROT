"""Per-card confidence state machine for TarotVision.

Tracks how consistently a card identity is reported across frames.
A card progresses from 'empty' → 'candidate' → 'confirmed' after
enough consecutive high-confidence detections of the same identity.

This is a cleaner formalization of the debounce_state logic currently
in main.py.  It can be used per detection slot or per crop region.
"""

from dataclasses import dataclass


@dataclass
class CardState:
    """Current state of a card detection slot."""
    card_id: str | None
    phase: str           # 'empty', 'candidate', 'confirmed'
    frames: int          # consecutive frames at this identity
    confidence: float    # most recent confidence value


class CardStateMachine:
    """FSM tracking card identity stability over consecutive frames.

    Usage::

        fsm = CardStateMachine(confirm_frames=5, min_confidence=0.8)

        # Each frame, feed the best match for this slot:
        state = fsm.update(card_id="17_star", confidence=0.91)
        if state.phase == "confirmed":
            # Card identity is stable — safe to display
            ...

    Args:
        confirm_frames:  consecutive frames needed to move from
                          'candidate' to 'confirmed'.
        min_confidence:  minimum confidence to consider a detection
                          valid (below this → 'empty').
    """

    def __init__(self, confirm_frames=5, min_confidence=0.8):
        self.confirm_frames = confirm_frames
        self.min_confidence = min_confidence
        self.state = CardState(
            card_id=None, phase="empty", frames=0, confidence=0.0
        )

    def update(self, card_id, confidence):
        """Feed a new detection result and advance the FSM.

        Args:
            card_id:     detected card name (e.g. '17_star').
            confidence:  detection confidence score (0.0 – 1.0).

        Returns:
            Updated CardState.
        """
        if confidence < self.min_confidence:
            self.state = CardState(
                card_id=None, phase="empty", frames=0, confidence=confidence
            )
            return self.state

        if self.state.card_id == card_id:
            frames = self.state.frames + 1
        else:
            frames = 1

        phase = "confirmed" if frames >= self.confirm_frames else "candidate"
        self.state = CardState(
            card_id=card_id, phase=phase, frames=frames,
            confidence=confidence
        )
        return self.state
