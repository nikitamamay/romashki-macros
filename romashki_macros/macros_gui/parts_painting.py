"""
Модуль графического интерфейса макроса `parts_painting`.

Графический интерфейс позволяет:
* сохранять краску текущей модели в список красок;
* покрасить текущую модель или выбранные компоненты, в том числе рекурсивно;
* покрасить \"По исходному объекту\"",
* настраивать:
    * опцию рекурсивной покраски дочерних компонентов;
    * список цветов и оптических свойств красок.

"""
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config

from ..gui import widgets as gui_widgets
from ..gui.macros import Macros

from ..utils.resources import get_resource_path

import re

from ..macros.parts_painting import *



re_html_color = re.compile(r'#[0-9,a-f,A-F]{6}\b', re.I)


class PaintInputWidget(QtWidgets.QWidget):
    data_edited = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self._csw = gui_widgets.WidgetColorSelect()
        self._csw.color_changed.connect(lambda: self.data_edited.emit())

        self._layout = QtWidgets.QGridLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self._layout.addWidget(QtWidgets.QLabel("Цвет:"), 0, 0, 1, 1)
        self._layout.addWidget(self._csw, 0, 1, 1, 2)

        self._slider_ambient = self._create_slider("Общий цвет", 0)
        self._slider_diffuse = self._create_slider("Диффузия", 1)
        self._slider_specularity = self._create_slider("Зеркальность", 2)
        self._slider_shininess = self._create_slider("Блеск", 3)
        self._slider_transparency = self._create_slider("Прозрачность", 5)
        self._slider_emission = self._create_slider("Излучение", 4)

        self.clear()

    def clear(self) -> None:
        self.set_data(DEFAULT_PAINT)

    def get_data(self) -> PaintData:
        color = self._csw.get_color()
        Am = self._slider_ambient.value() / 100
        Di = self._slider_diffuse.value() / 100
        Sp = self._slider_specularity.value() / 100
        Sh = self._slider_shininess.value() / 100
        Tr = self._slider_transparency.value() / 100
        Em = self._slider_emission.value() / 100
        return (color, Am, Di, Sp, Sh, Tr, Em)

    def set_data(self, paint_data: PaintData) -> None:
        color, Am, Di, Sp, Sh, Tr, Em = paint_data
        self._csw.set_color(color)
        self._slider_ambient.setValue(round(Am * 100))
        self._slider_diffuse.setValue(round(Di * 100))
        self._slider_specularity.setValue(round(Sp * 100))
        self._slider_shininess.setValue(round(Sh * 100))
        self._slider_transparency.setValue(round(Tr * 100))
        self._slider_emission.setValue(round(Em * 100))

    def _create_slider(self, text: str, row: int) -> QtWidgets.QSlider:
        lbl_info = QtWidgets.QLabel(text)

        lbl_value = QtWidgets.QLabel("  0")
        lbl_value.setFont(gui_widgets.get_monospace_font())

        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setPageStep(10)
        slider.setSingleStep(1)
        slider.setTickInterval(10)
        slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        slider.valueChanged.connect(lambda: lbl_value.setText(str(slider.value()).rjust(3)))
        slider.valueChanged.connect(lambda: self.data_edited.emit())

        self._layout.addWidget(lbl_info, row + 1, 0, 1, 1)
        self._layout.addWidget(slider, row + 1, 1, 1, 1)
        self._layout.addWidget(lbl_value, row + 1, 2, 1, 1)

        return slider


class MacrosPartsPainting(Macros):
    DATA_ROLE_PAINT_DATA = 100

    def __init__(self) -> None:
        super().__init__(
            "parts_painting",
            "Покраска деталей сборки"
        )

    def check_config(self) -> None:
        try:
            assert isinstance(self._config["paints_list"], list)
            for el in self._config["paints_list"]:
                assert isinstance(el, (list, tuple))
                name, paint = el
                color, Am, Di, Sp, Sh, Tr, Em = paint
                assert isinstance(name, str)
                assert isinstance(color, int)
                for number in [Am, Di, Sp, Sh, Tr, Em]:
                    assert isinstance(number, (float))
        except:
            self._config["paints_list"] = [
                ["Стандартная краска", DEFAULT_PAINT],
            ]
            config.save_delayed()

        try:
            assert isinstance(self._config["do_paint_children"], bool)
        except:
            self._config["do_paint_children"] = False
            config.save_delayed()

    def settings_widget(self) -> QtWidgets.QWidget:
        def _create_new_item(name=pretty_print_color(DEFAULT_PAINT[0]), paint=DEFAULT_PAINT) -> QtGui.QStandardItem:
            item = QtGui.QStandardItem()
            item.setData(name, QtCore.Qt.ItemDataRole.DisplayRole)
            item.setData(paint, self.DATA_ROLE_PAINT_DATA)
            item.setIcon(gui_widgets.get_icon_from_color(paint[0]))
            return item

        def _save_list() -> None:
            self._config["paints_list"].clear()
            for item in paints_selector.iterate_items():
                name = item.data(QtCore.Qt.ItemDataRole.DisplayRole)
                paint_data = item.data(self.DATA_ROLE_PAINT_DATA)
                paint = [name, paint_data]
                self._config["paints_list"].append(paint)
            self.toolbar_update_requested.emit(False)
            config.save_delayed()

        def _selection_changed() -> None:
            item = paints_selector.get_one_selected_item()
            if not item is None:
                piw.setEnabled(True)
                paint_data = item.data(self.DATA_ROLE_PAINT_DATA)
                piw.set_data(paint_data)
            else:
                piw.setEnabled(False)
                piw.clear()

        def _input_widget_data_changed() -> None:
            paint_data = piw.get_data()
            item = paints_selector.get_one_selected_item()
            if not item is None:
                name: str = item.data(QtCore.Qt.ItemDataRole.DisplayRole)
                if re_html_color.match(name):
                    s_color = pretty_print_color(paint_data[0])
                    item.setData(s_color, QtCore.Qt.ItemDataRole.DisplayRole)

                item.setData(paint_data, self.DATA_ROLE_PAINT_DATA)
                item.setIcon(gui_widgets.get_icon_from_color(paint_data[0]))
                _save_list()

        def _change_config() -> None:
            self._config["do_paint_children"] = cb_check_do_paint_children.isChecked()
            self.toolbar_update_requested.emit(False)
            config.save_delayed()

        def _remember_current_paint() -> None:
            def f():
                paint_data = get_current_color()
                name = pretty_print_color(paint_data[0])
                item = _create_new_item(name, paint_data)
                paints_selector.add_new_item(item)
                _save_list()
            self.execute(f)

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        cb_check_do_paint_children = QtWidgets.QCheckBox("Рекурсивно красить все дочерние компоненты")
        cb_check_do_paint_children.setToolTip(
            "Включить или отключить опцию рекурсивной покраски\n"
            "не только выбранных компонентов, но и входящих\n"
            "в него компонентов по всем уровням.\n\n"
            "Компоновочная геометрия и исключенные из расчета\n"
            "компоненты и их дочерние компоненты не красятся."
        )
        cb_check_do_paint_children.setChecked(self._config["do_paint_children"])
        cb_check_do_paint_children.stateChanged.connect(_change_config)

        btn_add_current_paint = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/macros/paint_pipette.svg")), "Сохранить краску текущей модели")
        btn_add_current_paint.clicked.connect(_remember_current_paint)

        paints_selector = gui_widgets.StringListSelector(_create_new_item)
        paints_selector.add_custom_button(btn_add_current_paint)
        for name, paint_data in self._config["paints_list"]:
            item = QtGui.QStandardItem()
            item.setData(name, QtCore.Qt.ItemDataRole.DisplayRole)
            item.setData(paint_data, self.DATA_ROLE_PAINT_DATA)
            item.setIcon(gui_widgets.get_icon_from_color(paint_data[0]))
            paints_selector.add_new_item(item)

        piw = PaintInputWidget()

        l.addWidget(cb_check_do_paint_children, 0, 0, 1, 1)
        l.addWidget(paints_selector, 1, 0, 1, 1)
        l.addWidget(piw, 2, 0, 1, 1)

        piw.data_edited.connect(_input_widget_data_changed)
        paints_selector.selection_changed.connect(_selection_changed)
        paints_selector.list_changed.connect(lambda: self.toolbar_update_requested.emit(False))
        paints_selector.list_changed.connect(_save_list)

        paints_selector.clear_selection()

        return w

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        def _apply_paint(paint_index: int) -> None:
            name, paint = self._config["paints_list"][paint_index]
            self.execute(
                lambda: paint_parts(paint, UseColorEnum.useColorOur, self._config["do_paint_children"])
            )

        def _do_paint_children_handler(state: bool) -> None:
            self._config["do_paint_children"] = state
            config.save_delayed()

        btn_paint = gui_widgets.ButtonWithList(QtGui.QIcon(get_resource_path("img/macros/paint_bucket.svg")), "")
        btn_paint.clicked.connect(lambda: self.execute(self._paint_with_first_color))
        btn_paint.setToolTip("Покрасить текущую модель первой краской в списке")

        for i, m in enumerate(self._config["paints_list"]):
            name, paint = m
            btn_paint.menu().addAction(gui_widgets.get_icon_from_color(paint[0]), name, (lambda i: lambda: _apply_paint(i))(i))

        btn_paint.menu().addSeparator()

        a_paint_like_owner = QtWidgets.QAction(
            QtGui.QIcon(get_resource_path("img/macros/paint.svg")),
            "Покрасить \"По исходному объекту\"",
            btn_paint.menu()
        )
        a_paint_like_owner.setToolTip("Покрасить выбранные компоненты способом \"По исходному объекту\"")
        a_paint_like_owner.triggered.connect(
            lambda: self.execute(
                lambda: paint_parts(None, UseColorEnum.useColorOwner, self._config["do_paint_children"])
            )
        )
        btn_paint.menu().addAction(a_paint_like_owner)

        btn_paint.menu().addSeparator()

        a_paint_children = QtWidgets.QAction("Красить все дочерние компоненты", btn_paint.menu())
        a_paint_children.setToolTip(
            "Включить или отключить опцию рекурсивной покраски\n"
            "не только выбранных компонентов, но и входящих\n"
            "в него компонентов по всем уровням.\n\n"
            "Компоновочная геометрия и исключенные из расчета\n"
            "компоненты и их дочерние компоненты не красятся."
        )
        a_paint_children.setCheckable(True)
        a_paint_children.setChecked(self._config["do_paint_children"])
        a_paint_children.toggled.connect(_do_paint_children_handler)
        btn_paint.menu().addAction(a_paint_children)

        btn_paint.menu().addAction(
            QtGui.QIcon(get_resource_path("img/settings.svg")),
            "Настроить список...",
            self.request_settings,
        )

        return {
            "кнопка покраски": btn_paint,
        }

    def _paint_with_first_color(self):
        if len(self._config["paints_list"]) == 0:
            paint = DEFAULT_PAINT
        else:
            name, paint = self._config["paints_list"][0]
        paint_parts(paint, UseColorEnum.useColorOur, self._config["do_paint_children"])

