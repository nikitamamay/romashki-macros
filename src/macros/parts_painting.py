"""
Макрос для покраски компонентов.

Макрос предоставляет функционал:
* для сохранения краски текущей модели, чтобы использовать её повторно.

* для покраски компонентов в какой-то определенный цвет.

    Исторически возникла необходимость вернуть краску по умолчанию для детали
    после установки материала через штатный справочник "Материалы и сортаменты",
    который зачем-то перекрашивает деталь в темно-серый цвет и меняет её
    оптические свойства.

* для покраски дочерних компонентов в цвет "По исходному объекту".
То есть, чтобы дочерние компоненты имели тот же цвет, что и цвет сборки.

    Например, для задания цвета сварной рамы в головной сборке машины, чтобы
    все входящие в раму детали также приняли этот цвет.


Перекрашивание может выполняться как для выбранного единичного компонента, так и
рекурсивно для его компонентов тоже.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path



DEFAULT_PAINT = [0x909090, 0.5, 0.6, 0.8, 0.8, 0.0, 0.5]  # краска по-умолчанию для деталей в Компас16


class UseColorEnum:
    useColorUnknown = -1  # тип не определен
    useColorOur = 0  # собственный цвет
    useColorOwner = 1   # цвет хозяина (исходного объекта)
    useColorSource = 2  # цвет источника
    useColorLayer = 3  # Цвет слоя


def paint_parts(paint, useColor = UseColorEnum.useColorOur, is_recursive = False) -> None:
    def apply_color(part: KAPI7.IPart7):
        if part.IsLayoutGeometry or KAPI7.IFeature7(part).Excluded:
            print(f"Пропускается от перекрашивания: {part.Marking} {part.Name} {part.FileName}")
            return False
        print(f"Перекрашивается: {part.Marking} {part.Name} {part.FileName}")
        cp = KAPI7.IColorParam7(part)
        cp.UseColor = useColor
        if useColor == UseColorEnum.useColorOur:
            color, Am, Di, Sp, Sh, Tr, Em = paint
            color_kompas = color_traditional_to_kompas(color)
            cp.SetAdvancedColor(color_kompas, Am, Di, Sp, Sh, 1 - Tr, Em)
        part.Update()
        return True

    doc, toppart = open_part()
    parts: list[KAPI7.IPart7] = get_selected(doc, KAPI7.IPart7)

    if len(parts) == 0:
        if is_recursive:
            raise Exception("Недопускается перекрашивание текущей модели и её дочерних компонентов."
                " Выберите каждый нужный компонент отдельно.")
        print(f"Компоненты не выбраны. Будет перекрашиваться текущая модель.")
        parts.append(toppart)
    else:
        print(f"Выбрано компонентов: {len(parts)}. ")

    for part in parts:
        apply_color(part)

    if is_recursive:
        for part in parts:
            apply_to_children_r(part, apply_color)

    print("Перекрашивание окончено.")


def get_current_color() -> tuple[int, float, float, float, float, float, float]:
    doc, part = open_part()
    cp = KAPI7.IColorParam7(part)
    _, color_kompas, Am, Di, Sp, Sh, Tr, Em = cp.GetAdvancedColor()
    Tr = 1 - Tr
    color = color_kompas_to_traditional(color_kompas)
    paint = [color, Am, Di, Sp, Sh, Tr, Em]
    print("Текущие параметры:", paint)
    return paint


def get_icon_from_color(color: int) -> QtGui.QIcon:
    p = QtGui.QPixmap(16, 16)
    painter = QtGui.QPainter(p)
    painter.setBrush(QtGui.QColor(color))
    painter.setPen(QtGui.QColorConstants.Black)
    painter.drawRect(0, 0, 15, 15)
    painter.end()
    return QtGui.QIcon(p)



class MacrosPartsPainting(Macros):
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
                ["Стандартная краска Компас v16", DEFAULT_PAINT],
            ]
            config.save_delayed()

        try:
            assert isinstance(self._config["do_paint_children"], bool)
        except:
            self._config["do_paint_children"] = False
            config.save_delayed()

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
            btn_paint.menu().addAction(get_icon_from_color(paint[0]), name, (lambda i: lambda: _apply_paint(i))(i))

        btn_paint.menu().addSeparator()

        btn_paint.menu().addAction(
            QtGui.QIcon(get_resource_path("img/macros/paint_pipette.svg")),
            "Сохранить краску текущей модели",
            lambda: self.execute(self._remember_current_paint),
        )

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
        a_paint_children.setToolTip("Включить или отключить опцию рекурсивной покраски\n"
                                    "не только выбранных компонентов, но и входящих\n"
                                    "в него компонентов по всем уровням.\n\n"
                                    "Компоновочная геометрия и исключенные из расчета\n"
                                    "компоненты и их дочерние компоненты не красятся.")
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

    def _remember_current_paint(self) -> None:
        paint = get_current_color()
        name = "#" + pretty_print_color(paint[0])
        self._config["paints_list"].append([name, paint])
        config.save_delayed()
        self.toolbar_update_requested.emit(True)


if __name__ == "__main__":
    paint_parts()
