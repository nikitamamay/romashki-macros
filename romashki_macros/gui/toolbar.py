"""
Модуль виджета инструментальной панели.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

TOOLBAR_SEPARATOR_NAME = "$$$separator$$$"



class ToolBar(QtWidgets.QToolBar):
    move_event = QtCore.pyqtSignal()
    hide_event = QtCore.pyqtSignal()

    def __init__(self, title: str, parent = None):
        super().__init__(title, parent)
        self._contents: list[tuple[str, str]] = []

    def moveEvent(self, a0: QtGui.QMoveEvent | None) -> None:
        self.move_event.emit()
        return super().moveEvent(a0)

    def hideEvent(self, a0: QtGui.QHideEvent | None) -> None:
        self.hide_event.emit()
        return super().hideEvent(a0)

    def add_object(self, macros_codename: str, widget_codename: str, obj: QtWidgets.QWidget|QtWidgets.QAction|None) -> None:
        self._contents.append([macros_codename, widget_codename])
        if macros_codename == TOOLBAR_SEPARATOR_NAME:
            self.addSeparator()
        elif isinstance(obj, QtWidgets.QWidget):
            self.addWidget(obj)
            obj.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        elif isinstance(obj, QtWidgets.QAction):
            self.addAction(obj)
        else:
            raise Exception(f"Unsupported element type: ({(macros_codename, widget_codename, obj)})")

    def get_contents(self) -> list[tuple[str, str]]:
        return self._contents