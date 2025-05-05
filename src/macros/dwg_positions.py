"""
Макрос для определения, какие номера позиций расставлены на всех видах чертежа,
и какие номера среди них пропущены.

Макрос не берет информацию из спецификации, работает просто на основании
присутствующих линий обозначения позиций. Проверяется наличие номеров позиций
без пропусков, начиная от наименьшего до самого наибольшего уже проставленных
в видах чертежа номеров.

Для этого макроса нет GUI-интерфейса. Запускать макрос следует командой:

    python -m src.macros.dwg_positions

"""



from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path



def get_position_leaders():
    """
    В Компас16 была обнаружена такая проблема:
    запуск скрипта, всё отрабатывает нормально; после выполнения в Компасе
    каких-то действий с позициями (удаление, добавление, редактирование)
    и повторном запуске скрипта выдаются неактуальные данные.
    Решается закрытием и открытием чертежа в Компасе.
    """

    doc = open_doc2d()

    assert get_document_type(doc) == DocumentTypeEnum.type_2D

    vlm: KAPI7.IViewsAndLayersManager = doc.ViewsAndLayersManager
    views: KAPI7.IViews = vlm.Views

    positions: set[int] = set()

    for i in range(views.Count):
        view: KAPI7.IView = views.View(i)
        container: KAPI7.ISymbols2DContainer = KAPI7.ISymbols2DContainer(view)
        leaders: KAPI7.ILeaders = container.Leaders

        for j in range(leaders.Count):
            leader: KAPI7.IBaseLeader = leaders.Leader(j)
            pl = KAPI7.IPositionLeader(leader)
            if not pl is None:
                poss: KAPI7.IText = pl.Positions
                try:
                    for s in str(poss.Str).splitlines():
                        pos_number = int(s)
                        positions.add(pos_number)
                except:
                    pass

    return positions



if __name__ == "__main__":
    positions = get_position_leaders()

    print("present", positions)

    mx = max(positions)
    mn = min(positions)

    all_positions = set(range(mn, mx + 1))

    missing = all_positions.difference(positions)

    print("missing", missing)

