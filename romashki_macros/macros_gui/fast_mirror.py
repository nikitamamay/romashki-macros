
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *

from ..gui.macros import Macros

from ..utils.resources import get_resource_path


from ..macros.fast_mirror import *


class FastMirrorMacros(Macros):
    def __init__(self) -> None:
        super().__init__(
            "fast_mirror",
            "Быстрый зеркальный массив"
        )

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        btn_go = QtWidgets.QToolButton()
        btn_go.setIcon(QtGui.QIcon(get_resource_path("img/macros/fast_mirror.svg")))
        btn_go.clicked.connect(lambda: self.execute(fast_mirror))
        btn_go.setToolTip("Создать зеркальный массив выбранных тел\nотносительно выбранной плоскости")

        return {
            "кнопка запуска макроса": btn_go,
        }
