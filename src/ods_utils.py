"""
Модуль предоставляет удобные функции для работы с файлами ODS.

"""

from collections import OrderedDict  # for ods3
import pyexcel_ods3

from time import time as get_timestamp
import os
import traceback

from src.macros import HEAD


HEAD.ensure_folder(HEAD.PROGRAM_TEMP_FOLDER)


def save_ods_data(filepath: str, data: OrderedDict) -> None:
    assert isinstance(data, OrderedDict)
    pyexcel_ods3.save_data(filepath, data)


def save_ods_sheet(filepath: str, sheet: list[list], sheet_name: str = "Sheet1") -> None:
    assert isinstance(sheet, (list, tuple))
    for el in sheet:
        assert isinstance(el, (list, tuple))
    data = OrderedDict()
    data.update({sheet_name: sheet})
    save_ods_data(filepath, data)


def read_ods_data(filepath: str) -> OrderedDict:
    return pyexcel_ods3.get_data(filepath)


def read_ods_sheet(filepath: str, sheet_name: str = "Sheet1") -> list[list]:
    data = pyexcel_ods3.get_data(filepath)
    if not sheet_name in data:
        raise Exception(f"No sheet {repr(sheet_name)} in ODS file {repr(filepath)}")
    sheet = list(data[sheet_name])
    return sheet


def create_temp_ods_filepath() -> str:
    filename = f"{int(get_timestamp())}.ods"
    return os.path.join(HEAD.PROGRAM_TEMP_FOLDER, filename)


def remove_file(filepath: str) -> bool:
    raise Exception("Not implemented")  # FIXME


def open_for_edit(ods_filepath: str) -> bool:
    try:
        print(f"Запуск на редактирование файла: '{ods_filepath}'")
        os.startfile(ods_filepath)
        return True
    except Exception as e:
        print(f"Не удалось запустить редактирование файла: '{ods_filepath}'")
        print(traceback.format_exc())
        return False

