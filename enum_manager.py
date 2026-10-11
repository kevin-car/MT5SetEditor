"""Gestion des labels d'énumerations persistants.

Un fichier .set ne stocke que des entiers pour les parametres de type enum.
Ces mappings permettent d'afficher et d'editer les labels (ex: Trade_Direction).
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional


def _config_dir() -> str:
    base = os.path.join(os.path.expanduser("~"), ".mt5_set_editor")
    os.makedirs(base, exist_ok=True)
    return base


def _config_path() -> str:
    return os.path.join(_config_dir(), "enums.json")


class EnumManager:
    def __init__(self) -> None:
        self.enums: Dict[str, List[str]] = {}
        self.load()

    def load(self) -> None:
        path = _config_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.enums = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.enums = {}
        else:
            self.enums = {}
        self.enums.setdefault(
            "Trade_Direction",
            ["Buy_And_Sell", "Buy_Only", "Sell_Only"],
        )

    def save(self) -> None:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(self.enums, f, indent=2, ensure_ascii=False)

    def names(self) -> List[str]:
        return sorted(self.enums.keys())

    def get(self, name: str) -> List[str]:
        return self.enums.get(name, [])

    def set_enum(self, name: str, labels: List[str]) -> None:
        cleaned = [label.strip() for label in labels if label.strip()]
        if cleaned:
            self.enums[name] = cleaned
        elif name in self.enums:
            del self.enums[name]
        self.save()

    def delete(self, name: str) -> None:
        if name in self.enums:
            del self.enums[name]
            self.save()
