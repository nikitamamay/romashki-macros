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


def obtain_current_color() -> tuple[int, int]:
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    view_params = iKompasObject5.GetParamStruct(LDefin2D.ko_ViewColorParam)
    iKompasObject5.ksGetSysOptions(LDefin2D.MODEL_VIEWCOLOR_OPTIONS, view_params)

    if view_params.useGradient == True:
        top, bottom = [color_kompas_to_traditional(c) for c in [view_params.topColor, view_params.bottomColor]]
        return (top, bottom)
    else:
        c = color_kompas_to_traditional(view_params.color)
        return (c, c)


def change_bg(color: list[int,int]) -> None:
    """
        Цвет должны быть представлен в традиционном виде: [0xRRGGBB, 0xRRGGBB].
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
        print(f"Setting background color to solid #{pretty_print_color(rgb_top)}.")
    else:
        view_params.useGradient = True
        view_params.color = rgb_top
        view_params.topColor = rgb_top
        view_params.bottomColor = rgb_bottom
        print(f"Setting background color to gradient #{pretty_print_color(rgb_top)} to #{pretty_print_color(rgb_bottom)}.")

    if not iKompasObject5.ksSetSysOptions(LDefin2D.VIEWCOLOR_OPTIONS, view_params):
        raise Exception("ksSetSysOptions for 2d was not succeed")
    if not iKompasObject5.ksSetSysOptions(LDefin2D.MODEL_VIEWCOLOR_OPTIONS, view_params):
        raise Exception("ksSetSysOptions for 3d was not succeed")



class MacrosChangeBackgroundColor(MacrosSingleCommand):
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
                obtain_current_color(),
                [0xffffff, 0xffffff],
            ]
            config.save_delayed()

    def execute_macros(self) -> None:
        color = obtain_current_color()
        for i, c in enumerate(self._config["colors"]):
            if c[0] == color[0] and c[1] == color[1]:
                break
        i = (i + 1) % len(self._config["colors"])
        change_bg(self._config["colors"][i])

    def settings_widget(self) -> QtWidgets.QWidget:
        def _apply_changes() -> None:
            colors: list[tuple[int,int]] = lv.get_colors()
            if len(colors) == 0:
                lv.add_color()
                _apply_changes()
                return
            self._config["colors"] = colors
            config.save_delayed()

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        lv = gui_widgets.ColorsListView()
        lv.set_colors(self._config["colors"])
        lv.data_changed.connect(_apply_changes)

        btn_add = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/add.svg")), "")
        btn_add.setToolTip("Добавить цвет")
        btn_add.clicked.connect(lambda: lv.add_color())
        btn_add.clicked.connect(lambda: _apply_changes())

        btn_remove = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/delete.svg")), "")
        btn_remove.setToolTip("Удалить выбранный цвет")
        btn_remove.clicked.connect(lambda: lv.remove_selected())
        btn_remove.clicked.connect(lambda: _apply_changes())

        l.addWidget(QtWidgets.QLabel("Список цветов:"), 0, 0, 1, 2)
        l.addWidget(lv, 1, 0, 3, 1)
        l.addWidget(btn_add, 1, 1, 1, 1)
        l.addWidget(btn_remove, 2, 1, 1, 1)

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
