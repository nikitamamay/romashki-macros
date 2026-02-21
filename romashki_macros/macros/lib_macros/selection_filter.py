"""
Макрос-библиотека для получения и установки фильтра выбора объектов для 3D-модели.

"""

from .core import *


class binaryObjectsFilter:
    """
    Бинарная маска для указания фильтра выбора объектов в 3D-модели.
    """
    All           = 0
    Faces         = 1 << (1 - 1)
    Edges         = 1 << (2 - 1)
    Vertexs       = 1 << (3 - 1)
    CPlanes       = 1 << (4 - 1)
    CAxis         = 1 << (5 - 1)
    Parts         = 1 << (6 - 1)
    Bodies        = 1 << (7 - 1)
    Surfaces      = 1 << (8 - 1)
    Sketches      = 1 << (9 - 1)
    Curves        = 1 << (10 - 1)
    CS            = 1 << (11 - 1)
    ControlPoints = 1 << (12 - 1)
    Points3D      = 1 << (13 - 1)
    Designations  = 1 << (14 - 1)
    Thread        = 1 << (15 - 1)


# enum ksObjectsFilter3DEnum
#   ksFilterAll           = 0;
#   ksFilterFaces         = 1;
#   ksFilterEdges         = 2;
#   ksFilterVertexs       = 3;
#   ksFilterCPlanes       = 4;
#   ksFilterCAxis         = 5;
#   ksFilterParts         = 6;
#   ksFilterBodies        = 7;
#   ksFilterSurfaces      = 8;
#   ksFilterSketches      = 9;
#   ksFilterCurves        = 10;
#   ksFilterCS            = 11;
#   ksFilterControlPoints = 12;
#   ksFilterPoints3D      = 13;
#   ksFilterDesignations  = 14;
#   ksFilterThread        = 15;


def get_objects_filter() -> int:
    """
    Возвращает текущие активированные фильтры выбора объектов
    в виде бинарной маски (см. `binaryObjectsFilter`).
    """
    app = get_app7()
    ss: KAPI7.ISystemSettings = app.SystemSettings
    binary_mask = 0
    for i in range(1, 19):
        binary_mask |= (2 ** (i - 1)) * ss.ObjectsFilter3D(i)
    return binary_mask


def set_objects_filter(binary_mask: int) -> None:
    """
    Устанавливает фильтры выбора объектов на указанные
    в виде бинарной маски `binary_mask` (см. `binaryObjectsFilter`).
    """
    app = get_app7()
    ss: KAPI7.ISystemSettings = app.SystemSettings
    if binary_mask == 0:
        ss.SetObjectsFilter3D(LDefin3D.ksFilterAll, True)
        return

    for i in range(1, 19):
        value = bool(binary_mask & (2 ** (i - 1)))
        ss.SetObjectsFilter3D(i, value)



if __name__ == "__main__":
    kO5, kO7 = get_kompas_objects()
    app = get_app7(kO7)
    bm = get_objects_filter()
    print(bm)
    print(bin(bm))
