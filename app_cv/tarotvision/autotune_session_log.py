"""Persistent JSON logging for live autotuning operator sessions."""

import json
import os
import time


class AutotuneSessionLog:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def write_event(
        self,
        event,
        session,
        active_decks=None,
        runtime_parameters=None,
        recommendation=None,
        profile_name=None,
    ):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_suffix = time.time_ns()
        scenario = session.current_scenario() or "unknown"
        filename = f"autotune_{timestamp}_{unique_suffix}_{scenario}_{event}.json"
        path = os.path.join(self.log_dir, filename)
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "event": event,
            "active_decks": list(active_decks or []),
            "runtime_parameters": dict(runtime_parameters or {}),
            "status": session.status(),
            "samples": {
                scenario_id: [dict(sample) for sample in samples]
                for scenario_id, samples in session.samples.items()
            },
            "recommendation": recommendation if recommendation is not None else session.recommendation,
            "profile_name": profile_name,
        }
        with open(path, "w", encoding="utf-8") as log_file:
            json.dump(payload, log_file, ensure_ascii=False, indent=2)
        return path
