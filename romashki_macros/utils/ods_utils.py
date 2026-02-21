"""
Модуль предоставляет удобные функции для работы с файлами ODS (OpenDocument Spreadsheet).

"""

from collections import OrderedDict  # for ods3
import pyexcel_ods3

from time import time as get_timestamp
import os
import traceback


def save_ods_data(filepath: str, data: OrderedDict) -> None:
    """
    Сохраняет таблицу `data` в файл по пути `filepath`.
    """
    assert isinstance(data, OrderedDict)
    pyexcel_ods3.save_data(filepath, data)


def save_ods_sheet(filepath: str, sheet: list[list], sheet_name: str = "Sheet1") -> None:
    """
    Сохраняет таблицу с одним листом `sheet` (с именем `sheet_name`)
    в файл по пути `filepath`.
    """
    assert isinstance(sheet, (list, tuple))
    for el in sheet:
        assert isinstance(el, (list, tuple))
    data = OrderedDict()
    data.update({sheet_name: sheet})
    save_ods_data(filepath, data)


def read_ods_data(filepath: str) -> OrderedDict:
    """
    Возвращает таблицу, считанную из файла по пути `filepath`.
    """
    return pyexcel_ods3.get_data(filepath)


def read_ods_sheet(filepath: str, sheet_name: str = "Sheet1") -> list[list]:
    """
    Возвращает лист по имени `sheet_name` таблицы, считанной
    из файла по пути `filepath`.
    """
    data = pyexcel_ods3.get_data(filepath)
    if not sheet_name in data:
        raise Exception(f"No sheet {repr(sheet_name)} in ODS file {repr(filepath)}")
    sheet = list(data[sheet_name])
    return sheet


def create_temp_ods_filepath(temp_folder_path: str) -> str:
    """
    Возвращает путь к временному файлу формата ODS,
    размещенному в папке `temp_folder_path`.

    Имя файла состоит из `123456789.ods`, где
    `123456789` - это текущий timestamp (время в секундах с 1.01.1970).

    Не создает файл на диске.
    """
    filename = f"{int(get_timestamp())}.ods"
    return os.path.join(temp_folder_path, filename)


def remove_file(filepath: str) -> bool:
    """
    Not implemented
    """
    raise Exception("Not implemented")  # FIXME


def open_for_edit(ods_filepath: str) -> bool:
    """
    Открывает файл `ods_filepath` на редактирование программой, которая
    ассоциирована с расширением файла. Возвращает `True`, если удалось открыть,
    и `False` в противном случае.

    (Для `*.ods` это может быть LibreOffice Calc или Excel.)

    См. также `os.startfile()`.
    """
    try:
        print(f"Запуск на редактирование файла: '{ods_filepath}'")
        os.startfile(ods_filepath)
        return True
    except Exception as e:
        print(f"Не удалось запустить редактирование файла: '{ods_filepath}'")
        print(traceback.format_exc())
        return False

