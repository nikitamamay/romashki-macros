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
        try:
            assert "number" in self._config
            assert isinstance(self._config["number"], int)
        except:
            self._config["number"] = 900
            config.save_delayed()

        try:
            assert "color" in self._config
            assert isinstance(self._config["color"], int)
            assert 0x000000 <= self._config["color"] <= 0xffffff
        except:
            self._config["color"] = 0x999900
            config.save_delayed()

        try:
            assert "do_create_in_every_view" in self._config
            assert isinstance(self._config["do_create_in_every_view"], bool)
        except:
            self._config["do_create_in_every_view"] = True
            config.save_delayed()

    def execute_macros(self) -> None:
        dwg_create_hidden_layers(
            self._config["number"],
            self._config["color"],
            self._config["do_create_in_every_view"],
        )

    def settings_widget(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        sb = QtWidgets.QSpinBox()
        sb.setRange(-10**9, 10**9)
        sb.setValue(self._config["number"])
        sb.valueChanged.connect(self.set_number)

        l.addWidget(QtWidgets.QLabel("Номер скрытых слоёв:"), 0, 0)
        l.addWidget(sb, 0, 1)

        cs = gui_widgets.WidgetColorSelect(self._config["color"])
        cs.color_changed.connect(self.set_new_color)

        l.addWidget(QtWidgets.QLabel("Цвет скрытых слоёв:"), 1, 0)
        l.addWidget(cs, 1, 1)

        cb = QtWidgets.QCheckBox("Создавать скрытые слои во всех видах, а не только в текущем")
        cb.setChecked(self._config["do_create_in_every_view"])
        cb.stateChanged.connect(self.set_create_everywhere_flag)

        l.addWidget(cb, 2, 0, 1, 2)
        return w

    def set_number(self, new_value) -> None:
        self._config["number"] = new_value
        config.save()

    def set_new_color(self, new_value: int) -> None:
        self._config["color"] = new_value
        config.save()

    def set_create_everywhere_flag(self, new_value: bool) -> None:
        self._config["do_create_in_every_view"] = new_value
        config.save()

