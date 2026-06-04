# STATE — TASK-CV-OFFLINE-LAB-STAGE-6-MANUAL-LABEL-CONFIRMATION-001

## Summary

Updated Stage 6 ground truth from `UNKNOWN_DECK` structural labels to manually confirmed `Gilded_*` card IDs.

## Confirmed Labels

```text
empty_to_empty: []
empty_to_one_card: Gilded_34
empty_to_three_cards: Gilded_54, Gilded_34, Gilded_73
one_card_to_three_cards: Gilded_54, Gilded_73
one_card_to_empty: Gilded_34
three_cards_to_empty: Gilded_54, Gilded_34, Gilded_73
```

## Evidence

Labels were confirmed by visual comparison of Stage 5 debug sheets against the Gilded reference deck contact sheet.

The mapping was not guessed from tarot memory; it was confirmed against repository reference images:

- `Gilded_34`: Gwiazda
- `Gilded_54`: Dziesiątka Kielichów
- `Gilded_73`: Siódemka Kielichów

## Ground Truth Status

`logs/live_fixtures/event_first_current_debug_verified/ground_truth.json` now has:

- `label_status`: `manual_confirmed`
- 10 labels
- 0 `UNKNOWN_DECK` labels

## Preflight Result

Status:

- `PASS`

## Required Next Action

Create `TASK-CV-OFFLINE-LAB-STAGE-6-CARD-IDENTIFICATION-BENCHMARK-001`.
