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

from .lib_macros.core import *

import typing


PaintData: typing.TypeAlias = tuple[int, float, float, float, float, float, float]
"""
1. `int` - цвет в формате `0xRRGGBB` (**отличается от API Компас**);
2. `float` - Ambient (Общий цвет);
3. `float` - Diffuse (Диффузия);
4. `float` - Specularity (Зеркальность);
5. `float` - Shininess (Блеск);
6. `float` - Transparency (Прозрачность) (**отличается от API Компас**: 0 - непрозрачный, 1 - полностью прозрачный);
7. `float` - Emission (Излучение).

Следует использовать следующим образом:
```
KAPI7.IColorParam7.SetAdvancedColor(color_traditional_to_kompas(color), Am, Di, Sp, Sh, 1 - Tr, Em)
```
"""

DEFAULT_PAINT: PaintData = (0x909090, 0.5, 0.6, 0.8, 0.8, 0.0, 0.5)
""" Краска по умолчанию для деталей в Компас v16 """


class UseColorEnum:
    useColorUnknown = -1
    """ цвет не определен """

    useColorOur = 0
    """ собственный цвет ("наш" цвет XD) """

    useColorOwner = 1
    """ цвет хозяина (исходного объекта) """

    useColorSource = 2
    """ цвет источника """

    useColorLayer = 3
    """ цвет слоя """



def paint_parts(
        paint: PaintData | None,
        useColor = UseColorEnum.useColorOur,
        is_recursive = False,
        ) -> None:
    def apply_color(part: KAPI7.IPart7):
        if part.IsLayoutGeometry or KAPI7.IFeature7(part).Excluded:
            print(f"Пропускается от перекрашивания: {part.Marking} {part.Name} {part.FileName}")
            return False
        print(f"Перекрашивается: {part.Marking} {part.Name} {part.FileName}")
        cp = KAPI7.IColorParam7(part)
        cp.UseColor = useColor
        if useColor == UseColorEnum.useColorOur:
            assert paint is not None
            color, Am, Di, Sp, Sh, Tr, Em = paint
            color_kompas = color_traditional_to_kompas(color)
            cp.SetAdvancedColor(color_kompas, Am, Di, Sp, Sh, 1 - Tr, Em)
        part.Update()
        return True

    doc, toppart = open_part()
    parts: list[KAPI7.IPart7] = get_selected(doc, KAPI7.IPart7)

    if len(parts) == 0:
        if is_recursive:
            raise Exception("Недопускается рекурсивное перекрашивание текущей модели и всех её дочерних компонентов."
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


def get_current_color() -> PaintData:
    doc, part = open_part()
    cp = KAPI7.IColorParam7(part)
    _, color_kompas, Am, Di, Sp, Sh, Tr, Em = cp.GetAdvancedColor()
    Tr = 1 - Tr
    color = color_kompas_to_traditional(color_kompas)
    paint = [color, Am, Di, Sp, Sh, Tr, Em]
    print("Текущие параметры:", paint)
    return paint


if __name__ == "__main__":
    paint_parts(DEFAULT_PAINT, UseColorEnum.useColorOur, False)
