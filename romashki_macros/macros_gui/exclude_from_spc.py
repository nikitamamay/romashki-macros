"""
Модуль графического интерфейса макроса `exclude_from_spc`.

Графический интерфейс позволяет:
* устанавливать флаг включения в спецификацию на "Включен" или "Не включен"
у выбранных компонентов в текущей модели.
"""
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config

from ..gui import widgets as gui_widgets
from ..gui.macros import Macros


from ..utils.resources import get_resource_path

from ..macros.exclude_from_spc import *


class MacrosExcludeFromSPC(Macros):
    def __init__(self) -> None:
        super().__init__(
            "exclude_from_spc",
            "Управление включением в спецификацию",
        )

    def check_config(self) -> None:
        try:
            pass
        except:
            self._config["nothing"] = None
            config.save_delayed()

    def include_in_spc(self) -> None:
        QtWidgets.qApp.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            switch_spc_inclusion(True)
        except Exception as e:
            self.show_error(e=e)
        QtWidgets.qApp.restoreOverrideCursor()

    def exclude_from_spc(self) -> None:
        QtWidgets.qApp.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            switch_spc_inclusion(False)
        except Exception as e:
            self.show_error(e=e)
        QtWidgets.qApp.restoreOverrideCursor()

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        btn = QtWidgets.QToolButton()
        btn.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        btn.setIcon(QtGui.QIcon(get_resource_path("img/macros/spc.svg")))
        btn.setToolTip("Управление включением в спецификацию")

        a_include = QtWidgets.QAction(QtGui.QIcon(get_resource_path("img/macros/spc_include.svg")), "Включить в спецификацию", btn)
        a_include.toggled.connect(self.include_in_spc)

        a_exclude = QtWidgets.QAction(QtGui.QIcon(get_resource_path("img/macros/spc_exclude.svg")), "Исключить из спецификации", btn)
        a_exclude.toggled.connect(self.exclude_from_spc)

        menu = QtWidgets.QMenu("Управление включением в спецификацию")
        menu.addAction(a_include)
        menu.addAction(a_exclude)
        btn.setMenu(menu)

        return {
            "кнопка с меню": btn,
        }
