
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config

from ..gui import widgets as gui_widgets
from ..gui.macros import Macros

from ..utils.resources import get_resource_path

from ..macros.do_not_disturb import *


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

