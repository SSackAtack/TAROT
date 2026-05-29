from dataclasses import dataclass


PHASE_LOCKED = "locked_tracking"
PHASE_NEEDS_REVERIFY = "needs_reverify"


@dataclass
class TrackedCard:
    card_id: str
    phase: str
    x: float
    y: float
    angle: float
    confidence: float
    last_seen_frame: int
    reverify_reason: str | None = None


class TableState:
    def __init__(self, all_card_ids):
        self.all_card_ids = list(all_card_ids)
        self.cards = {}

    @property
    def available_card_ids(self):
        locked_ids = set(self.cards.keys())
        return [card_id for card_id in self.all_card_ids if card_id not in locked_ids]

    def upsert_locked(self, card_id, x, y, angle, confidence, frame_index):
        if card_id not in self.all_card_ids:
            raise ValueError(f"Unknown card id: {card_id}")
        self.cards[card_id] = TrackedCard(
            card_id=card_id,
            phase=PHASE_LOCKED,
            x=float(x),
            y=float(y),
            angle=float(angle),
            confidence=float(confidence),
            last_seen_frame=int(frame_index),
        )

    def mark_needs_reverify(self, card_id, reason):
        if card_id not in self.cards:
            return
        card = self.cards[card_id]
        card.phase = PHASE_NEEDS_REVERIFY
        card.reverify_reason = reason

    def remove_card(self, card_id):
        self.cards.pop(card_id, None)

    def correct_card_id(self, old_card_id, new_card_id):
        if new_card_id not in self.all_card_ids:
            raise ValueError(f"Unknown card id: {new_card_id}")
        if old_card_id not in self.cards:
            return
        old = self.cards.pop(old_card_id)
        self.cards[new_card_id] = TrackedCard(
            card_id=new_card_id,
            phase=old.phase,
            x=old.x,
            y=old.y,
            angle=old.angle,
            confidence=old.confidence,
            last_seen_frame=old.last_seen_frame,
            reverify_reason=old.reverify_reason,
        )
