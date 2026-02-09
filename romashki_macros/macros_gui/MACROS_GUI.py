"""
Головной модуль, который импортирует модули макросов с GUI-интерфейсами
и предоставляет список-синглтон (`list`) с объектами этих GUI-интерфейсов.

"""

from . import change_bg
from . import do_not_disturb
from . import dwg_hidden_layers
from . import exclude_from_spc
from . import fast_dxf
from . import fast_export
from . import fast_material
from . import fast_mirror
from . import fast_parts
from . import fast_rvd
from . import fix_lcs
from . import parts_painting
from . import sheet_layout
from . import stamp
from . import surface_and_demand
from . import welding

from ..gui.macros import Macros


macroses: list[Macros] = [
    do_not_disturb.MacrosDoNotDisturb(),
    change_bg.MacrosChangeBackgroundColor(),
    dwg_hidden_layers.MacrosDWGHiddenLayers(),
    fast_export.MacrosFastExport(),
    stamp.MacrosStamp(),
    fix_lcs.MacrosFixLCS(),
    # fast_mate.MacrosFastMate(),
    fast_parts.MacrosFastParts(),
    fast_dxf.MacrosFastDXF(),
    fast_material.MacrosFastMaterial(),
    sheet_layout.MacrosSheetLayout(),
    surface_and_demand.MacrosSurfaceRoughnessAndTechDemand(),
    exclude_from_spc.MacrosExcludeFromSPC(),
    parts_painting.MacrosPartsPainting(),
    # bulk_rename.BulkRenameMacros(),
    fast_mirror.FastMirrorMacros(),
    # fast_rollback.FastRollbackMacros(),
    fast_rvd.FastRVDMacros(),
    welding.WeldingMacros(),
]


def get_macros(codename: str) -> Macros:
    for m in macroses:
        if m.code_name == codename:
            return m
    raise Exception(f"Не найден макрос с codename=\"{codename}\"")


