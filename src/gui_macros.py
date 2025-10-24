"""
Модуль предоставляет классы графического интерфейса макроса.

"""

from PyQt5 import QtCore, QtGui, QtWidgets
from sys import exit
import traceback

from src import config


class Macros(QtCore.QObject):
    settings_requested = QtCore.pyqtSignal(str)
    """Signature: `toolbar_update_requested(macros_codename: str)` """

    toolbar_update_requested = QtCore.pyqtSignal(bool)
    """Signature: `toolbar_update_requested(is_immediate: bool)` """

    def __init__(self, code_name: str, full_name: str) -> None:
        super().__init__()
        self.code_name = code_name
        self.full_name = full_name
        self._config = config.macros(self.code_name)
        self._parent_widget: QtWidgets.QWidget = None

        Macros.check_config(self)  # вызов базовой проверки
        self.check_config()  # вызов проверки, переопределенной в классе макроса

    def set_parent_widget(self, widget: QtWidgets.QWidget) -> None:
        self._parent_widget = widget

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget | QtWidgets.QAction]:
        return {}

    def settings_widget(self) -> QtWidgets.QWidget:
        l = QtWidgets.QLabel(f'Нет доступных настроек для макроса «{self.full_name}».')
        l.setWordWrap(True)
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        return l

    def check_config(self) -> None:
        """
            Проверить и исправить config (настройки) макроса.
        """
        try:
            assert isinstance(self._config, dict)
        except:
            self._config = {}

    def execute(self, func) -> bool:
        QtWidgets.qApp.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            func()
        except Exception as e:
            QtWidgets.qApp.restoreOverrideCursor()
            self.show_error(e=e)
            return False
        QtWidgets.qApp.restoreOverrideCursor()
        return True

    def show_error(self, text: str = "Произошла ошибка", e: Exception = None) -> None:
        if e is None:
            e_str = ""
        else:
            e_str = f"<br>{e.__class__.__name__}: {str(e)}<br><pre>{traceback.format_exc()}</pre>"
        QtWidgets.QMessageBox.critical(
            self._parent_widget,
            "Ошибка",
            f"{text}{e_str}",
        )
        print(traceback.format_exc())

    def show_warning(self, text: str) -> None:
        QtWidgets.QMessageBox.warning(
            self._parent_widget,
            "Внимание!",
            str(text),
        )
        print("Внимание!", text)

    def request_settings(self, code_name = "") -> None:
        if code_name == "":
            code_name = self.code_name
        self.settings_requested.emit(code_name)



class MacrosSingleCommand(Macros):
    def __init__(self, code_name: str, full_name: str, icon_path: str, tooltip: str) -> None:
        super().__init__(code_name, full_name)
        self._icon_path = icon_path
        self._toolbar_button_tooltip = tooltip

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget | QtWidgets.QAction]:
        btn = QtWidgets.QToolButton()
        btn.setIcon(QtGui.QIcon(self._icon_path))
        btn.setToolTip(self._toolbar_button_tooltip)
        btn.clicked.connect(lambda: self.execute(self.execute_macros))
        return {
            "кнопка запуска макроса": btn,
        }

    def execute_macros(self) -> None:
        pass
