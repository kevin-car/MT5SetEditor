"""Gestion des filtres persistants (groupes de paramètres nommés).

Les filtres sont indépendants du fichier .set ouvert : une fois créés, ils
sont proposés pour n'importe quel fichier chargé par la suite (utile car les
mêmes EA ont souvent les mêmes noms de paramètres).
"""
from __future__ import annotations

import json
import os
from typing import Dict, List


def _config_dir() -> str:
    base = os.path.join(os.path.expanduser("~"), ".mt5_set_editor")
    os.makedirs(base, exist_ok=True)
    return base


def _config_path() -> str:
    return os.path.join(_config_dir(), "filters.json")


class FilterManager:
    def __init__(self) -> None:
        self.filters: Dict[str, List[str]] = {}
        self.load()

    def load(self) -> None:
        path = _config_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.filters = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.filters = {}
        else:
            self.filters = {}

    def save(self) -> None:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(self.filters, f, indent=2, ensure_ascii=False)

    def names(self) -> List[str]:
        return sorted(self.filters.keys())

    def get(self, name: str) -> List[str]:
        return self.filters.get(name, [])

    def set_filter(self, name: str, param_names: List[str]) -> None:
        self.filters[name] = list(param_names)
        self.save()

    def delete(self, name: str) -> None:
        if name in self.filters:
            del self.filters[name]
            self.save()

    def rename(self, old_name: str, new_name: str) -> None:
        if old_name in self.filters and old_name != new_name:
            self.filters[new_name] = self.filters.pop(old_name)
            self.save()
