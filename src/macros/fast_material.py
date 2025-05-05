"""
Макрос для задания материала и плотности в 3D-модели в обход штатного справочника
"Материалы и сортаменты" Компас.

В графическом интерфейсе макроса можно задать свой собственный список наиболее
часто используемых материалов и назначать их за два клика мыши.

При применении материала в 3D-модели не происходит перекрашивания модели
в темно-серый цвет, как это зачем-то выполняется при работе с штатным справочником
материалов в Компас.

Maкрос поддерживает запись сортамента с привычным форматированием с дробной чертой,
например, для обозначений листов, труб, профилей и т.д.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path

import re


DENSITY_STEEL = 7850  # kg/m3


re_fraction = re.compile(r'([\s\S]*?)\$d([\s\S]*?);([\s\S]*?)\$', re.I | re.M)


def ensure_value(value, default):
    if value is None:
        return default
    return value




def set_material_in_current_part(material: str, density: int) -> None:
    """ Назначить материал для текущей детали. Плотность `density` здесь выражается в кг/м3."""
    doc, part = open_part()
    part.SetMaterial(material, density / 1000)
    part.Update()


def get_material_in_current_part() -> tuple[str, float]:
    doc, part = open_part()
    s_raw = part.Material
    density = part.Density * 1000
    return (s_raw, density)


def compile_material_str(base: str, on_top: str = "", under: str = "") -> str:
    if on_top == "" and under == "":
        return base
    return f"{base}$d{on_top};{under}$"

def parse_material_str(s: str) -> tuple[str, str, str]:
    m = re_fraction.match(s)
    if not m is None:
        return (m.group(1), m.group(2), m.group(3))
    return (s, "", "")

def get_single_line_material_str(base: str, on_top: str = "", under: str = "") -> str:
    if on_top == "" and under == "":
        return base
    return f"{base} {on_top} / {under}"



class MaterialInputWidget(QtWidgets.QWidget):
    data_edited = QtCore.pyqtSignal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self._le_left = QtWidgets.QLineEdit()
        self._le_left.textEdited.connect(self.fancy_updated)
        self._le_left.textEdited.connect(lambda: self.data_edited.emit())

        self._le_top = QtWidgets.QLineEdit()
        self._le_top.textEdited.connect(self.fancy_updated)
        self._le_top.textEdited.connect(lambda: self.data_edited.emit())

        self._le_bottom = QtWidgets.QLineEdit()
        self._le_bottom.textEdited.connect(self.fancy_updated)
        self._le_bottom.textEdited.connect(lambda: self.data_edited.emit())

        _lbl_line = gui_widgets.FilledLabel()
        _lbl_line.setFixedHeight(1)
        _lbl_line.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed
        )

        self._lbl_str = QtWidgets.QLabel()  # FIXME сделать ElidedLabel

        self._le_raw = QtWidgets.QLineEdit()
        font = QtGui.QFont("Monospace")
        font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
        self._le_raw.setFont(font)
        self._le_raw.textEdited.connect(self.raw_updated)
        self._le_raw.textEdited.connect(lambda: self.data_edited.emit())

        self._sb_density = QtWidgets.QDoubleSpinBox()
        self._sb_density.setRange(-(10**9), 10**9)
        self._sb_density.setValue(0)
        self._sb_density.setSuffix(" кг/м3")
        self._sb_density.setDecimals(3)
        self._sb_density.valueChanged.connect(lambda: self.data_edited.emit())
        self._sb_density.setToolTip(
            "Плотность веществ:"
            "\nАлюминий    2700 кг/м3"
            "\nБронза    7600 кг/м3"
            "\nДуб (сухой)    700 кг/м3"
            "\nЛатунь    8500 кг/м3"
            "\nМедь    8900 кг/м3"
            "\nОргстекло    1200 кг/м3"
            "\nПолиэтилен    920 кг/м3"
            "\nРезина    900...1200 кг/м3"
            "\nРВД (2SN)    2600 кг/м3"
            "\nСосна (сухая)    400 кг/м3"
            "\nСталь    7850 кг/м3"
            "\nСтекло    2500 кг/м3"
            "\nФторопласт    1700 кг/м3"
            "\nЧугун    7000 кг/м3"
        )

        self._l_le = QtWidgets.QGridLayout()
        self._l_le.addWidget(self._le_left, 1, 0, 3, 1)
        self._l_le.addWidget(self._le_top, 0, 1, 2, 1)
        self._l_le.addWidget(self._le_bottom, 3, 1, 2, 1)
        self._l_le.addWidget(_lbl_line, 2, 1, 1, 1)

        self._l = QtWidgets.QGridLayout()
        self._l.addLayout(self._l_le, 0, 0, 1, 2)
        self._l.addWidget(QtWidgets.QLabel("Однострочная запись:"), 1, 0, 1, 1)
        self._l.addWidget(self._lbl_str, 1, 1, 1, 1)
        self._l.addWidget(QtWidgets.QLabel("Синтаксическая запись:"), 2, 0, 1, 1)
        self._l.addWidget(self._le_raw, 2, 1, 1, 1)
        self._l.addWidget(QtWidgets.QLabel("Плотность материала:"), 3, 0, 1, 1)
        self._l.addWidget(self._sb_density, 3, 1, 1, 1)
        self.setLayout(self._l)

    def raw_updated(self) -> None:
        base, top, bottom = parse_material_str(self._le_raw.text())
        self._le_left.setText(base)
        self._le_top.setText(top)
        self._le_bottom.setText(bottom)
        self._lbl_str.setText(get_single_line_material_str(base, top, bottom))

    def fancy_updated(self) -> None:
        base = self._le_left.text()
        top = self._le_top.text()
        bottom = self._le_bottom.text()
        self._le_raw.setText(compile_material_str(base, top, bottom))
        self._lbl_str.setText(get_single_line_material_str(base, top, bottom))

    def set_material(self, s_raw: str, density: float) -> None:
        self._le_raw.setText(s_raw)
        self._sb_density.setValue(density)
        self.raw_updated()

    def get_material(self) -> tuple[str, float]:
        return (self._le_raw.text(), self._sb_density.value())

    def clear(self) -> None:
        self.set_material("", 0)




class MacrosFastMaterial(Macros):
    DATA_ROLE_RAW = 0x100
    DATA_ROLE_DENSITY = 0x101

    def __init__(self) -> None:
        super().__init__("fast_material", "Запись материала в 3D-модель")
        self._dialog = None
        self._dialog_miw = None
        self._is_selector_widget_inited = False

    def init_selector_widget(self) -> None:
        if not self._is_selector_widget_inited:
            self._is_selector_widget_inited = True

            self._dialog = QtWidgets.QWidget(self._parent_widget)
            self._dialog.resize(500, 0)
            self._dialog.setWindowFlag(QtCore.Qt.WindowType.Window)
            self._dialog.setWindowTitle("Назначить материал")

            self._dialog_miw = MaterialInputWidget()

            btn_go_and_add = QtWidgets.QPushButton("Применить и сохранить")
            btn_go_and_add.clicked.connect(lambda: self.enter_material(do_save=True))

            btn_go = QtWidgets.QPushButton("Применить без сохранения")
            btn_go.clicked.connect(lambda: self.enter_material(do_save=False))

            l = QtWidgets.QGridLayout()
            l.addWidget(self._dialog_miw, 0, 0, 1, 3)
            l.addWidget(btn_go_and_add, 1, 0, 1, 1)
            l.addWidget(btn_go, 1, 1, 1, 1)
            self._dialog.setLayout(l)

        self._dialog_miw.set_material("Лист$d8 ГОСТ 19903-74;09Г2С ГОСТ 19281-2014$", DENSITY_STEEL)


    def check_config(self) -> None:
        try:
            assert isinstance(self._config["materials_list"], list)
            for el in self._config["materials_list"]:
                assert isinstance(el, (list, tuple))
                raw, density = el
                assert isinstance(raw, str)
                assert isinstance(density, (int, float))
        except:
            self._config["materials_list"] = [
                ["40Х ГОСТ 4543-2016", DENSITY_STEEL],
                ["Лист$d8 ГОСТ 19903-74;09Г2С ГОСТ 19281-2014$", DENSITY_STEEL],
                ["Уголок$d20х20х3 ГОСТ 8509-93;Ст3сп ГОСТ 535-2005$", DENSITY_STEEL],
                ["Труба$d50х50х3 ГОСТ 8639-82;09Г2С ГОСТ 19281-2014$", DENSITY_STEEL],
            ]
            config.save_delayed()


    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        def _apply_material(material_index: int) -> None:
            s_raw, density = self._config["materials_list"][material_index]
            self.execute(lambda: set_material_in_current_part(
                s_raw, density
            ))

        btn_material = gui_widgets.ButtonWithList(QtGui.QIcon(get_resource_path("img/macros/material.svg")), "")
        btn_material.clicked.connect(self.choose_material)
        btn_material.setToolTip("Назначить материал...")

        for i, m in enumerate(self._config["materials_list"]):
            s_raw, density = m
            s = get_single_line_material_str(*parse_material_str(s_raw))
            btn_material.menu().addAction(s, (lambda i: lambda: _apply_material(i))(i))
        btn_material.menu().addSeparator()
        btn_material.menu().addAction(
            QtGui.QIcon(get_resource_path("img/macros/material.svg")),
            "Сохранить материал текущей детали",
            self.remember_current_material,
        )
        btn_material.menu().addAction(
            QtGui.QIcon(get_resource_path("img/settings.svg")),
            "Настроить список...",
            self.request_settings,
        )

        return {
            "кнопка: назначить материал...": btn_material,
        }

    def settings_widget(self) -> QtWidgets.QWidget:
        def _save_list() -> None:
            self._config["materials_list"].clear()
            for item in materials_list.iterate_items():
                s_raw = item.data(self.DATA_ROLE_RAW)
                density = item.data(self.DATA_ROLE_DENSITY)
                m = [s_raw, density]
                self._config["materials_list"].append(m)
            config.save_delayed()

        def _set_item_data(item: QtGui.QStandardItem, s_raw: str, density: float) -> None:
            s_fancy = get_single_line_material_str(*parse_material_str(s_raw))
            item.setData(s_fancy, QtCore.Qt.ItemDataRole.DisplayRole)
            item.setData(s_raw, self.DATA_ROLE_RAW)
            item.setData(density, self.DATA_ROLE_DENSITY)

        def _selection_changed() -> None:
            item = materials_list.get_one_selected_item()
            if not item is None:
                s_raw = ensure_value(item.data(self.DATA_ROLE_RAW), "")
                density = ensure_value(item.data(self.DATA_ROLE_DENSITY), 0.0)
                miw.set_material(s_raw, density)
            else:
                miw.clear()

        def _material_data_changed() -> None:
            s_raw, density = miw.get_material()
            item = materials_list.get_one_selected_item()
            if not item is None:
                _set_item_data(item, s_raw, density)
                _save_list()

        def _create_new_material() -> QtGui.QStandardItem:
            item = QtGui.QStandardItem()
            _set_item_data(item, "Сталь", DENSITY_STEEL)
            return item


        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        materials_list = gui_widgets.StringListSelector(_create_new_material)
        for m in self._config["materials_list"]:
            s_raw, density = m

            item = QtGui.QStandardItem()
            _set_item_data(item, s_raw, density)

            materials_list.add_new_item(item)

        miw = MaterialInputWidget()

        l.addWidget(materials_list, 0, 0, 1, 1)
        l.addWidget(miw, 1, 0, 1, 1)

        materials_list.clear_selection()

        miw.data_edited.connect(_material_data_changed)
        materials_list.selection_changed.connect(_selection_changed)
        materials_list.list_changed.connect(lambda: self.toolbar_update_requested.emit(False))
        materials_list.list_changed.connect(lambda: _save_list())

        return w

    def choose_material(self) -> None:
        self.init_selector_widget()
        self._dialog.show()

    def enter_material(self, do_save: bool) -> None:
        s_raw, density = self._dialog_miw.get_material()
        if do_save:
            m = [s_raw, density]
            self._config["materials_list"].append(m)
            config.save_delayed()
            self.toolbar_update_requested.emit(False)

        def _enter_material():
            set_material_in_current_part(s_raw, density)

        if self.execute(_enter_material):
            self._dialog.hide()

    def remember_current_material(self) -> None:
        def _remember_material():
            m = get_material_in_current_part()
            self._config["materials_list"].append(m)
            config.save_delayed()
            self.toolbar_update_requested.emit(True)
        self.execute(_remember_material)






if __name__ == "__main__":
    pass

    app = QtWidgets.QApplication([])

    w = MaterialInputWidget()

    w.show()

    app.exec()

    # set_material_in_current_part()
