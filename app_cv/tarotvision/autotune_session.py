"""State container for live autotuning sessions."""


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

    def status(self):
        return {
            "state": self.state,
            "progress": {
                scenario: f"{len(self.samples[scenario])}/{self.samples_per_scenario}"
                for scenario in self.required_scenarios
            },
            "recommendation": self.recommendation,
        }
