"""
Макрос предоставляет функционал для создания скрытых слоев, как правило,
во всех видах чертежа.

По умолчанию скрытые слои создаются с номером 900 и с темно-желтым цветом.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import MacrosSingleCommand

from src.resources import get_resource_path


def dwg_create_hidden_layers(hidden_layer_number = 900, color = 0x999900, do_create_everywhere = True) -> None:
    def create_layer(view: KAPI7.IView) -> bool:
        rc = False
        layers: KAPI7.ILayers = view.Layers
        hidden_layer: KAPI7.ILayer = layers.LayerByNumber(hidden_layer_number)
        if hidden_layer == None:
            current_layer_number: int = view.LayerNumber

            hidden_layer = layers.Add()
            hidden_layer.Name = "Скрытое"
            hidden_layer.Color = color_traditional_to_kompas(color)
            hidden_layer.LayerNumber = hidden_layer_number
            hidden_layer.Update()

            view.LayerNumber = current_layer_number
            view.Update()

            rc = True

        hidden_layer.Visible = False
        hidden_layer.Printable = False
        hidden_layer.Update()

        view.Update()
        return rc

    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app: KAPI7.IApplication = get_app7(iKompasObject7)
    doc: KAPI7.IKompasDocument2D = KAPI7.IKompasDocument2D(app.ActiveDocument)

    assert not doc is None

    vlm: KAPI7.IViewsAndLayersManager = doc.ViewsAndLayersManager
    views: KAPI7.IViews = vlm.Views

    new_layers_count: int = 0
    i: int = 0

    if do_create_everywhere:
        for do in views:
            do: KAPI7.IDrawingObject
            view: KAPI7.IView = KAPI7.IView(do)

            i += int(create_layer(view))

        print(f"Общее количество видов: {i}. Созданы скрытые слои в {new_layers_count} видах.")
    else:
        view: KAPI7.IView = views.ActiveView
        is_created = create_layer(view)
        if is_created:
            print(f"Создан скрытый слой в текущем виде.")
        else:
            print(f"Скрытый слой уже присутствует в текущем виде.")


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



if __name__ == "__main__":
    dwg_create_hidden_layers(900)

