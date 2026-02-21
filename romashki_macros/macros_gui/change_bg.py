"""
Модуль графического интерфейса макроса `change_bg`.

Графический интерфейс позволяет:
* [циклически] переменять цвет фона в рабочем окне модели и чертежа
    по заранее заданному списку цветов;
* настраивать список цветов;
* сохранять текущий цвет фона рабочего окна в список цветов.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config

from ..gui import widgets as gui_widgets
from ..gui.macros import MacrosSingleCommand

from ..utils.resources import get_resource_path


from ..macros.change_bg import *


def get_name_from_color(color: tuple[int, int]) -> str:
    """
    Возвращает строковое представление цвета `color`:
    * для сплошного цвета: `#RRGGBB`;
    * для градиента: `#RRGGBB - #RRGGBB` (верх и низ соответственно).
    """
    if color[0] == color[1]:
        return f"{pretty_print_color(color[0])}"
    return f"{pretty_print_color(color[0])} - {pretty_print_color(color[1])}"



class ColorInputWidget(QtWidgets.QWidget):
    data_edited = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self._lbl_color = gui_widgets.LabelGradientColor()
        self._lbl_color.setMinimumSize(50, 50)

        self._btn_change_top = QtWidgets.QPushButton("Изменить верхний цвет")
        self._btn_change_top.clicked.connect(lambda: self.change_color(True))

        self._btn_remove_gradient = QtWidgets.QPushButton("Убрать градиент")
        self._btn_remove_gradient.clicked.connect(self.remove_gradient)

        self._btn_change_bottom = QtWidgets.QPushButton("Изменить нижний цвет")
        self._btn_change_bottom.clicked.connect(lambda: self.change_color(False))

        self._layout = QtWidgets.QGridLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._lbl_color, 0, 0, 3, 1)
        self._layout.addWidget(self._btn_change_top, 0, 1, 1, 1)
        self._layout.addWidget(self._btn_remove_gradient, 1, 1, 1, 1)
        self._layout.addWidget(self._btn_change_bottom, 2, 1, 1, 1)
        self.setLayout(self._layout)

    def clear(self) -> None:
        self._lbl_color.set_gradient_color(DEFAULT_COLOR)

    def get_data(self) -> tuple[int, int]:
        return self._lbl_color.get_gradient_color()

    def set_data(self, color: tuple[int, int]) -> None:
        self._color = color
        self._lbl_color.set_gradient_color(self._color)

    def remove_gradient(self) -> None:
        self._lbl_color.set_bottom_color(self._lbl_color.get_top_color())
        self.data_edited.emit()

    def change_color(self, is_top: bool) -> None:
        title = "Изменить верхний цвет" if not is_top else "Изменить нижний цвет"
        initial_color = self._lbl_color.get_gradient_color()[int(is_top)]

        qcolor: QtGui.QColor = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(initial_color),
            self,
            title,
        )

        if qcolor.isValid():
            c: int = qcolor.rgb() & 0xffffff

            if is_top:
                self._lbl_color.set_top_color(c)
            else:
                self._lbl_color.set_bottom_color(c)
            self.data_edited.emit()



class MacrosChangeBackgroundColor(MacrosSingleCommand):
    DATA_ROLE_COLOR = 101

    def __init__(self) -> None:
        super().__init__(
            "change_bg",
            "Смена цвета фона",
            get_resource_path("img/macros/bg_color.svg"),
            "Сменить цвет фона рабочей области",
        )

    def check_config(self) -> None:
        try:
            assert "colors" in self._config
            assert isinstance(self._config["colors"], list)
            assert len(self._config["colors"]) > 0
            for el in self._config["colors"]:
                assert isinstance(el, (list, tuple))
                assert len(el) == 2
                for rgb in el:
                    assert isinstance(rgb, int)
                    assert 0x000000 <= rgb <= 0xffffff
        except:
            self._config["colors"] = [
                DEFAULT_COLOR,
            ]
            config.save_delayed()

    def execute_macros(self) -> None:
        if len(self._config["colors"]) == 0:
            self.request_settings()
            raise Exception(f"В списке цветов фона нет ни одного цвета!")

        color = obtain_current_color()
        for i, c in enumerate(self._config["colors"]):
            if c[0] == color[0] and c[1] == color[1]:
                i = (i + 1) % len(self._config["colors"])
                break
        else:
            i = 0
            btn = QtWidgets.QMessageBox.question(
                self._parent_widget,
                "Текущий цвет фона",
                f"<p>Текущего цвета фона рабочей области<br>{get_name_from_color(color)}<br>нет в списке цветов.</p>"\
                "<p>Добавить текущий цвет в список цветов, чтобы не потерять его?</p>",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.Yes,
            )
            if btn == QtWidgets.QMessageBox.StandardButton.Yes:
                self._config["colors"].append(color)
                print(f"Добавлен в список цветов цвет фона [{pretty_print_color(color[0])}, {pretty_print_color(color[1])}].")
        change_bg(self._config["colors"][i])

    def settings_widget(self) -> QtWidgets.QWidget:
        def _create_new_item(color = DEFAULT_COLOR) -> QtGui.QStandardItem:
            item = QtGui.QStandardItem()
            item.setData(get_name_from_color(color), QtCore.Qt.ItemDataRole.DisplayRole)
            item.setData(color, self.DATA_ROLE_COLOR)
            item.setIcon(gui_widgets.get_icon_from_gradient(color))
            return item

        def _save_list() -> None:
            self._config["colors"].clear()
            for item in colors_selector.iterate_items():
                color = item.data(self.DATA_ROLE_COLOR)
                self._config["colors"].append(color)
            config.save_delayed()

        def _selection_changed() -> None:
            item = colors_selector.get_one_selected_item()
            if item is not None:
                ciw.setEnabled(True)
                color = item.data(self.DATA_ROLE_COLOR)
                ciw.set_data(color)
            else:
                ciw.setEnabled(False)
                ciw.clear()

        def _input_widget_data_changed() -> None:
            color = ciw.get_data()
            item = colors_selector.get_one_selected_item()
            if item is not None:
                item.setData(get_name_from_color(color), QtCore.Qt.ItemDataRole.DisplayRole)
                item.setData(color, self.DATA_ROLE_COLOR)
                item.setIcon(gui_widgets.get_icon_from_gradient(color))
                _save_list()

        def _add_current() -> None:
            def f():
                color = obtain_current_color()
                item = _create_new_item(color)
                colors_selector.add_new_item(item)
            self.execute(f)

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        btn_remember_current = QtWidgets.QPushButton("Запомнить текущий цвет")
        btn_remember_current.setToolTip("Добавить текущий цвет рабочей области\nв список цветов")
        btn_remember_current.clicked.connect(_add_current)

        colors_selector = gui_widgets.StringListSelector(_create_new_item)
        colors_selector.set_name_editing_allowed(False)
        colors_selector.add_custom_button(btn_remember_current)

        for color in self._config["colors"]:
            item = _create_new_item(color)
            colors_selector.add_new_item(item)

        ciw = ColorInputWidget()

        l.addWidget(colors_selector, 0, 0, 1, 1)
        l.addWidget(ciw, 1, 0, 1, 1)

        ciw.data_edited.connect(_input_widget_data_changed)
        colors_selector.selection_changed.connect(_selection_changed)
        colors_selector.list_changed.connect(lambda: self.toolbar_update_requested.emit(False))
        colors_selector.list_changed.connect(_save_list)

        colors_selector.clear_selection()

        return w

