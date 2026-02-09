"""
Макрос предназначен для [циклической] перемены цвета фона в рабочем окне модели
и чертежа по заранее заданному списку цветов.

Исторически возникла необходимость быстрого переключения между белым цветом фона
и градиентным темно-серым, соответствующим темной теме Компаса, чтобы выполнить
скриншот 3D-модели на белом фоне для вставки в пояснительную записку или презентацию.


Это самый первый созданный автором полноценный макрос: идея макроса датируется
августом-сентябрём 2022 года.

"""

from .lib_macros.core import *


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
