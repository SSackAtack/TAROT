"""Scoring logic for the Calibration Wizard session.

Evaluates table setup quality (lighting, card placement, reflections, performance)
based on samples collected in AutotuneSession.
"""

# Thresholds baseline
QUALITY_GOOD = 0.70
QUALITY_WARNING = 0.55

CONFIDENCE_GOOD_ONE_CARD = 0.75
CONFIDENCE_WARNING_ONE_CARD = 0.60

CONFIDENCE_GOOD_THREE_CARDS = 0.70
CONFIDENCE_WARNING_THREE_CARDS = 0.55

ANALYSIS_MS_GOOD = 750.0
ANALYSIS_MS_WARNING = 1500.0


def score_calibration_wizard_samples(samples_by_scenario: dict) -> dict:
    """Computes setup quality report based on collected samples."""
    report = {
        "score": 0.0,
        "grade": "bad",
        "ready_for_session": False,
        "sample_count": 0,
        "scenario_results": {},
        "operator_messages": [],
        "warnings": [],
        "blocking_issues": []
    }

    if not samples_by_scenario:
        report["operator_messages"].append("Brak zebranych danych do oceny.")
        return report

    active_scenarios = {
        sc: s for sc, s in samples_by_scenario.items() if s
    }

    if not active_scenarios:
        report["operator_messages"].append("Brak aktywnych scenariuszy w sesji.")
        return report

    total_samples = 0
    scenario_scores = []

    for scenario, samples in active_scenarios.items():
        total_samples += len(samples)
        res = _score_scenario(scenario, samples)
        report["scenario_results"][scenario] = res
        scenario_scores.append(res["score"])
        
        # Collect messages/warnings/issues from scenario
        report["warnings"].extend(res.get("warnings", []))
        report["blocking_issues"].extend(res.get("blocking_issues", []))
        if res.get("message"):
            report["operator_messages"].append(f"[{scenario}] {res['message']}")

    report["sample_count"] = total_samples

    # Overall score is average of scenario scores
    if scenario_scores:
        overall_score = sum(scenario_scores) / len(scenario_scores)
    else:
        overall_score = 0.0

    report["score"] = round(overall_score, 3)

    # Grade mapping
    if overall_score >= 0.90:
        report["grade"] = "excellent"
    elif overall_score >= 0.75:
        report["grade"] = "good"
    elif overall_score >= 0.55:
        report["grade"] = "warning"
    else:
        report["grade"] = "bad"

    # Readiness
    report["ready_for_session"] = (
        overall_score >= 0.75
        and len(report["blocking_issues"]) == 0
    )

    if report["ready_for_session"]:
        report["operator_messages"].append("Warunki sa wystarczajace do rozpoczecia sesji.")
    else:
        if report["blocking_issues"]:
            report["operator_messages"].append("Wykryto problemy blokujace rozpoczęcie sesji.")
        else:
            report["operator_messages"].append("Jakosć stanowiska jest zbyt niska na start sesji.")

    return report


def _score_scenario(scenario: str, samples: list) -> dict:
    """Scores a single scenario's samples and returns detailed metrics & messages."""
    metrics = _calculate_scenario_metrics(samples)
    score = 1.0
    warnings = []
    blocking_issues = []
    status = "ok"
    message = ""

    # Threshold checks and scoring
    if scenario == "empty":
        # Expecting accepted_count == 0
        if metrics["avg_accepted_count"] > 0:
            score = 0.0
            status = "bad"
            blocking_issues.append("Wykryto zaakceptowane karty w scenariuszu pustej maty.")
            message = "Pusta mata zawiera zaakceptowane karty."
        else:
            # Check false candidates (detected_count > 0 but accepted == 0)
            if metrics["avg_detected_count"] > 0:
                penalty = min(0.4, metrics["avg_detected_count"] * 0.15)
                score -= penalty
                warnings.append("Pusta mata generuje kandydatow kart. Sprawdz odbicia, kontrast maty albo cienie.")
                message = "Pusta mata generuje fałszywych kandydatów."
            
            # Check quality score
            if metrics["avg_snapshot_quality_score"] < QUALITY_GOOD:
                penalty = max(0.0, QUALITY_GOOD - metrics["avg_snapshot_quality_score"]) * 0.5
                score -= penalty
                if metrics["avg_snapshot_quality_score"] < QUALITY_WARNING:
                    warnings.append("Jakosc obrazu pustej maty jest niska. Popraw oswietlenie lub ostrosc.")
                    status = "bad"
                else:
                    warnings.append("Jakosc obrazu pustej maty mogłaby byc lepsza.")
                    status = "warning"
            
            if status == "ok" and not message:
                message = "Pusta mata zweryfikowana poprawnie."

    elif scenario in ("one_card", "three_cards"):
        expected = 1 if scenario == "one_card" else 3
        conf_good = CONFIDENCE_GOOD_ONE_CARD if scenario == "one_card" else CONFIDENCE_GOOD_THREE_CARDS
        conf_warning = CONFIDENCE_WARNING_ONE_CARD if scenario == "one_card" else CONFIDENCE_WARNING_THREE_CARDS

        # 1. Card Count Match
        if metrics["avg_accepted_count"] == 0:
            score = 0.0
            status = "bad"
            blocking_issues.append(f"Nie wykryto zadnych kart w scenariuszu {expected} kart.")
            message = f"Brak wykrytych kart (oczekiwano {expected})."
        elif metrics["avg_accepted_count"] < expected:
            ratio = metrics["avg_accepted_count"] / expected
            score *= ratio
            status = "warning"
            warnings.append(f"Wykryto tylko czesc kart: {metrics['avg_accepted_count']:.1f}/{expected}.")
            message = f"Wykryto za mało kart ({metrics['avg_accepted_count']:.1f}/{expected})."
        elif metrics["avg_accepted_count"] > expected:
            # False positives or multiple detections
            score *= 0.8
            status = "warning"
            warnings.append(f"Wykryto wiecej kart niz oczekiwano ({metrics['avg_accepted_count']:.1f}/{expected}).")
            message = "Wykryto za dużo kart."

        # 2. Confidence evaluation (only if cards were accepted)
        if metrics["avg_accepted_count"] > 0:
            avg_conf = metrics["avg_confidence"]
            if avg_conf < conf_good:
                penalty = max(0.0, conf_good - avg_conf) * 0.8
                score -= penalty
                if avg_conf < conf_warning:
                    status = "bad"
                    blocking_issues.append(
                        f"Niska pewnosc rozpoznawania kart (avg={avg_conf:.2f}). Popraw ostrosc lub swiatlo."
                    )
                    message = "Pewność rozpoznania poniżej krytycznego progu."
                else:
                    status = "warning"
                    warnings.append(
                        f"Pewnosc rozpoznawania kart mogłaby byc wyzsza (avg={avg_conf:.2f})."
                    )
                    if not message:
                        message = "Pewność rozpoznania jest niska."

        # 3. Rejections check
        total_rejections = (
            metrics["total_recognition_rejections"]
            + metrics["total_candidate_validation_rejections"]
        )
        if total_rejections > 0:
            avg_rejections = total_rejections / metrics["sample_count"]
            penalty = min(0.3, avg_rejections * 0.05)
            score -= penalty
            warnings.append("Pipeline czesto odrzuca kandydatow. Sprawdz kontrast karty wzgledem maty.")
            if not message:
                message = "Wykryto wysoki wskaźnik odrzuceń kandydatów."

        # 4. Latency
        if metrics["avg_analysis_ms"] > ANALYSIS_MS_GOOD:
            if metrics["avg_analysis_ms"] > ANALYSIS_MS_WARNING:
                score -= 0.15
                warnings.append(
                    f"Analiza ukladu {expected} kart jest bardzo wolna (avg={metrics['avg_analysis_ms']:.1f}ms)."
                )
            else:
                score -= 0.05
                warnings.append(
                    f"Analiza ukladu {expected} kart przekracza zalecany czas (avg={metrics['avg_analysis_ms']:.1f}ms)."
                )

        if status == "ok" and not message:
            message = f"Scenariusz {expected} kart zaliczony pomyslnie."

    if status == "warning":
        score = min(score, 0.74)
    elif status == "bad":
        score = min(score, 0.54)

    score = max(0.0, min(1.0, score))

    return {
        "score": round(score, 3),
        "status": status,
        "sample_count": metrics["sample_count"],
        "message": message,
        "metrics": metrics,
        "warnings": warnings,
        "blocking_issues": blocking_issues,
    }


def _calculate_scenario_metrics(samples: list) -> dict:
    """Safely calculates average and total metrics from a list of samples."""
    count = len(samples)
    if count == 0:
        return {
            "sample_count": 0,
            "avg_detected_count": 0.0,
            "avg_accepted_count": 0.0,
            "avg_analysis_ms": 0.0,
            "avg_snapshot_quality_score": 0.0,
            "avg_confidence": 0.0,
            "min_confidence": 0.0,
            "total_recognition_rejections": 0,
            "total_candidate_validation_rejections": 0,
        }

    detected_sum = 0
    accepted_sum = 0
    analysis_sum = 0.0
    quality_sum = 0.0
    confidence_sum = 0.0
    confidence_count = 0
    min_confidence = 1.0

    total_rec_rejections = 0
    total_val_rejections = 0

    for s in samples:
        detected_sum += int(s.get("detected_count", 0) or 0)
        accepted_sum += int(s.get("accepted_count", 0) or 0)
        analysis_sum += float(s.get("analysis_ms", 0.0) or 0.0)
        quality_sum += float(s.get("snapshot_quality_score", 0.0) or 0.0)
        
        # Confidences extraction
        confidences = s.get("recognition_confidences") or []
        for val in confidences:
            val_f = float(val)
            confidence_sum += val_f
            confidence_count += 1
            if val_f < min_confidence:
                min_confidence = val_f

        total_rec_rejections += int(s.get("recognition_rejections", 0) or 0)
        total_val_rejections += int(s.get("candidate_validation_rejections", 0) or 0)

    avg_confidence = confidence_sum / confidence_count if confidence_count > 0 else 0.0
    if confidence_count == 0:
        min_confidence = 0.0

    return {
        "sample_count": count,
        "avg_detected_count": round(detected_sum / count, 2),
        "avg_accepted_count": round(accepted_sum / count, 2),
        "avg_analysis_ms": round(analysis_sum / count, 2),
        "avg_snapshot_quality_score": round(quality_sum / count, 2),
        "avg_confidence": round(avg_confidence, 3),
        "min_confidence": round(min_confidence, 3),
        "total_recognition_rejections": total_rec_rejections,
        "total_candidate_validation_rejections": total_val_rejections,
    }
