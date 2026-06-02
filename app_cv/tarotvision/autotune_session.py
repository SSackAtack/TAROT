"""State container for live autotuning sessions."""


SCENARIO_LABELS = {
    "empty": "pusta mata",
    "one_card": "1 karta",
    "three_cards": "3 karty",
}


class AutotuneSession:
    def __init__(self, required_scenarios=("empty", "one_card", "three_cards"), samples_per_scenario=3):
        self.required_scenarios = tuple(required_scenarios)
        self.samples_per_scenario = int(samples_per_scenario)
        self.samples = {scenario: [] for scenario in self.required_scenarios}
        self.state = "collecting"
        self.recommendation = None

    def add_sample(self, scenario, sample):
        if scenario not in self.samples:
            raise ValueError(f"Unknown autotune scenario: {scenario}")
        if len(self.samples[scenario]) < self.samples_per_scenario:
            self.samples[scenario].append(dict(sample))
        if self.ready_to_score():
            self.state = "ready_to_score"

    def ready_to_score(self):
        return all(
            len(self.samples[scenario]) >= self.samples_per_scenario
            for scenario in self.required_scenarios
        )

    def all_samples(self):
        result = []
        for scenario, samples in self.samples.items():
            for sample in samples:
                sample_copy = dict(sample)
                sample_copy["scenario"] = scenario
                result.append(sample_copy)
        return result

    def set_recommendation(self, recommendation):
        self.recommendation = recommendation
        self.state = "recommendation_ready"

    def current_scenario(self):
        return self.required_scenarios[0] if self.required_scenarios else None

    def stage_result(self):
        scenario = self.current_scenario()
        if scenario is None:
            return {"state": "WAIT", "message": "Brak aktywnego scenariusza."}

        samples = self.samples.get(scenario, [])
        if len(samples) < self.samples_per_scenario:
            return {
                "state": "COLLECTING",
                "message": (
                    f"Zbieram probki: {SCENARIO_LABELS.get(scenario, scenario)} "
                    f"({len(samples)}/{self.samples_per_scenario})."
                ),
            }

        checks = [_sample_passes_scenario(scenario, sample) for sample in samples]
        if all(checks):
            return {
                "state": "PASS",
                "message": _pass_message(scenario),
            }
        return {
            "state": "FAIL",
            "message": _fail_message(scenario),
        }

    def next_action(self):
        result = self.stage_result()
        if result["state"] == "COLLECTING":
            return "Nie ruszaj stolu, czekam na stabilne snapshoty."
        if result["state"] == "FAIL":
            return "Kliknij Skalibruj albo popraw swiatlo/mate."
        scenario = self.current_scenario()
        if scenario == "empty":
            return "Przejdz do testu 1 karta."
        if scenario == "one_card":
            return "Przejdz do testu 3 karty."
        if scenario == "three_cards":
            return "Kliknij Save Profile, jesli warunki sa poprawne."
        return "Sprawdz kolejny etap kalibracji."

    def status(self):
        return {
            "state": self.state,
            "scenario": self.current_scenario(),
            "progress": {
                scenario: f"{len(self.samples[scenario])}/{self.samples_per_scenario}"
                for scenario in self.required_scenarios
            },
            "stage_result": self.stage_result(),
            "next_action": self.next_action(),
            "recommendation": self.recommendation,
        }


def _sample_passes_scenario(scenario, sample):
    candidate_count = int(sample.get("candidate_count", 0))
    accepted_count = int(sample.get("accepted_count", 0))
    false_positive_count = int(sample.get("false_positive_count", 0))
    validation_rejections = int(sample.get("candidate_validation_rejections", 0))
    recognition_rejections = int(sample.get("recognition_rejections", 0))

    if scenario == "empty":
        return candidate_count == 0 and accepted_count == 0 and false_positive_count == 0
    if scenario == "one_card":
        return (
            candidate_count == 1
            and accepted_count == 1
            and validation_rejections == 0
            and recognition_rejections == 0
        )
    if scenario == "three_cards":
        return candidate_count >= 3 and accepted_count >= 3 and validation_rejections == 0
    return False


def _pass_message(scenario):
    if scenario == "empty":
        return "Pusta mata poprawna: system nie widzi kart ani kandydatow."
    if scenario == "one_card":
        return "1 karta poprawna: wykryto i zaakceptowano jedna karte."
    if scenario == "three_cards":
        return "3 karty poprawne: wykryto i zaakceptowano uklad trzech kart."
    return "Etap poprawny."


def _fail_message(scenario):
    if scenario == "empty":
        return "Pusta mata FAIL: wykryto false positive na macie."
    if scenario == "one_card":
        return "1 karta FAIL: system nie zaakceptowal dokladnie jednej karty."
    if scenario == "three_cards":
        return "3 karty FAIL: system nie zaakceptowal wszystkich 3 kart."
    return "Etap kalibracji FAIL."
