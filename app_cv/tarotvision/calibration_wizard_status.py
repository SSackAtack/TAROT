"""Defensive status builder for the Calibration Wizard session.

Ensures that the calibration.autotune payload has a consistent,
complete, JSON-safe structure under both idle and active sessions.
"""

def build_calibration_wizard_status(
    session=None,
    quality_report=None,
    *,
    default_required_count=3,
) -> dict:
    """Builds a complete and stable status payload dictionary."""
    # Base defaults
    scenario = None
    state = "idle"
    collected_count = 0
    required_count = default_required_count
    ready_to_score = False
    recommendation = None
    last_score = None
    next_action = "Rozpocznij autotuning z poziomu konsoli."

    # Session processing (defensive checks)
    if session is not None:
        # Scenario
        if hasattr(session, "current_scenario"):
            if callable(session.current_scenario):
                try:
                    scenario = session.current_scenario()
                except Exception:
                    scenario = None
            else:
                scenario = session.current_scenario

        # State
        if hasattr(session, "state"):
            state = session.state
        else:
            state = "collecting"

        # Collected count
        if scenario is not None and hasattr(session, "samples"):
            try:
                samples_list = session.samples.get(scenario)
                if samples_list is not None:
                    collected_count = len(samples_list)
            except Exception:
                collected_count = 0

        # Required count
        if hasattr(session, "samples_per_scenario"):
            try:
                required_count = int(session.samples_per_scenario)
            except Exception:
                required_count = default_required_count

        # Ready to score
        if hasattr(session, "ready_to_score"):
            if callable(session.ready_to_score):
                try:
                    ready_to_score = bool(session.ready_to_score())
                except Exception:
                    ready_to_score = False
            else:
                ready_to_score = bool(session.ready_to_score)

        # Recommendation
        if hasattr(session, "recommendation"):
            recommendation = session.recommendation

        if recommendation is not None and isinstance(recommendation, dict):
            try:
                last_score = recommendation.get("score")
            except Exception:
                last_score = None

        # Next action
        if hasattr(session, "next_action"):
            if callable(session.next_action):
                try:
                    next_action = session.next_action()
                except Exception:
                    next_action = "W toku."
            else:
                next_action = session.next_action
        else:
            next_action = "W toku."

    # Quality report processing (defensive checks)
    ready_for_session = False
    current_step_ready = False
    overall_wizard_ready = False  # Hardcoded to False at this stage
    operator_messages = []
    warnings = []
    blocking_issues = []

    if quality_report is not None and isinstance(quality_report, dict):
        try:
            ready_for_session = bool(quality_report.get("ready_for_session", False))
        except Exception:
            ready_for_session = False

        current_step_ready = ready_for_session

        try:
            msg_list = quality_report.get("operator_messages")
            if msg_list is not None:
                operator_messages = list(msg_list)
        except Exception:
            operator_messages = []

        try:
            warn_list = quality_report.get("warnings")
            if warn_list is not None:
                warnings = list(warn_list)
        except Exception:
            warnings = []

        try:
            issue_list = quality_report.get("blocking_issues")
            if issue_list is not None:
                blocking_issues = list(issue_list)
        except Exception:
            blocking_issues = []

    return {
        "schema_version": 1,
        "mode": "calibration_wizard",
        "scenario": scenario,
        "state": state,
        "collected_count": collected_count,
        "required_count": required_count,
        "ready_to_score": ready_to_score,
        "quality_report": quality_report,
        "ready_for_session": ready_for_session,
        "current_step_ready": current_step_ready,
        "overall_wizard_ready": overall_wizard_ready,
        "operator_messages": operator_messages,
        "warnings": warnings,
        "blocking_issues": blocking_issues,
        "recommendation": recommendation,
        "last_score": last_score,
        "next_action": next_action,
    }
