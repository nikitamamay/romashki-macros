"""
Макрос предоставляет функционал по управлению включением компонентов в спецификацию.

Макрос актуален для старых версий Компаса, в которых нет возможности в штатной
панели свойств выключить вхождение в спецификацию у выделенных компонентов, а нужно
для каждого компонента (по одному) заходить в отдельное меню свойств компонента и
выключать это там.

"""
from .lib_macros.core import *


def switch_spc_inclusion(new_state: bool|None = None) -> None:
    """
    Изменяет флаг включения в спецификацию на `new_state`
    у выбранных компонентов текущей 3D-модели.

    Если `new_state is None`, то переключает флаг на противоположный.
    """
    doc3d, toppart = open_part()

    parts: list[KAPI7.IPart7] = get_selected(doc3d, KAPI7.IPart7)

    print(f"{len(parts)} are selected.")

    if len(parts) == 0:
        return

    if new_state is None:
        new_state = not parts[0].CreateSpcObjects

    for p in parts:
        p.CreateSpcObjects = new_state
        p.Update()
        print(f"{p.Marking} {p.Name} is now with CreateSpcObjects={new_state}.".lstrip())



if __name__ == "__main__":
    switch_spc_inclusion()
