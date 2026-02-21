"""
Модуль графического интерфейса макроса `sheet_layout`.

Графический интерфейс позволяет:
* изменять формат листа чертежа;
* менять ориентацию формата листа;
* применять оформление листа из lyt-библиотеки или сбрасывать на умолчательное.

"""
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config
from ..utils import config_reader

from ..gui.macros import Macros

from ..utils.resources import get_resource_path

from ..macros.sheet_layout import *



class MacrosSheetLayout(Macros):
    def __init__(self) -> None:
        super().__init__("sheet_layout", "Оформление чертежа")

    def check_config(self) -> None:
        config_reader.ensure_dict_value(self.config(), "lib_path", str, "")

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        def _get_apply_format_function(i: int):
            return lambda: self.execute(lambda: self.apply_sheet_format(i))

        btn_format = QtWidgets.QToolButton()
        btn_format.setIcon(QtGui.QIcon(get_resource_path("img/macros/sheet_format.svg")))
        btn_format.setToolTip("Выбор формата листа 2D-документа")
        btn_format.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        menu_format = QtWidgets.QMenu("Выбор формата листа 2D-документа")
        for i in range(6):
            fmt = f"A{i}"
            action = QtWidgets.QAction(fmt, btn_format)
            action.triggered.connect(_get_apply_format_function(i))
            menu_format.addAction(action)
        btn_format.setMenu(menu_format)

        btn_orientation = QtWidgets.QToolButton()
        btn_orientation.setIcon(QtGui.QIcon(get_resource_path("img/macros/sheet_orientation.svg")))
        btn_orientation.clicked.connect(lambda: self.execute(self.switch_sheet_orientation))
        btn_orientation.setToolTip("Сменить ориентацию формата листа")

        btn_layout = QtWidgets.QToolButton()
        btn_layout.setIcon(QtGui.QIcon(get_resource_path("img/macros/sheet_layout.svg")))
        btn_layout.clicked.connect(lambda: self.execute(self.apply_lib_layout))
        btn_layout.setToolTip("Применить оформление из библиотеки")

        return {
            "селектор формата листа": btn_format,
            "кнопка: сменить ориентацию формата листа": btn_orientation,
            "кнопка: применить оформление из библиотеки": btn_layout,
        }

    def settings_widget(self) -> QtWidgets.QWidget:
        def get_new() -> None:
            ext_filter = "Библиотека оформлений (*.lyt)"
            lib_path, filter_ = QtWidgets.QFileDialog.getOpenFileName(
                self._parent_widget,
                "Выбрать библиотеку оформления чертежей",
                "",
                f"{ext_filter};;Все файлы (*)",
                ext_filter,
            )
            if lib_path != "":
                self.config()["lib_path"] = lib_path
                le_lib_path.setText(self.config()["lib_path"])

        def reset() -> None:
            self.config()["lib_path"] = ""
            le_lib_path.setText(self.config()["lib_path"])

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        le_lib_path = QtWidgets.QLineEdit(self.config()["lib_path"])
        le_lib_path.setReadOnly(True)

        btn_choose = QtWidgets.QPushButton("Выбрать...")
        btn_choose.clicked.connect(get_new)

        btn_clear = QtWidgets.QPushButton("Вернуть стандартное")
        btn_clear.clicked.connect(reset)

        l.addWidget(QtWidgets.QLabel("Путь к библиотеке оформления:"), 0, 0, 1, 2)
        l.addWidget(le_lib_path, 1, 0, 1, 2)
        l.addWidget(btn_choose, 2, 0, 1, 1)
        l.addWidget(btn_clear, 2, 1, 1, 1)

        return w

    def apply_lib_layout(self) -> None:
        set_sheets_layout_library(self.config()["lib_path"])

    def apply_sheet_format(self, fmt: int) -> None:
        sheet_index = 0
        old_fmt, is_vertical = get_sheet_format(sheet_index)
        set_sheet_format(fmt, is_vertical, sheet_index)

    def switch_sheet_orientation(self) -> None:
        sheet_index = 0
        old_fmt, is_vertical = get_sheet_format(sheet_index)
        is_vertical = not is_vertical
        set_sheet_format(old_fmt, is_vertical, sheet_index)

