"""
Модуль предоставляет класс и объект-singleton для реализации функционала
для работы с сохраняемыми конфигурационными настройками данного приложения
и его модулей (макросов в частности).

"""

import os

from src import config_reader
from src import delayed_handler


PROGRAM_NAME = "RomashkiMacros"
APP_CONFIG_FOLDER = config_reader.get_user_config_folder(PROGRAM_NAME)
PROGRAM_TEMP_FOLDER = os.path.join(os.environ.get("TEMP", "./Temp"), PROGRAM_NAME)

config_reader.ensure_folder(PROGRAM_TEMP_FOLDER)

config_reader.IS_VERBOSE = True

cr = config_reader.ConfigReader.load_or_create_default_config_in_configfolder(
    PROGRAM_NAME,
    {
        "general": {
            "after_config_reset": True,
        },
        "interface": {
            "icon_size": 24,
            "stays_on_top": True,
            "toolbars": [],
        },
        "macroses_config": {},
    }
)

dh = delayed_handler.DelayedHandler()
task_save_config = dh.create_task(
    lambda: cr.save(),
    1,
)

after_config_reset_handlers: list = []


def interface() -> dict:
    return cr._cfg["interface"]

def macros(codename: str) -> dict:
    if not codename in cr._cfg["macroses_config"]:
        cr._cfg["macroses_config"][codename] = {}
    return cr._cfg["macroses_config"][codename]

def general() -> dict:
    return cr._cfg["general"]

def set_after_config_reset_handler(f) -> None:
    after_config_reset_handlers.append(f)

def execute_after_config_reset() -> None:
    if general()["after_config_reset"]:
        print("Executing after-reset procedures...")
        for f in after_config_reset_handlers:
            f()
        general()["after_config_reset"] = False
        print("Done setting after-reset state")


### CONFIG CHECK

try:
    assert "macroses_config" in cr._cfg
    assert isinstance(cr._cfg["macroses_config"], dict)
except:
    cr._cfg["macroses_config"] = {}

try:
    assert "interface" in cr._cfg
    assert isinstance(cr._cfg["interface"], dict)
except:
    cr._cfg["interface"] = {}

try:
    assert "toolbars" in interface()
    assert isinstance(interface()["toolbars"], list)
    for el in interface()["toolbars"]:
        assert isinstance(el, dict)
        assert isinstance(el["name"], str)
        assert isinstance(el["has_break_before"], bool)
        assert isinstance(el["is_hidden"], bool)
        assert isinstance(el["contents"], list)
        for a in el["contents"]:
            assert len(a) == 2
            assert isinstance(a[0], str)
            assert isinstance(a[1], str)
except:
    interface()["toolbars"] = []

try:
    assert "icon_size" in interface()
    assert isinstance(interface()["icon_size"], int)
except:
    interface()["icon_size"] = 32

try:
    assert "stays_on_top" in interface()
    assert isinstance(interface()["stays_on_top"], bool)
except:
    interface()["stays_on_top"] = True

try:
    assert "general" in cr._cfg
    assert isinstance(cr._cfg["general"], dict)
except:
    cr._cfg["general"] = {}

try:
    assert isinstance(general()["after_config_reset"], bool)
except:
    general()["after_config_reset"] = False


### BINDINGS FOR EASIER USAGE

def toolbars() -> list[dict]:
    return interface()["toolbars"]

def get_icon_size() -> int:
    return interface()["icon_size"]

def set_icon_size(size: int) -> None:
    assert isinstance(size, int)
    interface()["icon_size"] = size


save = cr.save
save_delayed = lambda: dh.do_task(task_save_config)

