"""
Головной модуль, который импортирует все остальные модули макросов
и предоставляет список-синглтон (`list`) с объектами GUI-интерфейсов макросов.

"""

from src.macros import change_bg
from src.macros import dwg_hidden_layers
from src.macros import fast_export
from src.macros import fast_mate
from src.macros import fix_lcs
from src.macros import stamp
from src.macros import fast_parts
from src.macros import fast_dxf
from src.macros import fast_material
from src.macros import sheet_layout
from src.macros import surface_and_demand
from src.macros import do_not_disturb
from src.macros import exclude_from_spc
from src.macros import parts_painting
from src.macros import bulk_rename
from src.macros import fast_mirror
from src.macros import fast_rollback
from src.macros import fast_rvd
from src.macros import welding


from src.gui_macros import Macros


macroses: list[Macros] = [
    do_not_disturb.MacrosDoNotDisturb(),
    change_bg.MacrosChangeBackgroundColor(),
    dwg_hidden_layers.MacrosDWGHiddenLayers(),
    fast_export.MacrosFastExport(),
    stamp.MacrosStamp(),
    fix_lcs.MacrosFixLCS(),
    fast_mate.MacrosFastMate(),
    fast_parts.MacrosFastParts(),
    fast_dxf.MacrosFastDXF(),
    fast_material.MacrosFastMaterial(),
    sheet_layout.MacrosSheetLayout(),
    surface_and_demand.MacrosSurfaceRoughnessAndTechDemand(),
    exclude_from_spc.MacrosExcludeFromSPC(),
    parts_painting.MacrosPartsPainting(),
    bulk_rename.BulkRenameMacros(),
    fast_mirror.FastMirrorMacros(),
    fast_rollback.FastRollbackMacros(),
    fast_rvd.FastRVDMacros(),
    welding.WeldingMacros(),
]


def get_macros(codename: str) -> Macros:
    for m in macroses:
        if m.code_name == codename:
            return m
    raise Exception(f"No macros with name \"{codename}\"")
