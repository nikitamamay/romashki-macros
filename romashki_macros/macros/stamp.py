"""
Макрос для автоматизированного заполнения основной надписи по шаблону.

Поддерживается возможность вставить текущую дату.

Один из самых первых разработанных автором макросов, один из наиболее часто применяемых.

"""

from .lib_macros.core import *

import datetime


class StampCellNumbers:
    Naimenovanie = 1
    Oboznachenie = 2
    Material = 3
    Litera0 = 40
    Litera1 = 41
    Litera2 = 42
    Massa = 5
    Masschtab = 6
    Predpriyatie = 9

    NachOtd_dolzhnost = 10

    Razrabotal = 110
    Proveril = 111
    TehControl = 112
    NachOtd = 113
    NormContr = 114
    Utverdil = 115

    Razrabotal_podp = 110 + 10
    Proveril_podp = 111 + 10
    TehControl_podp = 112 + 10
    NachOtd_podp = 113 + 10
    NormContr_podp = 114 + 10
    Utverdil_podp = 115 + 10

    Razrabotal_data = 110 + 20
    Proveril_data = 111 + 20
    TehControl_data = 112 + 20
    NachOtd_data = 113 + 20
    NormContr_data = 114 + 20
    Utverdil_data = 115 + 20

    SpravNomer = 24
    PervPrimen = 25



def format_date(date: datetime.date|None = None, fmt: str = "%d.%m.%y") -> str:
    """
    Форматирует дату по заданному шаблону функцией `strftime()`.
    Если объект `date` равен `None`, то используется текущая дата.

    Наиболее частые варианты:
    * для `31.12.90` используйте `%d.%m.%y`;
    * для `31.12.1990` используйте `%d.%m.%Y`.
    """
    if date is None:
        date = datetime.datetime.now()

    return date.strftime(fmt)


def stamp_numbers(max_number: int = 10000, min_number: int = 0) -> None:
    """
    Заполняет все ячейки основных надписей всех листов в текущем графическом
    документе номерами этих ячеек.

    Позволяет выяснить, какой номер у определенной ячейки.
    """
    doc = open_doc2d()

    lss: KAPI7.ILayoutSheets = doc.LayoutSheets

    for i in range(lss.Count):
        ls: KAPI7.ILayoutSheet = lss.Item(i)

        stamp: KAPI7.IStamp = ls.Stamp

        for col_id in range(min_number, max_number):
            txt: KAPI7.IText = stamp.Text(col_id)
            txt.Str = f"{col_id}"

        stamp.Update()


def stamp(data: dict[int, str], sheet_number: int = 1) -> None:
    """
    Заполняет основную надпись на листе `sheet_number` по словарю `data`.

    Cловарь `data` должен содержать пары `<номер_ячейки>: <текст>`.
    Номера ячеек можно использовать те, что заданы в `StampCellNumbers`,
    или можно узнать с помощью `stamp_numbers()`.

    Номера листов `sheet_number` начинаются с 1 (единицы).
    """
    assert isinstance(data, dict)

    app: KAPI7.IApplication = get_app7()
    doc: KAPI7.IKompasDocument = app.ActiveDocument

    lss: KAPI7.ILayoutSheets = doc.LayoutSheets

    ls: KAPI7.ILayoutSheet = lss.ItemByNumber(sheet_number)

    stamp: KAPI7.IStamp = ls.Stamp

    for col_id, value in data.items():
        col_id = int(col_id)
        txt: KAPI7.IText = stamp.Text(col_id)
        txt.Str = str(value)

    stamp.Update()


def get_stamp_data(cell_number: int, doc: KAPI7.IKompasDocument2D|None = None, sheet_number: int = 1) -> str:
    """
    Возвращает содержимое ячейки с номером `cell_number` в документе `doc` на листе с номером `sheet_number`.

    Если `doc` равен `None`, то используется текущий документ.

    Номера листов `sheet_number` начинаются с 1 (единицы).
    """
    if doc is None:
        doc = KAPI7.IKompasDocument2D(app.ActiveDocument)

    lss: KAPI7.ILayoutSheets = doc.LayoutSheets
    ls: KAPI7.ILayoutSheet = lss.ItemByNumber(sheet_number)
    stamp: KAPI7.IStamp = ls.Stamp

    txt: KAPI7.IText = stamp.Text(cell_number)
    return txt.Str



if __name__ == "__main__":
    stamp({
        StampCellNumbers.Razrabotal: "Иванов",
        StampCellNumbers.Predpriyatie: "Университет\nКафедра\nГруппа",
        StampCellNumbers.Razrabotal_data: format_date(fmt="%d.%m.%Y"),
    })

