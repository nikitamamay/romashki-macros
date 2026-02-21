"""
Модуль предоставляет классы графического интерфейса макроса.

"""

from PyQt5 import QtCore, QtGui, QtWidgets
import traceback

from .. import config


class Macros(QtCore.QObject):
    """
    Графический интерфейс макроса и его настроек (конфигурации).
    """

    settings_requested = QtCore.pyqtSignal(str)
    """
    Signature: `settings_requested(macros_codename: str)`.

    `macros_codename` can be `""`.
    """

    toolbar_update_requested = QtCore.pyqtSignal(bool)
    """Signature: `toolbar_update_requested(is_immediate: bool)` """

    def __init__(self, code_name: str, full_name: str) -> None:
        super().__init__()
        self.code_name = code_name
        self.full_name = full_name
        self._parent_widget: QtWidgets.QWidget|None = None

        Macros.check_config(self)  # вызов базовой проверки
        self.check_config()  # вызов проверки, переопределенной в классе макроса

    def config(self) -> dict:
        return config.cr.macros(self.code_name)

    def set_parent_widget(self, widget: QtWidgets.QWidget) -> None:
        """
        Устанавливает родительский виджет (как правило, это главное окно приложения)
        для вновь создаваемых виджетов и окон макроса.
        """
        self._parent_widget = widget

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget | QtWidgets.QAction]:
        """
        Возвращает словарь с перечнем виджетов для панели инструментов:
        `{ "widget_name": <QWidget-or-QAction>, ... }`.
        """
        return {}

    def settings_widget(self) -> QtWidgets.QWidget:
        """
        Возвращает виджет, который будет отображаться в окне настроек макроса.

        См. `gui.settings.SettingsWindow`.
        """
        l = QtWidgets.QLabel(f'Нет доступных настроек для макроса «{self.full_name}».')
        l.setWordWrap(True)
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        return l

    def check_config(self) -> None:
        """
        Проверить и исправить config (настройки) макроса.

        Примечание. В конструкторе `Macros` вызываются две функции:
        базового класса `Macros.check_config()` и наследуемого `self.check_config()`.
        В связи с этим вызывать `super().check_config()` в переопределенном методе
        у дочернего класса не требуется.
        """
        self.config()  # гарантирует, что возвращаемое значение будет именно dict. Создает словарь, если его нет.

    def execute(self, func) -> bool:
        """
        Метод-обёртка для вызова функции `func`; гарантирует перехват исключений
        (Exceptions). Также на время выполнения `func` устанавливает курсор ожидания
        для всего графического приложения.

        Функция `func`, как правило, работает с Компас-API и может выбросить
        исключение (Exception). Это исключение перехватится в этом методе и
        выведется в виде всплывающего сообщения на экран.
        """
        QtWidgets.qApp.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            func()
        except Exception as e:
            QtWidgets.qApp.restoreOverrideCursor()
            self.show_error(e=e)
            return False
        QtWidgets.qApp.restoreOverrideCursor()
        return True

    def show_error(self, text: str = "Произошла ошибка", e: Exception|None = None) -> None:
        """
        Отображает всплывающее сообщение об ошибке.
        """
        if e is None:
            e_str = ""
        else:
            e_str = f"<br>{e.__class__.__name__}: {str(e)}<br><pre>{traceback.format_exc()}</pre>"
        print(traceback.format_exc())
        QtWidgets.QMessageBox.critical(
            self._parent_widget,
            "Ошибка",
            f"{text}{e_str}",
        )

    def show_warning(self, text: str) -> None:
        """
        Отображает всплывающее сообщение о предупреждении.
        """
        print("Внимание!", text)
        QtWidgets.QMessageBox.warning(
            self._parent_widget,
            "Внимание!",
            str(text),
        )

    def request_settings(self, code_name = "") -> None:
        """
        Посылает сигнал-запрос на открытие окна настроек
        для макроса с кодовым именем `code_name`.
        """
        if code_name == "":
            code_name = self.code_name
        self.settings_requested.emit(code_name)



class MacrosSingleCommand(Macros):
    """
    Графический интерфейс макроса, имеющего всего одну команду.

    **DEPRECATED**. Устаревший класс. Рекомендуется использовать класс `Macros` вместо этого
    в целях обеспечения возможности расширить функционал графического интерфейса макроса.
    """
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
        """
        Метод предназначен для выполнения непосредственных действий макроса
        (с обращениями к Компас-API).

        Метод безопасен при исключениях (Exceptions): он вызывается
        внутри обёртки `Macros.execute()`, поэтому дополнительно
        оборачивать его в try-except не требуется.

        Метод должен быть переопределён в наследуемом классе
        и не должен вызываться через `super()`.
        """
        raise Exception(
            "Метод execute_macros() должен быть переопределён в наследуемом классе "\
            "и не должен вызываться через `super()`"
        )
