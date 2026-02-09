
from ..gui.macros import MacrosSingleCommand
from ..utils.resources import get_resource_path

from ..macros.fix_lcs import *


class MacrosFixLCS(MacrosSingleCommand):
    def __init__(self) -> None:
        super().__init__(
            "fix_lcs",
            "Исправление ЛСК",
            get_resource_path("img/macros/lcs_fix.svg"),
            "Исправить опции создания ЛСК\n(сделать АСК текущей\nи не делать текущей ЛСК при её создании)"
        )

    def execute_macros(self) -> None:
        fix_LCS()
