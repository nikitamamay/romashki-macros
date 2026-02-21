"""
Модуль предоставляет класс и объект-singleton для реализации функционала
для работы с сохраняемыми конфигурационными настройками данного приложения
и его модулей (макросов в частности).

"""

import os

from . import PROGRAM_NAME
from .utils import file_utils
from .utils import config_reader
from .utils import delayed_handler


CONFIG_FILEPATH = config_reader.get_default_config_filepath(PROGRAM_NAME)

PROGRAM_TEMP_FOLDER = os.path.join(os.environ.get("TEMP", "./Temp"), PROGRAM_NAME)



class RomashkiMacrosConfigReader(config_reader.ConfigReader):
    def __init__(self, filepath: str = "") -> None:
        super().__init__(filepath)
        self._after_config_reset_handlers: list = []

    def set_after_config_reset_handler(self, f) -> None:
        self._after_config_reset_handlers.append(f)

    def execute_after_config_reset(self) -> None:
        if cr.cfg_general()["after_config_reset"]:
            print("Executing after-reset procedures...")
            for f in self._after_config_reset_handlers:
                f()
            cr.cfg_general()["after_config_reset"] = False
            print("Done setting after-reset state")

    def check_config(self) -> None:
        super().check_config()
        config_reader.ensure_dict_value(self.cfg(), "macroses_config", dict, dict())
        config_reader.ensure_dict_value(self.cfg(), "interface", dict, dict())
        config_reader.ensure_dict_value(self.cfg(), "general", dict, dict())

        # toolbars
        def check_toolbar(t: dict) -> bool:
            if not config_reader.ensure_dict_value(t, "name", str, ""): return False
            config_reader.ensure_dict_value(t, "has_break_before", bool, False)
            config_reader.ensure_dict_value(t, "is_hidden", bool, False)
            config_reader.ensure_dict_value_list(
                t, "contents", list,
                lambda c: config_reader.isinstance_for_list_values(c, [str, str]))
            return True
        config_reader.ensure_dict_value_list(self.cfg_interface(), "toolbars", dict, check_toolbar)

        # interface
        config_reader.ensure_dict_value(self.cfg_interface(), "icon_size", int, 24)
        config_reader.ensure_dict_value(self.cfg_interface(), "stays_on_top", bool, True)

        # general
        config_reader.ensure_dict_value(self.cfg_general(), "after_config_reset", bool, True)

    def macros(self, codename: str) -> dict:
        config_reader.ensure_dict_value(self.cfg_macroses(), codename, dict, dict())
        return self.cfg_macroses()[codename]

    def cfg_interface(self) -> dict:
        return self.cfg()["interface"]

    def cfg_interface_toolbars(self) -> list:
        return self.cfg_interface()["toolbars"]

    def cfg_general(self) -> dict:
        return self.cfg()["general"]

    def cfg_macroses(self) -> dict:
        return self.cfg()["macroses_config"]


dh = delayed_handler.DelayedHandler()
task_save_config: int = 0

cr = RomashkiMacrosConfigReader(CONFIG_FILEPATH)


def save():
    cr.require_initialized()
    cr.save()

def save_delayed():
    dh.do_task(task_save_config)

task_save_config = dh.create_task(save, 1.0)


if __name__ == "__main__":
    cr.init_config()
    print(cr.cfg())
    save()
