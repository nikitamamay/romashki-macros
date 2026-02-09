"""
Макрос для работы с оформлением листа чертежа.

Макрос предоставляет функционал:

* выбор формата листа от A0 до A5 и смена ориентации листа (портретная/альбомная).

    Этот функционал актуален для старых версий Компаса со старым интерфейсом,
    в котором нет возможности сменить формат листа за один клик мыши, а нужно
    заходить в отдельный менеджер документа и менять там.

* применение оформления основной надписи из lyt-библиотеки.

    Этот функционал полезен, если основная надпись чертежа как-то изменена
    под требования на предприятии. Например, в правой нижней чейке не просто
    прописано название предприятия, а вставлено какое-то изображение.

"""
from .lib_macros.core import *


def set_sheets_layout_library(lib_filepath: str) -> None:
    """
    Изменяет стили оформления всех листов, на имеющиеся в библиотеке по пути `lib_filepath`.
    Номера стилей сохраняются теми же. Следовательно, номера стилей должны быть такими же,
    как и в стандартной библиотеке `graphic.lyt`.

    При `lib_filepath = ""` устанавливается стандартное обозначение из библиотеки `graphic.lyt`.
    """

    iKompasObject5, iKompasObject7 = get_kompas_objects()

    doc2d: KAPI7.IKompasDocument2D = open_doc2d()
    lss: KAPI7.ILayoutSheets = doc2d.LayoutSheets


    for i in range(lss.Count):
        ls: KAPI7.ILayoutSheet = lss.Item(i)
        ls.LayoutLibraryFileName = lib_filepath
        ls.Update()


def get_sheet_format(sheet_index: int = 0) -> tuple[int, bool]:
    """
    Возвращает формат и ориентацию листа
    с индексом (не номером) `sheet_index` у текущего документа.

    Формат может принимать значения `0...5` для A0...A5 соответственно
    и `6` для пользовательского (нестандартного) формата.
    """
    doc2d: KAPI7.IKompasDocument2D = open_doc2d()
    lss: KAPI7.ILayoutSheets = doc2d.LayoutSheets

    if sheet_index > lss.Count - 1:
        raise Exception("индекс листа задан большим, чем количество листов документе")
    if sheet_index < 0:
        raise Exception("задан отрицательный индекс")

    ls: KAPI7.ILayoutSheet = lss.Item(sheet_index)
    f: KAPI7.ISheetFormat = ls.Format

    return (f.Format, f.VerticalOrientation)


def set_sheet_format(format_number: int, is_vertical: bool, sheet_index: int = 0):
    """
    Изменяет у текущего документа формат и ориентацию листа
    с индексом (не номером) `sheet_index`.

    `format_number` может принимать значения `0...5` для A0...A5 соответственно.
    """
    doc2d: KAPI7.IKompasDocument2D = open_doc2d()
    lss: KAPI7.ILayoutSheets = doc2d.LayoutSheets

    if sheet_index > lss.Count - 1:
        raise Exception("индекс листа задан больше, чем листов документе")
    if sheet_index < 0:
        raise Exception("задан отрицательный индекс")

    ls: KAPI7.ILayoutSheet = lss.Item(sheet_index)
    f: KAPI7.ISheetFormat = ls.Format

    f.Format = format_number
    f.VerticalOrientation = is_vertical

    ls.Update()




if __name__ == "__main__":
    # set_sheets_layout_library("")

    set_sheet_format(1, False)
