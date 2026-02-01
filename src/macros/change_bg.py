"""
Макрос предназначен для [циклической] перемены цвета фона в рабочем окне модели
и чертежа по заранее заданному списку цветов.

Исторически возникла необходимость быстрого переключения между белым цветом фона
и градиентным темно-серым, соответствующим темной теме Компаса, чтобы выполнить
скриншот 3D-модели на белом фоне для вставки в пояснительную записку или презентацию.


Это самый первый созданный автором полноценный макрос: идея макроса датируется
августом-сентябрём 2022 года.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import MacrosSingleCommand

from src.resources import get_resource_path


DEFAULT_COLOR = (0xffffff, 0xffffff)
""" Цвет рабочего поля в традиционном виде: `[0xRRGGBB, 0xRRGGBB]`. """


def obtain_current_color() -> tuple[int, int]:
    """
    Возвращает цвет рабочего поля модели в традиционном виде: `[0xRRGGBB, 0xRRGGBB]`
    для градиентного перехода сверху вниз соответственно; если у рабочего поля
    сплошная одноцветная заливка, возвращает два одинаковых цвета.
    """
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    view_params = iKompasObject5.GetParamStruct(LDefin2D.ko_ViewColorParam)
    iKompasObject5.ksGetSysOptions(LDefin2D.MODEL_VIEWCOLOR_OPTIONS, view_params)

    if view_params.useGradient == True:
        top, bottom = [color_kompas_to_traditional(c) for c in [view_params.topColor, view_params.bottomColor]]
        print(f"Текущий цвет фона: градиент от #{pretty_print_color(top)} до #{pretty_print_color(bottom)}.")
        return (top, bottom)
    else:
        c = color_kompas_to_traditional(view_params.color)
        print(f"Текущий цвет фона: сплошной #{pretty_print_color(c)}.")
        return (c, c)


def change_bg(color: tuple[int, int]) -> None:
    """
    Цвета должны быть представлены в традиционном виде: `[0xRRGGBB, 0xRRGGBB]`,
    задают градиентный переход сверху вниз соответственно. Если оба цвета
    одинаковые, то задается сплошная заливка.
    """
    assert isinstance(color, (list, tuple))
    assert len(color) == 2
    for el in color: assert isinstance(el, int)

    iKompasObject5, iKompasObject7 = get_kompas_objects()
    view_params = iKompasObject5.GetParamStruct(LDefin2D.ko_ViewColorParam)
    iKompasObject5.ksGetSysOptions(LDefin2D.MODEL_VIEWCOLOR_OPTIONS, view_params)

    rgb_top, rgb_bottom = [color_traditional_to_kompas(c) for c in color]

    if rgb_top == rgb_bottom:
        view_params.useGradient = False
        view_params.color = rgb_top
        print(f"Установка цвета фона на сплошной #{pretty_print_color(rgb_top)}.")
    else:
        view_params.useGradient = True
        view_params.color = rgb_top
        view_params.topColor = rgb_top
        view_params.bottomColor = rgb_bottom
        print(f"Установка цвета фона на градиент от #{pretty_print_color(rgb_top)} до #{pretty_print_color(rgb_bottom)}.")

    if not iKompasObject5.ksSetSysOptions(LDefin2D.VIEWCOLOR_OPTIONS, view_params):
        raise Exception("ksSetSysOptions for 2d was not succeed")
    if not iKompasObject5.ksSetSysOptions(LDefin2D.MODEL_VIEWCOLOR_OPTIONS, view_params):
        raise Exception("ksSetSysOptions for 3d was not succeed")


def get_name_from_color(color: tuple[int, int]) -> str:
    if color[0] == color[1]:
        return f"#{pretty_print_color(color[0])}"
    return f"#{pretty_print_color(color[0])} - #{pretty_print_color(color[1])}"


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
                print(f"Добавлен в список цветов цвет фона [#{pretty_print_color(color[0])}, #{pretty_print_color(color[1])}].")
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



if __name__ == "__main__":

    iKompasObject5, iKompasObject7 = get_kompas_objects()
    view_params = iKompasObject5.GetParamStruct(LDefin2D.ko_ViewColorParam)
    iKompasObject5.ksGetSysOptions(LDefin2D.MODEL_VIEWCOLOR_OPTIONS, view_params)

    # цвета - в формате Компаса, задом наперед: 0xBBGGRR
    t = 0x0000ff  # red
    b = 0x00ff00  # blue
    c = 0xff0000  # green

    view_params.useGradient = False
    view_params.color = c
    view_params.topColor = t
    view_params.bottomColor = b

    if not iKompasObject5.ksSetSysOptions(LDefin2D.VIEWCOLOR_OPTIONS, view_params):
        raise Exception("ksSetSysOptions for 2d was not succeed")
    if not iKompasObject5.ksSetSysOptions(LDefin2D.MODEL_VIEWCOLOR_OPTIONS, view_params):
        raise Exception("ksSetSysOptions for 3d was not succeed")
