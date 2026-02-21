"""
Модуль предоставляет набор функций и класс для работы (чтения, проверки,
исправления, изменения, сохранения) с сохраняемыми конфигурационными настройками
приложений.

Файл конфигурации приложения по умолчанию располагается по пути:
* для windows: `C:\\Users\\<user>\\%AppData%\\Roaming\\<program_name>\\cfg.json`;
* для Linux: `/home/<user>/.config/<program_name>/cfg.json`.

"""

import typing
import os
import json

from .file_utils import get_user_config_folder, ensure_file
from .json_utils import JSONable, json_copy

# from builtins import _ClassInfo
_ClassInfo: typing.TypeAlias = type | tuple[type, ...]  # isinstance()'s second parameter type


IS_VERBOSE: bool = True
"""Global variable, sets the verbose mode. By default is `True`."""


def get_default_config_filepath(program_name: str) -> str:
    """
    Формирует и возвращает абсолютный путь к файлу с настройками приложения:
    * для windows: `C:\\Users\\<user>\\%AppData%\\Roaming\\<program_name>\\cfg.json`;
    * для Linux: `/home/<user>/.config/<program_name>/cfg.json`.

    Не гарантирует существование родительских папок и файла на диске.

    См. также `file_utils.ensure_file()`.
    """
    return os.path.join(get_user_config_folder(program_name), "cfg.json")


def isinstance_for_list_values(l: list|tuple, list_values_types: list[_ClassInfo]) -> bool:
    if not isinstance(l, (list, tuple)):
        return False
    if len(l) != len(list_values_types):
        return False
    for i in range(len(list_values_types)):
        if not isinstance(l[i], list_values_types[i]):
            return False
    return True


def ensure_dict_value(
        d: dict,
        key: str,
        value_type: _ClassInfo,
        default_value: object,
        ) -> bool:
    """
    Проверяет значение по ключу `key` в словаре `d`. Если такого ключа нет или
    тип значения отличный от `value_type`,
    записывает значение по умолчанию `default_value`.

    Возвращает `True`, если значение есть и удовлетворяет требованиям;
    `False` - в противном случае, т.е. когда создано значение по умолчанию.

    Вариант использования - в функциях `check_config()`.
    """
    assert isinstance(default_value, value_type)
    if not key in d or not isinstance(d[key], value_type):
        d[key] = default_value
        return False
    return True


def ensure_dict_value_list(
        d: dict,
        key: str,
        list_element_type: _ClassInfo,
        list_element_check_function: typing.Callable[[typing.Any], bool]|None = None,
        ) -> bool:
    """
    Проверяет значение по ключу `key` в словаре `d`.

    Если такого ключа нет или тип значения - не список (`list`),
    записывает значение по умолчанию `[]` (пустой список).

    Для каждого элемента списка:
    * проверяет его тип на соответствие `list_element_type`,
    * проверяет возвращаемое значение `list_element_check_function(element)`
    (если эта функция указана, т.е. `is not None`) на соответствие `True`,

    и если хоть одно из двух условий не соответствует, удаляет этот элемент списка.

    Возвращает `False`, когда был создан пустой список или когда были
    удалены один или более элементов списка; в противном случае, т.е. когда все
    требования соответствуют, возвращает `True`.

    Вариант использования - в функциях `check_config()`.

    Пример:
    ```
    def check_toolbar_cfg(toolbar_el: dict) -> bool:
        if not ensure_dict_value(toolbar_el, "name", str, ""): return False  # required important property
        ensure_dict_value(toolbar_el, "is_hidden", bool, False)  # non-important property; do not remove if the property is wrong
        ensure_dict_value_list(
            toolbar_el, "contents", list,
            lambda c: isinstance_for_list_values(c, [str, str]))
        return True

    ensure_dict_value_list(cr.cfg(), "toolbars", dict, check_toolbar_cfg)
    ```
    """
    if not ensure_dict_value(d, key, list, list()):
        return False

    rv = True
    is_ok = True
    i = 0
    while i < len(d[key]):
        el = d[key][i]
        if list_element_check_function is not None:
            rv = list_element_check_function(el)
            assert isinstance(rv, bool), "list_element_check_function() has not returned bool"
        if not isinstance(el, list_element_type) or not rv:
            is_ok = False
            list.pop(d[key], i)
        else:
            i += 1
    return is_ok


def ensure_dict_structure_values_list(
        d: dict,
        key: str,
        list_values_types: list[_ClassInfo],
        default_values_list: list,
        ) -> bool:
    """
    Проверяет список (`list`) значений по ключу `key` в словаре `d`.
    Записывает значение по умолчанию `default_value`, если
    * такого ключа `key` в словаре нет
    * или тип значения `d[key]` - не список
    * или количество значений списка (`d[key]`) отличается от количества в `list_values_types`
    * или тип значений списка (`d[key]`) отличается от типов в `list_values_types`.

    Возвращает `True`, если значение есть и удовлетворяет требованиям;
    `False` - в противном случае, т.е. когда создано значение по умолчанию.

    Вариант использования - в функциях `check_config()`.
    """
    assert isinstance_for_list_values(default_values_list, list_values_types)
    if not key in d or not isinstance_for_list_values(d[key], list_values_types):
        d[key] = json_copy(default_values_list)
        return False
    return True


def ensure_dict_items_types(
        d: dict,
        key_type: _ClassInfo,
        value_type: _ClassInfo,
        ) -> bool:
    """
    Проверяет словарь `d` на соответствие типов его ключей и значений.
    Все ключи словаря должны соответствовать типу `key_type`,
    все значения - `value_type`.

    Если хотя бы один ключ или одно значение не соответствует типу, то удаляется
    эта пара ключ-значение.

    Возвращает `True`, если все ключи и значения заданных типов;
    и `False` в противном случае, т.е. когда была удалена хоть одна пара ключ-значение.

    Вариант использования - в функциях `check_config()`.
    """
    assert isinstance(d, dict)
    is_ok: bool = True
    for key, value in d.items():
        if not isinstance(key, key_type) or not isinstance(value, value_type):
            is_ok = False
            del d[key]
    return is_ok


class ConfigReader():
    def __init__(
            self,
            filepath: str = "",
            ) -> None:
        self._is_initialized: bool = False

        self._filepath: str = filepath
        self._cfg: dict = {}

    def init_config(self) -> None:
        """
        Загружает конфигурацию с диска или создает на диске конфигурацию
        по умолчанию и вызывает проверку `check_config()`.

        Перед вызовом должен быть установлен путь к файлу (см. `set_filepath()`).

        Как правило, вызывается в головном модуле программы.
        """
        if self._filepath == "":
            raise Exception("Config filepath is not set")
        ensure_file(self._filepath)
        self.load()
        self.set_initialized(True)
        self.check_config()

    def check_config(self) -> None:
        """
        Проверяет опции конфигурации и создает/исправляет их на значения по умолчанию.

        При переопределении в дочернем классе
        **обязателен** вызов `super().check_config()`.

        См. также `ensure_dict_value()`, `ensure_dict_values_list()`.
        """
        if not isinstance(self.cfg(), dict):
            self._cfg = {}

    def set_initialized(self, state: bool) -> None:
        self._is_initialized = state

    def is_initialized(self) -> bool:
        return self._is_initialized

    def require_initialized(self) -> None:
        if not self._is_initialized:
            raise Exception("Config must be initialized at this point")

    def set_filepath(self, filepath: str) -> None:
        self._filepath = os.path.abspath(filepath)

    def get_filepath(self) -> str:
        return self._filepath

    def cfg(self) -> dict:
        """
        Возвращает словарь со свойствами конфигурации.

        Если конфигурация не инициализирована (см. `set_initialized()`),
        выбрасывает ошибку.
        """
        self.require_initialized()
        return self._cfg

    def load(self) -> None:
        """
        Загружает конфигурацию из файла.

        Путь к файлу задается через `set_filepath()`.

        См. также `check_config()`.
        """
        if self._filepath == "":
            raise Exception("Config filepath is not set")

        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception as e:
            Exception(f"Error while loading the config ('{self._filepath}'): {e.__class__.__name__}: {e}")

        if not isinstance(d, dict):
            raise Exception("Config object is not a dict")

        self._cfg.clear()
        self._cfg.update(d)

        if IS_VERBOSE:
            print(f"Config is loaded from file '{self._filepath}'.")

    def save(self) -> None:
        """
        Сохраняет конфигурацию в файл.

        Путь к файлу задается через `set_filepath()`.
        """
        if self._filepath == "":
            raise Exception('Config filename is not set')

        ensure_file(self._filepath)
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(
                self._cfg,
                f,
                ensure_ascii=False,
                indent=2
            )
        if IS_VERBOSE:
            print(f"Config is saved to file '{self._filepath}'.")

    def reset_config(self) -> None:
        """
        Сбрасывает текущую конфигурацию на конфигурацию по умолчанию:
        * очищает словарь свойств конфигурации (см. `cfg()`),
        * вызывает `check_config()` для записи значений по умолчанию,
        * сохраняет в файл (см. `save()`).

        Путь к файлу задается через `set_filepath()`.

        *Примечание*. В прикладных приложениях может быть удобнее сразу завершить
        программу через `sys.exit()`;
        если же завершение программы не предусмотрено,
        тогда следует вызывать `check_config()` отдельно
        для вложенных словарей конфигурации.
        """

        if IS_VERBOSE:
            print("Resetting the config.", end=" ")

        self._cfg.clear()
        self.check_config()
        self.save()

        # self.load()  # нужно ли?



if __name__ == "__main__":
    """
    Пример использования в модуле `config.py`:
    """

    PROGRAM_NAME = "PythonConfigReader"

    class MyConfigReader(ConfigReader):
        def check_config(self) -> None:
            super().check_config()
            ensure_dict_value(self.cfg(), "a", float, 1.0)
            ensure_dict_value(self.cfg(), "b", str, "default string")
            ensure_dict_structure_values_list(self.cfg(), "c", [int, str], [45, "forty-five"])

            def check_toolbar_cfg(toolbar_el: dict) -> bool:
                if not ensure_dict_value(toolbar_el, "name", str, ""): return False
                ensure_dict_value(toolbar_el, "is_hidden", bool, False)  # do not remove if property is wrong
                ensure_dict_value_list(
                    toolbar_el, "contents", list,
                    lambda c: isinstance_for_list_values(c, [str, str]))
                return True
            ensure_dict_value_list(cr.cfg(), "toolbars", dict, check_toolbar_cfg)

        def cfg_structure(self, structure_name: str) -> dict:
            ensure_dict_value(self.cfg()["structures"], structure_name, dict, dict())
            return self.cfg()["structures"][structure_name]


    cr = MyConfigReader()

    def app_module_cfg():
        return cr.cfg_structure("custom_app_module")

    def check_app_module_cfg():
        ensure_dict_value(app_module_cfg(), "property1", float, 42.0)


    try:
        print(app_module_cfg()["property1"])
    except Exception as e:
        print(f"Error: {e}")

    cr.set_filepath(get_default_config_filepath(PROGRAM_NAME))
    cr.init_config()

    check_app_module_cfg()

    print(f"config is {cr.cfg()}")


    app_module_cfg()["property1"] = 35

    cr.save()

    # cr.reset_config()

    # print(f"config is {cr.cfg()}")

    # print(app_module_cfg()["property1"])

