import json
import os
import re

from tarotvision.runtime_config import PARAMETERS


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
