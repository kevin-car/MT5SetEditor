"""Libellés des paramètres de type énumération.

Un fichier .set ne stocke que la valeur entière des énumérations : les libellés
affichés par MT5 viennent de l'EA compilé (.ex5, chiffré). On fournit donc les
libellés des énumérations standard MQL5 et on permet à l'utilisateur de définir
(une seule fois, globalement) ceux des énumérations propres à l'EA.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict

MA_METHODS = {0: "Simple", 1: "Exponential", 2: "Smoothed", 3: "Linear weighted"}
# Énumérations propres aux EA REB, connues à l'avance.
DEFAULT_ENUMS: Dict[str, Dict[int, str]] = {
    "Trade_Direction": {1: "Buy_And_Sell", 2: "Buy_Only", 3: "Sell_Only"},
}
_MA_METHOD_NAME = re.compile(r"methode?$", re.IGNORECASE)


def _config_path() -> str:
    base = os.path.join(os.path.expanduser("~"), ".mt5_set_editor")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "enums.json")


class EnumManager:
    def __init__(self) -> None:
        self.enums: Dict[str, Dict[int, str]] = {}
        self.load()

    def load(self) -> None:
        self.enums = {}
        path = _config_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        for name, labels in raw.items():
            if isinstance(labels, dict):
                self.enums[name] = {int(k): v for k, v in labels.items()}

    def save(self) -> None:
        data = {name: {str(k): v for k, v in sorted(labels.items())} for name, labels in self.enums.items()}
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, name: str) -> Dict[int, str]:
        """Libellés {valeur: libellé} triés par valeur ; vide si inconnus."""
        labels = self.enums.get(name, DEFAULT_ENUMS.get(name))
        if labels is None and _MA_METHOD_NAME.search(name):
            labels = MA_METHODS
        return dict(sorted((labels or {}).items()))

    def set_labels(self, name: str, labels: Dict[int, str]) -> None:
        cleaned = {k: v.strip() for k, v in labels.items() if v.strip()}
        if cleaned:
            self.enums[name] = cleaned
        else:
            self.enums.pop(name, None)
        self.save()
