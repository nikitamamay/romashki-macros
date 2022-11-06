
from HEAD import *


class binaryObjectsFilter:
    All = 0
    Faces = 2 ** 0
    Edges = 2 ** 1
    Vertexs = 2 ** 2
    CPlanes = 2 ** 3
    CAxis = 2 ** 4
    Parts = 2 ** 5
    Bodies = 2 ** 6
    Surfaces = 2 ** 7
    Sketches = 2 ** 8
    Curves = 2 ** 9
    CS = 2 ** 10
    ControlPoints = 2 ** 11
    Points3D = 2 ** 12
    Designations = 2 ** 13
    Thread = 2 ** 14
    test1 = 2 ** 15
    test2 = 2 ** 16
    test3 = 2 ** 17
    test4 = 2 ** 18



def get_objects_filter(app) -> int:
    ss: KAPI7.ISystemSettings = app.SystemSettings
    binary_mask = 0
    for i in range(1, 19):
        binary_mask |= (2 ** (i - 1)) * ss.ObjectsFilter3D(i)
    return binary_mask


def set_objects_filter(app, binary_mask: int):
    ss: KAPI7.ISystemSettings = app.SystemSettings
    if binary_mask == 0:
        ss.SetObjectsFilter3D(LDefin3D.ksFilterAll, True)
        return

    for i in range(1, 19):
        value = bool(binary_mask & (2 ** (i - 1)))
        ss.SetObjectsFilter3D(i, value)



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

if __name__ == "__main__":
    kO5, kO7 = get_kompas_objects()
    app = get_app7(kO7)
    bm = get_objects_filter(app)
    print(bm)
    print(bin(bm))
