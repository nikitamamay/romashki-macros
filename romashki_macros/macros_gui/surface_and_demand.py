
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config

from ..gui.macros import MacrosSingleCommand

from ..utils.resources import get_resource_path


from ..macros.surface_and_demand import *


class MacrosSurfaceRoughnessAndTechDemand(MacrosSingleCommand):
    def __init__(self) -> None:
        super().__init__(
            "surface_and_demand",
            "Шероховатость и ТТ",
            get_resource_path("img/macros/surface_and_demand.svg"),
            "Вставить на чертеж неуказанную шероховатость\nи технические требования",
        )

    def check_config(self) -> None:
        try:
            assert isinstance(self._config["surface_finish_text"], str)
        except:
            self._config["surface_finish_text"] = "Ra 25"
            config.save_delayed()

        try:
            assert isinstance(self._config["technical_demand"], str)
        except:
            self._config["technical_demand"] = "* Размеры для справок.\nОбщие допуски по ГОСТ 30893.2 - mK."
            config.save_delayed()

    def execute_macros(self) -> None:
        set_surface_finish(self._config["surface_finish_text"])
        set_technical_demand(self._config["technical_demand"])

    def settings_widget(self) -> QtWidgets.QWidget:
        def _apply_changes() -> None:
            self._config["surface_finish_text"] = le_sf.text()
            self._config["technical_demand"] = te_td.toPlainText()
            # print(repr(te_td.toPlainText()))
            config.save_delayed()

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        le_sf = QtWidgets.QLineEdit(self._config["surface_finish_text"])
        le_sf.textChanged.connect(_apply_changes)

        te_td = QtWidgets.QTextEdit()
        te_td.setPlainText(self._config["technical_demand"])
        te_td.textChanged.connect(_apply_changes)

        l.addWidget(QtWidgets.QLabel("Текст неуказанной шероховатости:"), 0, 0, 1, 1)
        l.addWidget(le_sf, 0, 1, 1, 1)
        l.addWidget(QtWidgets.QLabel("Текст технических требований:"), 1, 0, 1, 2)
        l.addWidget(te_td, 2, 0, 1, 2)

        return w


