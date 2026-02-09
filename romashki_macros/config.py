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


APP_CONFIG_FOLDER = config_reader.get_user_config_folder(PROGRAM_NAME)
PROGRAM_TEMP_FOLDER = os.path.join(os.environ.get("TEMP", "./Temp"), PROGRAM_NAME)


_is_config_initialized: bool = False
cr: config_reader.ConfigReader = config_reader.ConfigReader()
dh: delayed_handler.DelayedHandler = delayed_handler.DelayedHandler()
after_config_reset_handlers: list = []
task_save_config: int = 0


def check_if_config_initialized() -> None:
    if not _is_config_initialized:
        raise Exception("Config is not initialized")


def init_config() -> bool:
    global _is_config_initialized
    global cr
    global dh
    global after_config_reset_handlers
    global task_save_config

    file_utils.ensure_folder(PROGRAM_TEMP_FOLDER)

    config_reader.IS_VERBOSE = True

    # FIXME если где-то (например, у макросов) захватывается ссылка на cr._cfg у неинициализированного cr? Переделать ConfigReader на настоящий синглтон!
    cr = config_reader.ConfigReader.load_or_create_default_config_in_configfolder(
        APP_CONFIG_FOLDER,
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

    task_save_config = dh.create_task(
        save,
        1,
    )

    ### CONFIG CHECK

    # cfg = cr.cfg()  # TODO заменить в проверках ниже доступ к полю напрямую `cr._cfg` на эту локальную переменную `cfg = cr.cfg()`

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
        assert "toolbars" in cr._cfg["interface"]
        assert isinstance(cr._cfg["interface"]["toolbars"], list)
        for el in cr._cfg["interface"]["toolbars"]:
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
        cr._cfg["interface"]["toolbars"] = []

    try:
        assert "icon_size" in cr._cfg["interface"]
        assert isinstance(cr._cfg["interface"]["icon_size"], int)
    except:
        cr._cfg["interface"]["icon_size"] = 32

    try:
        assert "stays_on_top" in cr._cfg["interface"]
        assert isinstance(cr._cfg["interface"]["stays_on_top"], bool)
    except:
        cr._cfg["interface"]["stays_on_top"] = True

    try:
        assert "general" in cr._cfg
        assert isinstance(cr._cfg["general"], dict)
    except:
        cr._cfg["general"] = {}

    try:
        assert isinstance(cr._cfg["general"]["after_config_reset"], bool)
    except:
        cr._cfg["general"]["after_config_reset"] = False

    ### SETTING INITIALIZED FLAG

    _is_config_initialized = True
    return True


def set_after_config_reset_handler(f) -> None:
    after_config_reset_handlers.append(f)


def execute_after_config_reset() -> None:
    check_if_config_initialized()
    if cr._cfg["general"]["after_config_reset"]:
        print("Executing after-reset procedures...")
        for f in after_config_reset_handlers:
            f()
        cr._cfg["general"]["after_config_reset"] = False
        print("Done setting after-reset state")


### BINDINGS FOR EASIER USAGE

def interface() -> dict:
    check_if_config_initialized()
    return cr._cfg["interface"]

def macros(codename: str) -> dict:
    check_if_config_initialized()
    if not codename in cr._cfg["macroses_config"]:
        cr._cfg["macroses_config"][codename] = {}
    return cr._cfg["macroses_config"][codename]

def general() -> dict:
    check_if_config_initialized()
    return cr._cfg["general"]


def toolbars() -> list[dict]:
    return interface()["toolbars"]

def get_icon_size() -> int:
    return interface()["icon_size"]

def set_icon_size(size: int) -> None:
    assert isinstance(size, int)
    interface()["icon_size"] = size


def save():
    check_if_config_initialized()
    cr.save()

def save_delayed():
    dh.do_task(task_save_config)

