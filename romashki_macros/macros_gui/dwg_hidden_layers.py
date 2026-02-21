"""
Модуль графического интерфейса макроса `dwg_hidden_layers`.

Графический интерфейс позволяет:
* создавать скрытые слои;
* настраивать для вновь создаваемых скрытых слоёв:
    * номер;
    * цвет;
    * опцию создания сразу во всех видах чертежа или только в текущем виде.

"""
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config
from ..utils import config_reader

from ..gui import widgets as gui_widgets
from ..gui.macros import MacrosSingleCommand

from ..utils.resources import get_resource_path


from ..macros.dwg_hidden_layers import *


class MacrosDWGHiddenLayers(MacrosSingleCommand):
    def __init__(self) -> None:
        super().__init__(
            "dwg_hidden_layers",
            "Создание скрытых слоёв в чертеже",
            get_resource_path("img/macros/hidden_layers.svg"),
            "Создать скрытые слои в чертеже"
        )

    def check_config(self) -> None:
        config_reader.ensure_dict_value(self.config(), "number", int, 900)
        config_reader.ensure_dict_value(self.config(), "color", int, 0x999900)
        config_reader.ensure_dict_value(self.config(), "do_create_in_every_view", bool, True)

    def execute_macros(self) -> None:
        dwg_create_hidden_layers(
            self.config()["number"],
            self.config()["color"],
            self.config()["do_create_in_every_view"],
        )

    def settings_widget(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        sb = QtWidgets.QSpinBox()
        sb.setRange(-10**9, 10**9)
        sb.setValue(self.config()["number"])
        sb.valueChanged.connect(self.set_number)

        l.addWidget(QtWidgets.QLabel("Номер скрытых слоёв:"), 0, 0)
        l.addWidget(sb, 0, 1)

        cs = gui_widgets.WidgetColorSelect(self.config()["color"])
        cs.color_changed.connect(self.set_new_color)

        l.addWidget(QtWidgets.QLabel("Цвет скрытых слоёв:"), 1, 0)
        l.addWidget(cs, 1, 1)

        cb = QtWidgets.QCheckBox("Создавать скрытые слои во всех видах, а не только в текущем")
        cb.setChecked(self.config()["do_create_in_every_view"])
        cb.stateChanged.connect(self.set_create_everywhere_flag)

        l.addWidget(cb, 2, 0, 1, 2)
        return w

    def set_number(self, new_value: int) -> None:
        self.config()["number"] = new_value
        config.save_delayed()

    def set_new_color(self, new_value: int) -> None:
        self.config()["color"] = new_value
        config.save_delayed()

    def set_create_everywhere_flag(self, new_value: bool) -> None:
        self.config()["do_create_in_every_view"] = new_value
        config.save_delayed()

