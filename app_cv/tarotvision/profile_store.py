import json
import os
import re

from tarotvision.runtime_config import PARAMETERS, RuntimeConfig, ParameterValidationError


SAFE_PROFILE_NAME = re.compile(r"^[a-zA-Z0-9_-]+$")


class ProfileStore:
    def __init__(self, directory):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _path_for(self, name):
        if not SAFE_PROFILE_NAME.match(name):
            raise ValueError(f"Invalid profile name: {name}")
        return os.path.join(self.directory, f"{name}.json")

    def save(self, name, values):
        unknown = [param for param in values if param not in PARAMETERS]
        if unknown:
            raise ValueError(f"Unknown profile parameters: {unknown}")
        path = self._path_for(name)
        with open(path, "w", encoding="utf-8") as profile_file:
            json.dump(values, profile_file, indent=2, sort_keys=True)

    def load(self, name):
        path = self._path_for(name)
        with open(path, "r", encoding="utf-8") as profile_file:
            return json.load(profile_file)

    def load_parameters(self, name):
        profile = self.load(name)
        if isinstance(profile, dict) and "parameters" in profile:
            return profile["parameters"]
        return profile

    def save_autotune_recommendation(self, name, recommendation):
        parameters = recommendation.get("profile") or recommendation.get("parameters") or {}
        validated_parameters = self._validate_parameters(parameters)
        profile_payload = {
            "name": name,
            "parameters": validated_parameters,
            "source": "autotune",
            "score": recommendation.get("score"),
            "confidence": recommendation.get("confidence", "LOW"),
        }
        path = self._path_for(name)
        with open(path, "w", encoding="utf-8") as profile_file:
            json.dump(profile_payload, profile_file, indent=2, sort_keys=True)

    def _validate_parameters(self, values):
        config = RuntimeConfig()
        validated = {}
        try:
            for param_name, value in values.items():
                config.update(param_name, value)
                validated[param_name] = config.values[param_name]
        except ParameterValidationError as exc:
            raise ValueError(str(exc)) from exc
        return validated
