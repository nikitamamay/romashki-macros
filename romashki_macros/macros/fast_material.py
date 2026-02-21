"""
Макрос для задания материала и плотности в 3D-модели в обход штатного справочника
"Материалы и сортаменты" Компас.

При применении материала в 3D-модели не происходит перекрашивания модели
в темно-серый цвет, как это зачем-то выполняется при работе с штатным справочником
материалов в Компас.

Maкрос поддерживает запись сортамента с привычным форматированием с дробной чертой,
например, для обозначений листов, труб, профилей и т.д.

"""
from .lib_macros.core import *

import re


DENSITY_STEEL: float = 7850.0  # kg/m3
""" Плотность стали. """


re_fraction = re.compile(r'([\s\S]*?)\$d([\s\S]*?);([\s\S]*?)\$', re.I | re.M)
""" Регулярное выражение для парсинга управляющих символов форматирования дроби: `$d ; $`. """



def set_material_in_current_part(material: str, density: float) -> None:
    """
    Назначить материал для текущей 3D-модели.

    Плотность `density` здесь выражается в кг/м3.

    См. также `compile_material_str()`.
    """
    doc, part = open_part()
    selected_bodies = get_selected(doc, (KAPI7.IBody7))

    # если выбраны тела, то применяется материал для этих тел
    if False and len(selected_bodies) != 0:
        # TODO для тел Компас не устанавливает материал? Свойства тела как бы меняются, но при закрытии и открытии панели свойств у тела снова возвращается материал детали. Но как тогда устанавливаются материалы для профилей в приложении Металлоконструкций?
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
    """
    Возвращает материал (строку) и плотность (в кг/м3) текущей 3D-модели.
    """
    doc, part = open_part()
    s_raw: str = part.Material
    density: float = part.Density * 1000
    return (s_raw, density)


def compile_material_str(base: str, on_top: str = "", under: str = "") -> str:
    """
    Возвращает наименование материала со специальными управляющими символами
    форматирования дроби (`$d ; $`).

    Функция актуальна для записи материалов сортаментов в те свойства модели
    (графа "Материал"; графа "Наименование" для бесчертежных деталей из проката),
    которые затем при передаче в основную надпись чертежа или в спецификацию
    приведут к отображению материала в виде дроби.

    Например, для того, чтобы в Компас при вставке текста запись материала была
    отформатирована в виде дроби
    ```
    |      on_top   |                  8 ГОСТ 19903
    | base ------   | например, Лист ----------------
    |      under    |                09Г2С ГОСТ 19281
    ```
    следует использовать строку с управляющими символами: `base$don_top;under$`.
    """
    if on_top == "" and under == "":
        return base
    return f"{base}$d{on_top};{under}$"


def parse_material_str(s: str) -> tuple[str, str, str]:
    """
    Проверяет, есть ли управляющие символы форматирования дроби в строке `s`,
    и возвращает три значения: содержимое слева от дроби, над дробью и снизу.

    В случае отсутствия символов форматирования дроби возвращается `(s, "", "")`

    Так, например, строка `base$don_top;under$` вернёт `("base", "on_top", "under")`.
    """
    m = re_fraction.match(s)
    if not m is None:
        return (m.group(1), m.group(2), m.group(3))
    return (s, "", "")


def get_single_line_material_str(base: str, on_top: str = "", under: str = "") -> str:
    """
    Возвращает наименование материала, записанное через косую черту:
    `base on_top / under`.

    Актуально для записи материала вне Компас-3D или где символы форматирования
    дроби не работают или не уместны.

    См. также `compile_material_str()`.
    """
    if on_top == "" and under == "":
        return base
    return f"{base} {on_top} / {under}"


if __name__ == "__main__":
    print(f"current_material={get_material_in_current_part()}")

    set_material_in_current_part("Адамантий", 666)
