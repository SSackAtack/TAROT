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
    bbox: tuple[int, int, int, int] | None = None


class TableState:
    def __init__(self, all_card_ids):
        self.all_card_ids = list(all_card_ids)
        self.cards = {}

    @property
    def available_card_ids(self):
        locked_ids = set(self.cards.keys())
        return [card_id for card_id in self.all_card_ids if card_id not in locked_ids]

    def clear(self):
        self.cards.clear()

    def upsert_locked(self, card_id, x, y, angle, confidence, frame_index, bbox=None):
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
            bbox=_normalize_bbox(bbox),
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
            bbox=old.bbox,
        )

    def remove_cards_intersecting_bbox(self, bbox, min_iou=0.10):
        target_bbox = _normalize_bbox(bbox)
        removed = []
        for card_id, card in list(self.cards.items()):
            if card.bbox is None:
                continue
            if _bbox_iou(card.bbox, target_bbox) >= float(min_iou):
                removed.append(card_id)
                self.remove_card(card_id)
        return removed

    def mark_cards_intersecting_bbox_needs_reverify(self, bbox, reason, min_iou=0.10):
        target_bbox = _normalize_bbox(bbox)
        marked = []
        for card_id, card in self.cards.items():
            if card.bbox is None:
                continue
            if _bbox_iou(card.bbox, target_bbox) >= float(min_iou):
                card.phase = PHASE_NEEDS_REVERIFY
                card.reverify_reason = reason
                marked.append(card_id)
        return marked

    def to_layout_cards(self):
        layout_cards = []
        for card in self.cards.values():
            payload = {
                "name": card.card_id,
                "x": card.x,
                "y": card.y,
                "angle": card.angle,
                "confidence": card.confidence,
                "phase": card.phase,
            }
            if card.bbox is not None:
                payload["bbox"] = list(card.bbox)
            if card.reverify_reason is not None:
                payload["reverify_reason"] = card.reverify_reason
            layout_cards.append(payload)
        return layout_cards


def _normalize_bbox(bbox):
    if bbox is None:
        return None
    x, y, w, h = bbox
    return int(x), int(y), int(w), int(h)


def _bbox_iou(first, second):
    if first is None or second is None:
        return 0.0
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    ax2 = ax + aw
    ay2 = ay + ah
    bx2 = bx + bw
    by2 = by + bh

    inter_x1 = max(ax, bx)
    inter_y1 = max(ay, by)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    intersection = float(inter_w * inter_h)
    union = float(aw * ah + bw * bh) - intersection
    if union <= 0.0:
        return 0.0
    return intersection / union
