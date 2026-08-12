"""Dialogue de création/édition d'un filtre (groupe de paramètres nommé)."""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


class FilterDialog(QDialog):
    def __init__(
        self,
        all_param_names: List[str],
        parent=None,
        filter_name: str = "",
        selected_names: Optional[List[str]] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Filtre" if not filter_name else f"Modifier '{filter_name}'")
        self.resize(380, 480)

        selected_names = selected_names or []

        layout = QVBoxLayout(self)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Nom du filtre :"))
        self.name_edit = QLineEdit(filter_name)
        name_row.addWidget(self.name_edit)
        layout.addLayout(name_row)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Rechercher :"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filtrer la liste des paramètres...")
        self.search_edit.textChanged.connect(self._on_search)
        search_row.addWidget(self.search_edit)
        layout.addLayout(search_row)

        layout.addWidget(QLabel("Sélectionnez les paramètres à inclure dans ce filtre :"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.NoSelection)
        for pname in all_param_names:
            item = QListWidgetItem(pname)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if pname in selected_names else Qt.Unchecked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_search(self, text: str) -> None:
        text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text().lower())

    def _on_accept(self) -> None:
        if not self.name_edit.text().strip():
            self.name_edit.setFocus()
            return
        self.accept()

    def result_data(self) -> tuple[str, List[str]]:
        name = self.name_edit.text().strip()
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return name, selected
