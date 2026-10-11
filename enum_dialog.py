"""Dialogue de saisie des libellés d'une énumération (valeur -> libellé)."""
from __future__ import annotations

from typing import Dict, Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class EnumDialog(QDialog):
    def __init__(self, param_name: str, values: Iterable[int], labels: Dict[int, str], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Libellés — {param_name}")
        self.resize(380, 360)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Saisissez le texte affiché par MT5 pour chaque valeur.\n"
            "Ces libellés seront réutilisés pour tous les fichiers .set."
        ))

        values = sorted(set(values) | set(labels))
        self.table = QTableWidget(len(values), 2)
        self.table.setHorizontalHeaderLabels(["Valeur", "Libellé"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        for row, value in enumerate(values):
            value_item = QTableWidgetItem(str(value))
            value_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, value_item)
            self.table.setItem(row, 1, QTableWidgetItem(labels.get(value, "")))
        layout.addWidget(self.table)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def labels(self) -> Dict[int, str]:
        return {
            int(self.table.item(row, 0).text()): self.table.item(row, 1).text()
            for row in range(self.table.rowCount())
        }
