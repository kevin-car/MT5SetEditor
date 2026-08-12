"""Fenêtre principale de l'éditeur de fichiers .set MetaTrader 5."""
from __future__ import annotations

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from filter_dialog import FilterDialog
from filter_manager import FilterManager
from set_parser import Parameter, SetFile

ALL_FILTER = "Tous les paramètres"

COL_NAME = 0
COL_VALUE = 1
COL_DEFAULT = 2
COL_MIN = 3
COL_MAX = 4
COL_OPTIMIZE = 5
COLUMNS = ["Paramètre", "Valeur", "Défaut", "Min", "Max", "Optimiser"]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Éditeur de fichiers .set MT5")
        self.resize(1100, 700)

        self.set_file: Optional[SetFile] = None
        self.current_path: Optional[str] = None
        self.filter_manager = FilterManager()

        self._build_ui()
        self._build_menu()
        self._refresh_filter_list()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Horizontal)

        # -- Panneau gauche : filtres --
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Filtres"))

        self.filter_list = QListWidget()
        self.filter_list.currentTextChanged.connect(self._on_filter_selected)
        left_layout.addWidget(self.filter_list)

        btn_row = QHBoxLayout()
        self.btn_new_filter = QPushButton("Nouveau")
        self.btn_edit_filter = QPushButton("Modifier")
        self.btn_delete_filter = QPushButton("Supprimer")
        self.btn_new_filter.clicked.connect(self._new_filter)
        self.btn_edit_filter.clicked.connect(self._edit_filter)
        self.btn_delete_filter.clicked.connect(self._delete_filter)
        btn_row.addWidget(self.btn_new_filter)
        btn_row.addWidget(self.btn_edit_filter)
        btn_row.addWidget(self.btn_delete_filter)
        left_layout.addLayout(btn_row)

        left.setLayout(left_layout)
        splitter.addWidget(left)

        # -- Panneau droit : table des paramètres --
        right = QWidget()
        right_layout = QVBoxLayout(right)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Recherche :"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Rechercher un paramètre...")
        self.search_edit.textChanged.connect(self._apply_text_search)
        search_row.addWidget(self.search_edit)
        right_layout.addLayout(search_row)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(COL_NAME, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(COL_VALUE, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.table.itemChanged.connect(self._on_item_changed)
        right_layout.addWidget(self.table)

        right.setLayout(right_layout)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 880])

        self.setCentralWidget(splitter)
        self._set_controls_enabled(False)

    def _build_menu(self) -> None:
        toolbar = QToolBar("Principal")
        self.addToolBar(toolbar)

        act_open = QAction("Ouvrir...", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self.open_file)

        act_save = QAction("Enregistrer", self)
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self.save_file)

        act_save_as = QAction("Enregistrer sous...", self)
        act_save_as.setShortcut(QKeySequence.SaveAs)
        act_save_as.triggered.connect(self.save_file_as)

        for act in (act_open, act_save, act_save_as):
            toolbar.addAction(act)

        menu_file = self.menuBar().addMenu("Fichier")
        menu_file.addAction(act_open)
        menu_file.addAction(act_save)
        menu_file.addAction(act_save_as)
        menu_file.addSeparator()
        act_quit = QAction("Quitter", self)
        act_quit.triggered.connect(self.close)
        menu_file.addAction(act_quit)

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.table.setEnabled(enabled)
        self.search_edit.setEnabled(enabled)
        self.btn_new_filter.setEnabled(enabled)
        self.btn_edit_filter.setEnabled(enabled)
        self.btn_delete_filter.setEnabled(enabled)
        self.filter_list.setEnabled(enabled)

    # ------------------------------------------------------------- Fichier
    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier .set", "", "Fichiers .set (*.set);;Tous les fichiers (*.*)"
        )
        if not path:
            return
        self.load_file(path)

    def load_file(self, path: str) -> None:
        """Charge un fichier .set donné (utilisé par 'Ouvrir' et par le
        double-clic sur un fichier .set depuis l'Explorateur Windows)."""
        if not os.path.isfile(path):
            QMessageBox.critical(self, "Erreur", f"Fichier introuvable :\n{path}")
            return
        try:
            self.set_file = SetFile.load(path)
        except OSError as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le fichier :\n{exc}")
            return

        self.current_path = path
        self.setWindowTitle(f"Éditeur de fichiers .set MT5 — {os.path.basename(path)}")
        self._set_controls_enabled(True)
        self._refresh_filter_list()
        self.filter_list.setCurrentRow(0)  # affiche "Tous les paramètres"

    def save_file(self) -> None:
        if not self.set_file:
            return
        if not self.current_path:
            self.save_file_as()
            return
        try:
            self.set_file.save(self.current_path)
        except OSError as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer :\n{exc}")
            return
        QMessageBox.information(self, "Enregistré", "Fichier enregistré avec succès.")

    def save_file_as(self) -> None:
        if not self.set_file:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer sous", self.current_path or "", "Fichiers .set (*.set)"
        )
        if not path:
            return
        if not path.lower().endswith(".set"):
            path += ".set"
        self.current_path = path
        self.save_file()
        self.setWindowTitle(f"Éditeur de fichiers .set MT5 — {os.path.basename(path)}")

    # -------------------------------------------------------------- Filtres
    def _refresh_filter_list(self) -> None:
        self.filter_list.blockSignals(True)
        self.filter_list.clear()
        self.filter_list.addItem(ALL_FILTER)
        for name in self.filter_manager.names():
            self.filter_list.addItem(name)
        self.filter_list.blockSignals(False)

    def _all_param_names(self) -> List[str]:
        if not self.set_file:
            return []
        return [p.name for p in self.set_file.parameters]

    def _new_filter(self) -> None:
        if not self.set_file:
            return
        dialog = FilterDialog(self._all_param_names(), self)
        if dialog.exec():
            name, selected = dialog.result_data()
            if not selected:
                QMessageBox.warning(self, "Filtre vide", "Sélectionnez au moins un paramètre.")
                return
            if name in self.filter_manager.filters:
                if QMessageBox.question(
                    self, "Filtre existant", f"Le filtre '{name}' existe déjà. Le remplacer ?"
                ) != QMessageBox.Yes:
                    return
            self.filter_manager.set_filter(name, selected)
            self._refresh_filter_list()
            items = self.filter_list.findItems(name, Qt.MatchExactly)
            if items:
                self.filter_list.setCurrentItem(items[0])

    def _edit_filter(self) -> None:
        current = self.filter_list.currentItem()
        if not current or current.text() == ALL_FILTER:
            QMessageBox.information(self, "Info", "Sélectionnez un filtre personnalisé à modifier.")
            return
        old_name = current.text()
        dialog = FilterDialog(
            self._all_param_names(),
            self,
            filter_name=old_name,
            selected_names=self.filter_manager.get(old_name),
        )
        if dialog.exec():
            new_name, selected = dialog.result_data()
            if not selected:
                QMessageBox.warning(self, "Filtre vide", "Sélectionnez au moins un paramètre.")
                return
            if new_name != old_name:
                self.filter_manager.delete(old_name)
            self.filter_manager.set_filter(new_name, selected)
            self._refresh_filter_list()
            items = self.filter_list.findItems(new_name, Qt.MatchExactly)
            if items:
                self.filter_list.setCurrentItem(items[0])

    def _delete_filter(self) -> None:
        current = self.filter_list.currentItem()
        if not current or current.text() == ALL_FILTER:
            QMessageBox.information(self, "Info", "Sélectionnez un filtre personnalisé à supprimer.")
            return
        name = current.text()
        if QMessageBox.question(self, "Confirmer", f"Supprimer le filtre '{name}' ?") == QMessageBox.Yes:
            self.filter_manager.delete(name)
            self._refresh_filter_list()
            self.filter_list.setCurrentRow(0)

    def _on_filter_selected(self, filter_name: str) -> None:
        self.search_edit.clear()
        self._populate_table(filter_name)

    def _apply_text_search(self, text: str) -> None:
        text = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_NAME)
            match = text in item.text().lower() if item else False
            self.table.setRowHidden(row, not match if text else False)

    # -------------------------------------------------------------- Table
    def _populate_table(self, filter_name: str) -> None:
        if not self.set_file:
            return

        if not filter_name or filter_name == ALL_FILTER:
            params = self.set_file.parameters
        else:
            allowed = set(self.filter_manager.get(filter_name))
            params = [p for p in self.set_file.parameters if p.name in allowed]

        self.table.blockSignals(True)
        self.table.setRowCount(len(params))
        for row, param in enumerate(params):
            name_item = QTableWidgetItem(param.name)
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, COL_NAME, name_item)

            value_item = QTableWidgetItem(param.value)
            self.table.setItem(row, COL_VALUE, value_item)

            if param.optimizable:
                default_item = QTableWidgetItem(param.default or "")
                min_item = QTableWidgetItem(param.min or "")
                max_item = QTableWidgetItem(param.max or "")
                self.table.setItem(row, COL_DEFAULT, default_item)
                self.table.setItem(row, COL_MIN, min_item)
                self.table.setItem(row, COL_MAX, max_item)

                optimize_item = QTableWidgetItem()
                optimize_item.setFlags(
                    Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
                )
                optimize_item.setCheckState(Qt.Checked if param.optimize else Qt.Unchecked)
                self.table.setItem(row, COL_OPTIMIZE, optimize_item)
            else:
                for col in (COL_DEFAULT, COL_MIN, COL_MAX, COL_OPTIMIZE):
                    empty_item = QTableWidgetItem("")
                    empty_item.setFlags(Qt.NoItemFlags)
                    self.table.setItem(row, col, empty_item)
        self.table.blockSignals(False)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if not self.set_file:
            return
        row = item.row()
        name_item = self.table.item(row, COL_NAME)
        if not name_item:
            return
        param = self.set_file.get_parameter(name_item.text())
        if not param:
            return

        col = item.column()
        if col == COL_VALUE:
            param.value = item.text()
        elif col == COL_DEFAULT:
            param.default = item.text()
        elif col == COL_MIN:
            param.min = item.text()
        elif col == COL_MAX:
            param.max = item.text()
        elif col == COL_OPTIMIZE and param.optimizable:
            param.optimize = item.checkState() == Qt.Checked
