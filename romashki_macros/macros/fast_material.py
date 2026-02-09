"""
Макрос для задания материала и плотности в 3D-модели в обход штатного справочника
"Материалы и сортаменты" Компас.

В графическом интерфейсе макроса можно задать свой собственный список наиболее
часто используемых материалов и назначать их за два клика мыши.

При применении материала в 3D-модели не происходит перекрашивания модели
в темно-серый цвет, как это зачем-то выполняется при работе с штатным справочником
материалов в Компас.

Maкрос поддерживает запись сортамента с привычным форматированием с дробной чертой,
например, для обозначений листов, труб, профилей и т.д.

"""
from .lib_macros.core import *

import re


DENSITY_STEEL = 7850  # kg/m3


re_fraction = re.compile(r'([\s\S]*?)\$d([\s\S]*?);([\s\S]*?)\$', re.I | re.M)



def set_material_in_current_part(material: str, density: float) -> None:
    """
    Назначить материал для текущей детали или для тел, если они выбраны.

    Плотность `density` здесь выражается в кг/м3.
    """
    doc, part = open_part()
    selected_bodies = get_selected(doc, (KAPI7.IBody7))

    # если выбраны тела, то применяется материал для этих тел
    if len(selected_bodies) != 0:
        print(f"Применяется материал для {len(selected_bodies)} выбранных тел")
        for body in selected_bodies:
            mip = KAPI7.IMassInertiaParam7(body)
            mip.DensityMode = True  # ручное задание плотности, а не из Справочника (?)
            mip.SetMaterial(material, density / 1000)
            mip.Calculate()
            body.Update()
        part.Update()

    # если тела не выбраны, то - для всей модели целиком
    else:
        print("Применяется материал для текущей модели")
        part.SetMaterial(material, density / 1000)
        part.Update()


def get_material_in_current_part() -> tuple[str, float]:
    doc, part = open_part()
    s_raw: str = part.Material
    density: float = part.Density * 1000
    return (s_raw, density)


def compile_material_str(base: str, on_top: str = "", under: str = "") -> str:
    if on_top == "" and under == "":
        return base
    return f"{base}$d{on_top};{under}$"

def parse_material_str(s: str) -> tuple[str, str, str]:
    m = re_fraction.match(s)
    if not m is None:
        return (m.group(1), m.group(2), m.group(3))
    return (s, "", "")

def get_single_line_material_str(base: str, on_top: str = "", under: str = "") -> str:
    if on_top == "" and under == "":
        return base
    return f"{base} {on_top} / {under}"


if __name__ == "__main__":
    print(get_material_in_current_part())
