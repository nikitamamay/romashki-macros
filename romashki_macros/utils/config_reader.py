"""
Модуль предоставляет набор функций и класс для работы (чтения, проверки,
исправления, изменения, сохранения) с сохраняемыми конфигурационными настройками
приложений.

Файл конфигурации приложения по умолчанию хранится
в папке `%%AppData%%/<ProgramName>` (для Windows)
или `~/.config/<ProgramName>` (для Linux).

"""

import os
import json

from .file_utils import get_user_config_folder, ensure_file
from .json_utils import JSONable, json_copy


IS_VERBOSE: bool = True
"""Global variable, sets the verbose mode. By default is `True`."""


class IConfig(JSONable):
    pass


class ConfigReader():
    def __init__(self, default_config: dict = {}) -> None:
        self._filepath: str = ""

        self._default_config: dict = default_config
        self._cfg: dict = json_copy(self._default_config)

    @staticmethod
    def load_or_create_default_config_in_configfolder(app_config_folder: str, default_config: dict = {}) -> 'ConfigReader':
        app_config_file = os.path.join(app_config_folder, "cfg.json")

        if os.path.exists(app_config_file):
            return ConfigReader.read_from_file(app_config_file, default_config)
        else:
            if IS_VERBOSE:
                print(f'Config file "{app_config_file}" not found. Using default config.')
            cr = ConfigReader(default_config)
            cr.set_filepath(app_config_file)
            cr.save()
            return cr

    @staticmethod
    def read_from_file(filepath: str, default_config: dict = {}) -> 'ConfigReader':
        if not os.path.isfile(filepath):
            raise Exception(f'"{filepath}" is not a file or does not exist')

        if IS_VERBOSE:
            print(f'Reading config from file: "{filepath}"')

        cr = ConfigReader(default_config)
        cr.set_filepath(filepath)
        cr.reload()
        return cr

    def copy(self) -> 'ConfigReader':
        cr = ConfigReader(json_copy(self._default_config))
        cr._cfg = json_copy(self._cfg)
        return cr

    def assign(self, cr: 'ConfigReader') -> None:
        self._cfg = json_copy(cr._cfg)
        self._default_config = json_copy(cr._default_config)

    def save(self, config: dict|None = None) -> None:
        if self._filepath == "":
            raise Exception('Config filename is not specified')

        ensure_file(self._filepath)
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(
                self._cfg if config is None else config,
                f,
                ensure_ascii=False,
                indent=2
            )
        if IS_VERBOSE:
            print("Config saved.")

    def save_default(self) -> None:
        self.save(self._default_config)

    def reload(self, do_reset: bool = False) -> None:
        if do_reset:
            if IS_VERBOSE:
                print("Resetting the config.", end=" ")
            self.save_default()

        if not os.path.isfile(self._filepath):
            if IS_VERBOSE:
                print(f"File '{self._filepath}' is not present. Writing the default config.", end=" ")
            self.save_default()

        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                self._cfg.update(json.load(f))

                if IS_VERBOSE:
                    print("Config is loaded.")

        except Exception as e:
            print(f'Error while loading the config: {e.__class__.__name__}: {e}')

    def set_filepath(self, filepath: str) -> None:
        self._filepath = os.path.abspath(filepath)

    def get_filepath(self) -> str:
        return self._filepath

    def set_default_config(self, default_config: dict) -> None:
        self._default_config = default_config

    def reset_config(self) -> None:
        self.reload(do_reset = True)


if __name__ == "__main__":
    from .file_utils import get_user_config_folder, ensure_file

    # testing
    PROGRAM_NAME = "PythonConfigReader"
    APP_CONFIG_FOLDER = get_user_config_folder(PROGRAM_NAME)
    APP_CONFIG_FILE = os.path.join(APP_CONFIG_FOLDER, "cfg.json")

    print(APP_CONFIG_FOLDER, APP_CONFIG_FILE, sep="\n")

    cr = ConfigReader.load_or_create_default_config_in_configfolder(APP_CONFIG_FOLDER, {
        "a": 1,
        "b": "hello",
        "c": [45, "forty-five"],
    })

    print(cr._cfg)

    cr.save()
