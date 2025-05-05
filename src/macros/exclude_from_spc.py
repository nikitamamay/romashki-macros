"""
Макрос предоставляет функционал по управлению включением компонентов в спецификацию.

Макрос актуален для старых версий Компаса, в которых нет возможности в штатной
панели свойств выключить вхождение в спецификацию у выделенных компонентов, а нужно
для каждого компонента (по одному) заходить в отдельное меню свойств компонента и
выключать это там.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros


from src.resources import get_resource_path


def switch_spc_inclusion(new_state: bool|None = None) -> None:
    doc3d, toppart = open_part()

    parts: list[KAPI7.IPart7] = get_selected(doc3d, KAPI7.IPart7)

    print(f"{len(parts)} are selected.")

    if len(parts) == 0:
        return

    if new_state is None:
        new_state = not parts[0].CreateSpcObjects

    for p in parts:
        p.CreateSpcObjects = new_state
        p.Update()
        print(f"{p.Marking} {p.Name} is now with CreateSpcObjects={new_state}.".lstrip())





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
            self.show_error(e)
        QtWidgets.qApp.restoreOverrideCursor()

    def exclude_from_spc(self) -> None:
        QtWidgets.qApp.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            switch_spc_inclusion(False)
        except Exception as e:
            self.show_error(e)
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

if __name__ == "__main__":
    switch_spc_inclusion()
