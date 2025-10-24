"""
Макрос предоставляет функционал для включения режима "Не беспокоить".
То есть для ручного отключения всплывающих окон, например с просьбами перестроить
3D-модель или чертеж, с автоматическим ответом "Нет" на эти предложения.

Следует иметь в виду, что некоторые операции в режиме "Не беспокоить" могут
работать некорректно. Даже те, которые не предполагают таких всплывающих окон.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path


def set_silent_mode(is_silent: bool) -> None:
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app = get_app7(iKompasObject7)
    app.HideMessage = 2 if is_silent else 0
    print(f"стало app.HideMessage={app.HideMessage} (is_silent={is_silent})")


def get_silent_mode() -> bool:
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app = get_app7(iKompasObject7)
    return app.HideMessage != 0



class MacrosDoNotDisturb(Macros):
    def __init__(self) -> None:
        super().__init__(
            "do_not_disturb",
            "Режим \"Не беспокоить\"",
        )

    def check_config(self) -> None:
        pass

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        def _switch_mode() -> None:
            is_silent = btn_switch.isChecked()
            self.execute(lambda: set_silent_mode(is_silent))

        btn_switch = QtWidgets.QToolButton()
        btn_switch.setIcon(QtGui.QIcon(get_resource_path("img/macros/do_not_disturb.svg")))
        btn_switch.setToolTip("Переключить режим \"Не беспокоить\"")
        btn_switch.setCheckable(True)
        btn_switch.setChecked(get_silent_mode() if is_kompas_running() else False)
        btn_switch.toggled.connect(_switch_mode)

        return {
            "переключатель режима \"Не беспокоить\"": btn_switch,
        }


if __name__ == "__main__":
    # set_silent_mode(True)
    set_silent_mode(False)
