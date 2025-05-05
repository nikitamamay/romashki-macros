"""
Макрос для выбора компонентов с обозначением, соответствующему регулярному
выражению (`Regular Expression`).

Происходит выбор в текущей модели дочерних компонентов первого уровня
(нерекурсивно), если их обозначение соответствует какому-то заданному регулярному
выражению.

Исторически возникла необходимость выбрать компоненты, заимствованные из другого
проекта, то есть с другим обозначением, и покрасить их в другой цвет. Этот макрос
выполнял выделение этих компонентов.


Для этого макроса нет GUI-интерфейса. Запускать макрос следует командой:

    python -m src.macros.select_by_properties

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path


import traceback
import re



def select_parts_by_marking_re(marking_re: re.Pattern) -> None:
    """
    Выбирает дочерние компоненты первого уровня (нерекурсивно),
    обозначения которых соответствуют RegExp.

    Если перед запуском функции уже выбраны какие-то компоненты,
    то выборка происходит среди выбранных, а не среди всех.
    """
    doc, toppart = open_part()
    sm: KAPI7.ISelectionManager = doc.SelectionManager
    s_objs = ensure_list(sm.SelectedObjects)
    if len(s_objs) != 0:
        _check = lambda part: sm.IsSelected(part)
    else:
        _check = lambda part: True

    # FIXME а где-то здесь не нужно ли сбросить выделение ранее выбранных компонентов?

    for part in iterate_child_parts(toppart):
        if _check(part):
            m = marking_re.match(part.Marking)
            if m:
                sm.Select(part)



if __name__ == "__main__":
    r = re.compile(r"(?!2025\.0012).*", re.DOTALL | re.IGNORECASE)  # выбор компонентов, обозначения которых не_начинаются с "2025.0012"
    select_parts_by_marking_re(r)


