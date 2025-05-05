"""
Модуль предоставляет класс и объект-singleton для реализации функционала
для работы с сохраняемыми конфигурационными настройками данного приложения
и его модулей (макросов в частности).

"""

from src import config_reader
from src import delayed_handler


PROGRAM_NAME = "RomashkiMacros"
APP_CONFIG_FOLDER = config_reader.get_user_config_folder(PROGRAM_NAME)



cr = config_reader.ConfigReader.load_or_create_default_config_in_configfolder(
    PROGRAM_NAME,
    {
        "macroses_config": {},
        "interface": {
            "show_all_toolbar_widgets": True,
            "toolbar_widgets": [],
            "icon_size": 16,
            "stays_on_top": True,
        }
    }
)
cr._verbose_saving = True

dh = delayed_handler.DelayedHandler()
task_save_config = dh.create_task(
    lambda: cr.save(),
    1,
)


def interface() -> dict:
    return cr._cfg["interface"]

def macros(codename: str) -> dict:
    if not codename in cr._cfg["macroses_config"]:
        cr._cfg["macroses_config"][codename] = {}
    return cr._cfg["macroses_config"][codename]


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
    assert "toolbar_widgets" in interface()
    assert isinstance(interface()["toolbar_widgets"], list)
    for el in interface()["toolbar_widgets"]:
        assert isinstance(el, list)
        assert len(el) == 2
        assert isinstance(el[0], str)
        assert isinstance(el[1], str)
except:
    interface()["toolbar_widgets"] = []

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
    assert "show_all_toolbar_widgets" in interface()
    assert isinstance(interface()["show_all_toolbar_widgets"], bool)
except:
    interface()["show_all_toolbar_widgets"] = True



### BINDINGS FOR EASIER USAGE

def toolbar_widgets() -> list[list[str, str]]:
    return interface()["toolbar_widgets"]

def set_toolbar_widgets(l: list[list[str, str]]) -> None:
    interface()["toolbar_widgets"].clear()
    interface()["toolbar_widgets"].extend(l)

def get_icon_size() -> int:
    return interface()["icon_size"]

def set_icon_size(size: int) -> None:
    assert isinstance(size, int)
    interface()["icon_size"] = size


save = cr.save
save_delayed = lambda: dh.do_task(task_save_config)

