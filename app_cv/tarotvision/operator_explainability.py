def _step(step_id, label, state, value, message):
    return {
        "id": step_id,
        "label": label,
        "state": state,
        "value": value,
        "message": message,
    }


def build_cv_explainability(cards, metrics, runtime, layout, operator, warnings):
    cards = cards or []
    metrics = metrics or {}
    runtime = runtime or {}
    layout = layout or {}
    operator = operator or {}
    warnings = warnings or []

    active_decks = operator.get("active_decks") or []
    layout_state = layout.get("state") or "unknown"
    table_status = runtime.get("table") if isinstance(runtime.get("table"), dict) else {}
    aruco_markers = runtime.get("aruco_markers", table_status.get("markers_detected", 0)) or 0
    aruco_calibrated = bool(runtime.get("aruco_calibrated", table_status.get("calibrated", False)))
    candidate_count = runtime.get("candidate_count", metrics.get("snapshot_quads_found"))
    if candidate_count is None:
        candidate_count = len(cards)

    steps = [
        _step(
            "decks",
            "Aktywne talie",
            "ok" if active_decks else "error",
            str(len(active_decks)),
            ", ".join(active_decks) if active_decks else "Brak aktywnej talii",
        ),
        _step(
            "aruco",
            "ArUco",
            "ok" if aruco_calibrated else "warn",
            f"{aruco_markers}/4",
            "Stol skalibrowany" if aruco_calibrated else "Pokaz markery ArUco w kadrze",
        ),
        _step(
            "snapshot",
            "Snapshot",
            "wait" if layout_state in {"settling", "sampling_snapshots", "analyzing_snapshot"} else "ok",
            layout_state,
            "Czeka na stabilny snapshot"
            if layout_state in {"settling", "sampling_snapshots", "analyzing_snapshot"}
            else "Snapshot gotowy",
        ),
        _step(
            "candidates",
            "Kandydaci kart",
            "ok" if candidate_count > 0 else "warn",
            str(candidate_count),
            "Wykryto kandydatow kart" if candidate_count > 0 else "Brak kandydatow kart",
        ),
        _step(
            "recognition",
            "Rozpoznanie",
            "ok" if cards else "wait",
            str(len(cards)),
            "Karty zaakceptowane" if cards else "Czeka na rozpoznanie",
        ),
    ]

    if not active_decks:
        severity = "error"
        next_action = "Wybierz 1-3 talie w Studio."
    elif layout_state == "no_camera":
        severity = "error"
        next_action = "Sprawdz kamere i launcher CV."
    elif not aruco_calibrated:
        severity = "warn"
        next_action = "Pokaz wszystkie markery ArUco w kadrze."
    elif layout_state in {"settling", "sampling_snapshots", "analyzing_snapshot"}:
        severity = "warn"
        next_action = "Zostaw mate nieruchomo przez kilka sekund."
    elif candidate_count < 1 and not cards:
        severity = "warn"
        next_action = "Popraw swiatlo, kontrast albo polozenie kart."
    elif cards:
        severity = "ok"
        next_action = "Mozna prowadzic sesje."
    else:
        severity = "warn"
        next_action = warnings[-1] if warnings else "Sprawdz diagnostyke CV."

    return {
        "severity": severity,
        "next_action": next_action,
        "steps": steps,
    }
