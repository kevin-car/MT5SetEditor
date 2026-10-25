"""Fenêtre principale de l'éditeur de fichiers .set MetaTrader 5."""
from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from enum_dialog import EnumDialog
from enum_manager import EnumManager
from filter_dialog import FilterDialog
from filter_manager import FilterManager
from set_parser import Parameter, SetFile

ALL_FILTER = "Tous les paramètres"

COL_NAME = 0
COL_VALUE = 1
COL_MINIMUM = 2
COL_STEP = 3
COL_MAXIMUM = 4
COL_OPTIMIZE = 5
COL_STEPS = 6
COLUMNS = ["Paramètre", "Valeur", "Minimum", "Pas", "Maximum", "Optimiser", "Étapes"]
KIND_BOOL = "bool"
KIND_ENUM = "enum"
KIND_TIMEFRAME = "timeframe"
KIND_TIME = "time"
KIND_NUMBER = "number"
TIME_STEP_SECONDS = 300
TIME_CHOICES = [
    f"{minutes // 60:02d}:{minutes % 60:02d}" for minutes in range(0, 24 * 60, TIME_STEP_SECONDS // 60)
]
TIMEFRAMES = {
    0: "Current",
    1: "1 Minute",
    2: "2 Minutes",
    3: "3 Minutes",
    4: "4 Minutes",
    5: "5 Minutes",
    6: "6 Minutes",
    10: "10 Minutes",
    12: "12 Minutes",
    15: "15 Minutes",
    20: "20 Minutes",
    30: "30 Minutes",
    16385: "1 Hour",
    16386: "2 Hours",
    16387: "3 Hours",
    16388: "4 Hours",
    16390: "6 Hours",
    16392: "8 Hours",
    16396: "12 Hours",
    16408: "1 Day",
    32769: "1 Week",
    49153: "1 Month",
}
TIMEFRAME_VALUES = {label.lower(): str(value) for value, label in TIMEFRAMES.items()}


def _format_number(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        number = Decimal(value)
    except InvalidOperation:
        return value
    if number == 0:
        return "0"
    formatted = format(number, "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def _is_timeframe_parameter(param: Parameter) -> bool:
    normalized_name = param.name.lower().replace("-", "_").replace(" ", "_")
    return normalized_name.endswith("_tf") or param.max == "49153"


def _format_timeframe(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return TIMEFRAMES.get(int(value), _format_number(value))
    except ValueError:
        return value


def _parse_timeframe(value: str) -> str:
    return TIMEFRAME_VALUES.get(value.strip().lower(), value)


def _is_time_parameter(param: Parameter) -> bool:
    normalized_name = param.name.lower().replace("-", "_").replace(" ", "_")
    time_name = (
        normalized_name in {"start", "stop"}
        or normalized_name.endswith("_hour")
        or "_hour_" in normalized_name
    )
    try:
        maximum = int(param.max or "")
    except ValueError:
        return time_name
    return 82800 <= maximum <= 86400


def _is_int(text: Optional[str]) -> bool:
    try:
        int((text or "").strip())
    except ValueError:
        return False
    return True


def _looks_like_enum(param: Parameter) -> bool:
    """MT5 écrit un pas de 0 et des bornes entières pour les énumérations."""
    return (
        param.optimizable
        and (param.min or "").strip() == "0"
        and all(_is_int(v) for v in (param.value, param.default, param.max))
    )


def _param_kind(param: Parameter, enum_manager: EnumManager) -> str:
    if (param.value or "").strip().lower() in ("true", "false"):
        return KIND_BOOL
    if enum_manager.get(param.name):
        return KIND_ENUM
    if _is_timeframe_parameter(param):
        return KIND_TIMEFRAME
    if _is_time_parameter(param):
        return KIND_TIME
    if _looks_like_enum(param):
        return KIND_ENUM
    return KIND_NUMBER


def _format_time(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        seconds = int(value)
    except ValueError:
        return _format_number(value)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}" if seconds == 0 else f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _parse_time(value: str) -> str:
    if ":" not in value:
        return value
    parts = value.split(":")
    if len(parts) not in (2, 3):
        return value
    try:
        hours, minutes = int(parts[0]), int(parts[1])
        seconds = int(parts[2]) if len(parts) == 3 else 0
    except ValueError:
        return value
    if hours < 0 or minutes not in range(60) or seconds not in range(60):
        return value
    return str(hours * 3600 + minutes * 60 + seconds)


def _enum_values(param: Parameter, labels: Dict[int, str]) -> List[int]:
    if labels:
        return list(labels)
    bounds = [int(v) for v in (param.value, param.default, param.max) if _is_int(v)]
    return list(range(min(bounds), max(bounds) + 1)) if bounds else []


def _optimization_steps(param: Parameter, kind: str, labels: Dict[int, str]) -> Optional[int]:
    """Nombre de passes d'optimisation pour un paramètre (colonne 'Étapes' de MT5)."""
    if not param.optimizable:
        return None
    start = (param.default or "").strip().lower()
    step = (param.min or "").strip()
    stop = (param.max or "").strip().lower()
    if kind == KIND_BOOL:
        return 1 if start == stop else 2
    try:
        start_d, step_d, stop_d = Decimal(start), Decimal(step or "0"), Decimal(stop)
    except InvalidOperation:
        return None
    if stop_d < start_d:
        return 0
    if kind == KIND_ENUM and labels:
        return sum(1 for value in labels if start_d <= value <= stop_d)
    if step_d > 0:
        return int((stop_d - start_d) / step_d) + 1
    if kind == KIND_TIMEFRAME:
        return sum(1 for tf in TIMEFRAMES if start_d <= tf <= stop_d)
    if kind == KIND_TIME:
        return int((stop_d - start_d) / TIME_STEP_SECONDS) + 1
    if start_d == start_d.to_integral_value() and stop_d == stop_d.to_integral_value():
        return int(stop_d - start_d) + 1
    return 1


def _format_count(count: int) -> str:
    return f"{count:,}".replace(",", " ")


class ChoiceDelegate(QStyledItemDelegate):
    """Listes déroulantes (heures, timeframes, énumérations, booléens) comme dans le testeur MT5."""

    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self._window = window

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        col = index.column()
        if col in (COL_MINIMUM, COL_MAXIMUM):
            pen = painter.pen()
            painter.setPen(option.palette.mid().color())
            rect = option.rect
            if col == COL_MINIMUM:
                painter.drawLine(rect.topLeft(), rect.bottomLeft())
            else:
                painter.drawLine(rect.topRight(), rect.bottomRight())
            painter.setPen(pen)

    def createEditor(self, parent, option, index):
        choices = self._window.choices_for(index.row(), index.column())
        if not choices:
            return super().createEditor(parent, option, index)
        combo = QComboBox(parent)
        combo.addItems(choices)
        combo.setMaxVisibleItems(20)
        combo.activated.connect(lambda _: (self.commitData.emit(combo), self.closeEditor.emit(combo)))
        return combo

    def setEditorData(self, editor, index):
        if not isinstance(editor, QComboBox):
            return super().setEditorData(editor, index)
        text = index.data() or ""
        if editor.findText(text) < 0:
            editor.addItem(text)
        editor.setCurrentText(text)

    def setModelData(self, editor, model, index):
        if not isinstance(editor, QComboBox):
            return super().setModelData(editor, model, index)
        model.setData(index, editor.currentText())


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Éditeur de fichiers .set MT5")
        self.resize(1100, 700)

        self.set_file: Optional[SetFile] = None
        self.current_path: Optional[str] = None
        self._saved_snapshot: List[str] = []
        self.filter_manager = FilterManager()
        self.enum_manager = EnumManager()
        self._kinds: Dict[str, str] = {}

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
        self.table.horizontalHeader().setSectionResizeMode(COL_STEPS, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.table.setItemDelegate(ChoiceDelegate(self))
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_table_menu)
        right_layout.addWidget(self.table)

        right.setLayout(right_layout)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 880])

        self.setCentralWidget(splitter)
        self._set_controls_enabled(False)

    def _build_menu(self) -> None:
        act_open = QAction("Ouvrir...", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self.open_file)

        act_save = QAction("Enregistrer", self)
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self.save_file)

        act_save_as = QAction("Enregistrer sous...", self)
        act_save_as.setShortcut(QKeySequence.SaveAs)
        act_save_as.triggered.connect(self.save_file_as)

        menu_file = self.menuBar().addMenu("Fichier")
        menu_file.addAction(act_open)
        menu_file.addAction(act_save)
        menu_file.addAction(act_save_as)
        menu_file.addSeparator()
        act_quit = QAction("Quitter", self)
        act_quit.triggered.connect(self.close)
        menu_file.addAction(act_quit)

        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-weight: bold; padding: 2px 10px;")
        self.total_label.setToolTip("Nombre total de combinaisons pour les paramètres cochés « Optimiser »")
        self.menuBar().setCornerWidget(self.total_label, Qt.TopRightCorner)
        self._update_total()

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.table.setEnabled(enabled)
        self.search_edit.setEnabled(enabled)
        self.btn_new_filter.setEnabled(enabled)
        self.btn_edit_filter.setEnabled(enabled)
        self.btn_delete_filter.setEnabled(enabled)
        self.filter_list.setEnabled(enabled)

    # ------------------------------------------------------------- Fichier
    def _snapshot(self) -> List[str]:
        return [entry.to_line() for entry in self.set_file.entries] if self.set_file else []

    def is_modified(self) -> bool:
        return bool(self.set_file) and self._snapshot() != self._saved_snapshot

    def _update_title(self) -> None:
        name = f" — {os.path.basename(self.current_path)}[*]" if self.current_path else ""
        self.setWindowTitle(f"Éditeur de fichiers .set MT5{name}")
        self.setWindowModified(self.is_modified())

    def maybe_save(self) -> bool:
        """Demande s'il faut enregistrer les modifications. Retourne False si l'utilisateur annule."""
        if not self.is_modified():
            return True
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Modifications non enregistrées")
        box.setText(f"Le fichier « {os.path.basename(self.current_path or 'sans nom')} » a été modifié.")
        box.setInformativeText("Voulez-vous enregistrer les modifications ?")
        btn_save = box.addButton("Enregistrer", QMessageBox.AcceptRole)
        btn_discard = box.addButton("Ne pas enregistrer", QMessageBox.DestructiveRole)
        box.addButton("Annuler", QMessageBox.RejectRole)
        box.setDefaultButton(btn_save)
        box.exec()
        if box.clickedButton() == btn_save:
            return self.save_file(show_message=False)
        return box.clickedButton() == btn_discard

    def closeEvent(self, event) -> None:
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()

    def open_file(self) -> None:
        if not self.maybe_save():
            return
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
            self._kinds.clear()
        except OSError as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le fichier :\n{exc}")
            return

        self.current_path = path
        self._saved_snapshot = self._snapshot()
        self._update_title()
        self._set_controls_enabled(True)
        self._refresh_filter_list()
        self.filter_list.setCurrentRow(0)  # affiche "Tous les paramètres"

    def save_file(self, show_message: bool = True) -> bool:
        if not self.set_file:
            return False
        if not self.current_path:
            return self.save_file_as(show_message)
        try:
            self.set_file.save(self.current_path)
        except OSError as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer :\n{exc}")
            return False
        self._saved_snapshot = self._snapshot()
        self._update_title()
        if show_message:
            QMessageBox.information(self, "Enregistré", "Fichier enregistré avec succès.")
        return True

    def save_file_as(self, show_message: bool = True) -> bool:
        if not self.set_file:
            return False
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer sous", self.current_path or "", "Fichiers .set (*.set)"
        )
        if not path:
            return False
        if not path.lower().endswith(".set"):
            path += ".set"
        previous_path, self.current_path = self.current_path, path
        if not self.save_file(show_message):
            self.current_path = previous_path
            self._update_title()
            return False
        return True

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

            kind = self.kind_of(param)
            value_item = QTableWidgetItem(self._format(param, param.value))
            if kind == KIND_ENUM:
                tip = "Clic droit pour modifier les libellés"
                name_item.setToolTip(tip)
                value_item.setToolTip(tip)
            self.table.setItem(row, COL_VALUE, value_item)

            if param.optimizable:
                minimum_item = QTableWidgetItem(self._format(param, param.default))
                if kind in (KIND_BOOL, KIND_ENUM, KIND_TIMEFRAME):
                    step_item = QTableWidgetItem("")
                    step_item.setFlags(Qt.ItemIsEnabled)
                else:
                    step_item = QTableWidgetItem(self._format(param, param.min, step=True))
                maximum_item = QTableWidgetItem(self._format(param, param.max))
                self.table.setItem(row, COL_MINIMUM, minimum_item)
                self.table.setItem(row, COL_STEP, step_item)
                self.table.setItem(row, COL_MAXIMUM, maximum_item)

                optimize_item = QTableWidgetItem()
                optimize_item.setFlags(
                    Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
                )
                optimize_item.setCheckState(Qt.Checked if param.optimize else Qt.Unchecked)
                self.table.setItem(row, COL_OPTIMIZE, optimize_item)
            else:
                for col in (COL_MINIMUM, COL_STEP, COL_MAXIMUM, COL_OPTIMIZE):
                    empty_item = QTableWidgetItem("")
                    empty_item.setFlags(Qt.NoItemFlags)
                    self.table.setItem(row, col, empty_item)
            self._set_steps_cell(row, param)
        self.table.blockSignals(False)
        self._update_total()

    def param_at_row(self, row: int) -> Optional[Parameter]:
        name_item = self.table.item(row, COL_NAME)
        if not self.set_file or not name_item:
            return None
        return self.set_file.get_parameter(name_item.text())

    def kind_of(self, param: Parameter) -> str:
        # Mis en cache : le type ne doit pas changer pendant l'édition (ex. pas modifié).
        if param.name not in self._kinds:
            self._kinds[param.name] = _param_kind(param, self.enum_manager)
        return self._kinds[param.name]

    def _enum_labels(self, param: Parameter) -> Dict[int, str]:
        return self.enum_manager.get(param.name) if self.kind_of(param) == KIND_ENUM else {}

    def _format(self, param: Parameter, value: Optional[str], step: bool = False) -> str:
        kind = self.kind_of(param)
        if kind == KIND_TIME:
            return _format_time(value)
        if step:
            return _format_number(value)
        if kind == KIND_TIMEFRAME:
            return _format_timeframe(value)
        if kind == KIND_ENUM and _is_int(value):
            return self._enum_labels(param).get(int(value), _format_number(value))
        return _format_number(value)

    def _parse(self, param: Parameter, text: str, step: bool = False) -> str:
        kind = self.kind_of(param)
        if kind == KIND_TIME:
            return _parse_time(text)
        if step:
            return text
        if kind == KIND_TIMEFRAME:
            return _parse_timeframe(text)
        if kind == KIND_ENUM:
            reverse = {label: str(value) for value, label in self._enum_labels(param).items()}
            return reverse.get(text.strip(), text)
        return text

    def choices_for(self, row: int, col: int) -> List[str]:
        param = self.param_at_row(row)
        if not param or col not in (COL_VALUE, COL_MINIMUM, COL_MAXIMUM):
            return []
        kind = self.kind_of(param)
        if kind == KIND_BOOL:
            return ["false", "true"]
        if kind == KIND_TIMEFRAME:
            return list(TIMEFRAMES.values())
        if kind == KIND_TIME:
            return TIME_CHOICES
        if kind == KIND_ENUM:
            labels = self._enum_labels(param)
            return [labels.get(v, str(v)) for v in _enum_values(param, labels)]
        return []

    def _show_table_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        param = self.param_at_row(row) if row >= 0 else None
        if not param:
            return
        kind = self.kind_of(param)
        if kind != KIND_ENUM and not (kind == KIND_NUMBER and _is_int(param.value)):
            return
        menu = QMenu(self)
        act = menu.addAction(f"Définir les libellés de « {param.name} »…")
        if menu.exec(self.table.viewport().mapToGlobal(pos)) == act:
            self._edit_enum_labels(param)

    def _edit_enum_labels(self, param: Parameter) -> None:
        labels = self.enum_manager.get(param.name)
        dialog = EnumDialog(param.name, set(_enum_values(param, {})) | {0}, labels, self)
        if dialog.exec():
            self.enum_manager.set_labels(param.name, dialog.labels())
            self._kinds.clear()
            current = self.filter_list.currentItem()
            self._populate_table(current.text() if current else ALL_FILTER)

    def _set_steps_cell(self, row: int, param: Parameter) -> None:
        steps = _optimization_steps(param, self.kind_of(param), self._enum_labels(param))
        if not param.optimize or steps is None:
            text = ""
        else:
            text = _format_count(steps)
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, COL_STEPS, item)

    def _update_total(self) -> None:
        params = [p for p in self.set_file.parameters if p.optimizable and p.optimize] if self.set_file else []
        total = 1 if params else 0
        for param in params:
            total *= _optimization_steps(param, self.kind_of(param), self._enum_labels(param)) or 1
        self.total_label.setText(f"Combinaisons : {_format_count(total)}")

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        row = item.row()
        param = self.param_at_row(row)
        if not param or item.column() == COL_STEPS:
            return

        col = item.column()
        value = self._parse(param, item.text(), step=col == COL_STEP)
        if col == COL_VALUE:
            param.value = value
        elif col == COL_MINIMUM:
            param.default = value
        elif col == COL_STEP:
            param.min = value
        elif col == COL_MAXIMUM:
            param.max = value
        elif col == COL_OPTIMIZE and param.optimizable:
            param.optimize = item.checkState() == Qt.Checked

        self.table.blockSignals(True)
        self._set_steps_cell(row, param)
        self.table.blockSignals(False)
        self._update_total()
        self.setWindowModified(self.is_modified())
