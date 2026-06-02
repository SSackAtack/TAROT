def _step(step_id, label, state, value, message):
    return {
        "id": step_id,
        "label": label,
        "state": state,
        "value": value,
        "message": message,
    }


def _current_aruco_marker_count(runtime, table_status):
    if "aruco_markers" in runtime:
        return int(runtime.get("aruco_markers") or 0)
    marker_ids = table_status.get("marker_ids")
    if isinstance(marker_ids, list):
        return len(marker_ids)
    return int(table_status.get("markers_detected", 0) or 0)


def _metric_int(metrics, key, fallback=0):
    try:
        return int(round(float(metrics.get(key, fallback) or 0)))
    except (TypeError, ValueError):
        return int(fallback)


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
    aruco_markers = _current_aruco_marker_count(runtime, table_status)
    aruco_calibrated = bool(runtime.get("aruco_calibrated", table_status.get("calibrated", False)))
    aruco_fully_visible = aruco_markers >= 4
    aruco_step_state = "ok" if aruco_calibrated and aruco_fully_visible else "warn"
    if aruco_calibrated and aruco_fully_visible:
        aruco_message = "Stol skalibrowany"
    elif aruco_calibrated:
        aruco_message = "Uzywam ostatniej kalibracji; pokaz markery ArUco"
    else:
        aruco_message = "Pokaz markery ArUco w kadrze"
    candidate_count = runtime.get("candidate_count", metrics.get("snapshot_quads_found"))
    if candidate_count is None:
        candidate_count = len(cards)
    candidate_count = int(candidate_count)
    accepted_count = len(cards)
    rejected_count = max(0, candidate_count - accepted_count)
    has_candidate_gap = candidate_count > accepted_count and accepted_count > 0
    validation_rejections = _metric_int(metrics, "snapshot_candidate_validation_rejections")
    if has_candidate_gap and validation_rejections > 0:
        recognition_message = (
            f"Zaakceptowano {accepted_count}, odrzucono {rejected_count}; "
            f"{validation_rejections} bez cech karty"
        )
    elif has_candidate_gap:
        recognition_message = f"Zaakceptowano {accepted_count}, odrzucono {rejected_count}"
    elif cards:
        recognition_message = "Karty zaakceptowane"
    else:
        recognition_message = "Czeka na rozpoznanie"

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
            aruco_step_state,
            f"{aruco_markers}/4",
            aruco_message,
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
            "warn" if has_candidate_gap else ("ok" if cards else "wait"),
            f"{accepted_count}/{candidate_count}" if candidate_count else str(accepted_count),
            recognition_message,
        ),
    ]

    if not active_decks:
        severity = "error"
        next_action = "Wybierz 1-3 talie w Studio."
    elif layout_state == "no_camera":
        severity = "error"
        next_action = "Sprawdz kamere i launcher CV."
    elif not aruco_calibrated or not aruco_fully_visible:
        severity = "warn"
        next_action = "Pokaz wszystkie markery ArUco w kadrze."
    elif layout_state in {"settling", "sampling_snapshots", "analyzing_snapshot"}:
        severity = "warn"
        next_action = "Zostaw mate nieruchomo przez kilka sekund."
    elif candidate_count < 1 and not cards:
        severity = "warn"
        next_action = "Popraw swiatlo, kontrast albo polozenie kart."
    elif has_candidate_gap:
        severity = "warn"
        if validation_rejections > 0:
            next_action = "Odrzucony kandydat wyglada jak odblask albo tlo: zmniejsz refleks i sprawdz separacje karty."
        else:
            next_action = "Jedna karta wymaga poprawy rozpoznania: popraw swiatlo, kontrast albo odsun karte od innych."
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
