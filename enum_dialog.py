"""Dialogue de gestion des labels d'enumerations."""
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
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from enum_manager import EnumManager


class EnumDialog(QDialog):
    """Permet d'ajouter/editer/supprimer les labels d'un parametre enum."""

    def __init__(
        self,
        all_param_names: List[str],
        enum_manager: EnumManager,
        parent=None,
        current_param: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Labels d'enumerations")
        self.resize(420, 480)

        self.enum_manager = enum_manager
        self.all_param_names = all_param_names

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Parametres avec labels :"))
        self.list_widget = QListWidget()
        self.list_widget.currentTextChanged.connect(self._on_selected_changed)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.btn_new = QPushButton("Nouveau")
        self.btn_delete = QPushButton("Supprimer")
        self.btn_new.clicked.connect(self._new_enum)
        self.btn_delete.clicked.connect(self._delete_enum)
        btn_row.addWidget(self.btn_new)
        btn_row.addWidget(self.btn_delete)
        layout.addLayout(btn_row)

        layout.addWidget(QLabel("Nom du parametre :"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Labels (un par ligne, dans l'ordre des valeurs 0,1,2...) :"))
        self.labels_edit = QTextEdit()
        layout.addWidget(self.labels_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self._refresh_list()
        if current_param:
            items = self.list_widget.findItems(current_param, Qt.MatchExactly)
            if items:
                self.list_widget.setCurrentItem(items[0])
            else:
                self._new_enum(current_param)
        elif self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def _refresh_list(self) -> None:
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for name in self.enum_manager.names():
            self.list_widget.addItem(name)
        self.list_widget.blockSignals(False)

    def _on_selected_changed(self, text: str) -> None:
        if not text:
            return
        self.name_edit.setText(text)
        self.labels_edit.setPlainText("\n".join(self.enum_manager.get(text)))

    def _on_selection_changed(self) -> None:
        has_selection = bool(self.list_widget.selectedItems())
        self.btn_delete.setEnabled(has_selection)

    def _new_enum(self, name: str = "") -> None:
        if name and isinstance(name, str):
            self.name_edit.setText(name)
        else:
            self.name_edit.clear()
        self.labels_edit.clear()
        self.list_widget.clearSelection()
        self.name_edit.setFocus()

    def _delete_enum(self) -> None:
        current = self.list_widget.currentItem()
        if not current:
            return
        name = current.text()
        if QMessageBox.question(self, "Confirmer", f"Supprimer les labels pour '{name}' ?") == QMessageBox.Yes:
            self.enum_manager.delete(name)
            self._refresh_list()
            self._new_enum()

    def _on_accept(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Nom manquant", "Entrez un nom de parametre.")
            return
        labels = [line.strip() for line in self.labels_edit.toPlainText().splitlines() if line.strip()]
        if not labels:
            QMessageBox.warning(self, "Labels manquants", "Entrez au moins un label.")
            return
        self.enum_manager.set_enum(name, labels)
        self.accept()
