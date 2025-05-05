"""
Один из самых ранних макросов, созданных автором. Узко специализированный макрос.

Макрос позволяет быстро создавать сопряжения типа "Совпадение" между системой
координат (абсолютной или локальной) вставляемого компонента и системой координат
в сборке или, как правило, в компоновочной геометрии. Вместо систем координат
можно выбирать и контрольные и присоединительные точки.

Суть макроса в том, что при выполнении команды автоматически выставляются фильтры
выбора объектов на локальные системы координат и контрольные точки, а также
скрываются (так же, как командо "Меню -> Вид -> Скрыть" и "Меню -> Вид -> Скрыть
в компонентах") все элементы, кроме систем координат и контрольных точек на уровнях
текущей сборки и компонентов.

Некоторое время спустя автор пришел к выводу о том, что удобнее назначить горячую
клавишу на переключение видимости компоновочной геометрии, в которой отображаются
нужные ЛСК (командой "Меню -> Вид -> Скрыть"). А фильтры выбора в Компас16,
в котором работал автор, можно вынести на отдельную панель инструментов, и они
будут всегда доступны без всяких выпадающих меню.
Поэтому необходимость в этом макросе быстро исчезла.


Создание сопряжений по совпадению систем координат однозначно ориентирует и
размещает в пространстве компонент всего одним сопряжением.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import MacrosSingleCommand

from src.macros import lib_selection_filter
from src.macros import lib_visible_elements

from src.resources import get_resource_path


fast_mate_used = False
last_visible_elements = 0
last_selection_filter = 0


def fast_mate() -> None:
    global fast_mate_used, last_selection_filter, last_visible_elements

    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app = get_app7(iKompasObject7)
    active_doc: KAPI7.IKompasDocument3D = KAPI7.IKompasDocument3D(app.ActiveDocument)

    # Первый вызов
    if not fast_mate_used:
        print("Быстрое сопряжение: первый вызов")
        # Сохранение настроек, которые были до вызова
        fast_mate_used = not fast_mate_used
        last_selection_filter = lib_selection_filter.get_objects_filter(app)
        last_visible_elements = lib_visible_elements.get_visible_elements(active_doc)

        # Установить фильтр выбора объектов на "Системы координат" и "Контрольные точки"
        lib_selection_filter.set_objects_filter(
            app,
            lib_selection_filter.binaryObjectsFilter.CS | lib_selection_filter.binaryObjectsFilter.ControlPoints
        )

        # Скрыть всё, кроме систем координат и контрольных точек
        # и на уровне головной сборки, и в компонентах
        lib_visible_elements.set_visible_elements(
            active_doc,
            lib_visible_elements.VisibleElements.Axis \
            | lib_visible_elements.VisibleElements.ControlPoints \
            | lib_visible_elements.VisibleElements.Places \
            | lib_visible_elements.VisibleElements.Axis_InComponents \
            | lib_visible_elements.VisibleElements.ControlPoints_InComponents \
            | lib_visible_elements.VisibleElements.Places_InComponents \
            | lib_visible_elements.VisibleElements.LayoutGeometry \
            | lib_visible_elements.VisibleElements.LayoutGeometry_InComponents \
        )

        CMD_MATE_COINCIDENT = 20060  # Номер команды "Сопряжение Совпадение"

        # Выполнить сопряжение "Совпадение"
        if app.IsKompasCommandEnable(CMD_MATE_COINCIDENT):
            app.ExecuteKompasCommand(CMD_MATE_COINCIDENT)

    # Повторный вызов, чтобы вернуть состояние фильтра объектов и режим скрытия объектов обратно
    else:
        print("Быстрое сопряжение: второй вызов")
        fast_mate_used = not fast_mate_used
        lib_selection_filter.set_objects_filter(app, last_selection_filter)
        last_selection_filter = 0
        lib_visible_elements.set_visible_elements(active_doc, last_visible_elements)
        last_visible_elements = 0


class MacrosFastMate(MacrosSingleCommand):
    def __init__(self) -> None:
        super().__init__(
            "fast_mate",
            "Быстрое сопряжение",
            get_resource_path("img/macros/fast_mate.svg"),
            "Быстрое сопряжение\nПервое нажатие активирует режим Быстрого сопряжения," \
                "\nвторое - отключает его.",
        )

    def execute_macros(self) -> None:
        fast_mate()



if __name__ == "__main__":
    fast_mate()
    input("Нажмите Enter для выхода из режима Быстрого сопряжения: ")
    fast_mate()
