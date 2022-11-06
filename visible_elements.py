from HEAD import *


class VisibleElements:
    AuxiliaryGeom = 2 ** 0
    Axis = 2 ** 1
    ControlPoints = 2 ** 2
    Curves = 2 ** 3
    Designations = 2 ** 4
    Dimensions = 2 ** 5
    Places = 2 ** 6
    Planes = 2 ** 7
    Sketches = 2 ** 8
    Surfaces = 2 ** 9
    Threads = 2 ** 10
    LayoutGeometry = 2 ** 11
    AuxiliaryGeom_InComponents = 2 ** 16
    Axis_InComponents = 2 ** 17
    ControlPoints_InComponents = 2 ** 18
    Curves_InComponents = 2 ** 19
    Designations_InComponents = 2 ** 20
    Dimensions_InComponents = 2 ** 21
    Places_InComponents = 2 ** 22
    Planes_InComponents = 2 ** 23
    Sketches_InComponents = 2 ** 24
    Surfaces_InComponents = 2 ** 25
    Threads_InComponents = 2 ** 26
    LayoutGeometry_InComponents = 2 ** 27


def get_visible_elements(active_doc: KAPI7.IKompasDocument3D) -> int:
    binary_mask = 0

    active_doc1: KAPI7.IKompasDocument3D1 = KAPI7.IKompasDocument3D1(active_doc)

    active_doc.HideInComponentsMode = False

    binary_mask += VisibleElements.AuxiliaryGeom * (1 - int(active_doc.HideAllAuxiliaryGeom))
    binary_mask += VisibleElements.Axis * (1 - int(active_doc.HideAllAxis))
    binary_mask += VisibleElements.ControlPoints * (1 - int(active_doc.HideAllControlPoints))
    binary_mask += VisibleElements.Curves * (1 - int(active_doc.HideAllCurves))
    binary_mask += VisibleElements.Designations * (1 - int(active_doc.HideAllDesignations))
    binary_mask += VisibleElements.Dimensions * (1 - int(active_doc.HideAllDimensions))
    binary_mask += VisibleElements.Places * (1 - int(active_doc.HideAllPlaces))
    binary_mask += VisibleElements.Planes * (1 - int(active_doc.HideAllPlanes))
    binary_mask += VisibleElements.Sketches * (1 - int(active_doc.HideAllSketches))
    binary_mask += VisibleElements.Surfaces * (1 - int(active_doc.HideAllSurfaces))
    binary_mask += VisibleElements.Threads * (1 - int(active_doc.HideAllThreads))
    binary_mask += VisibleElements.Threads * (1 - int(active_doc1.HideLayoutGeometry))

    active_doc.HideInComponentsMode = True

    binary_mask += VisibleElements.AuxiliaryGeom_InComponents * (1 - int(active_doc.HideAllAuxiliaryGeom))
    binary_mask += VisibleElements.Axis_InComponents * (1 - int(active_doc.HideAllAxis))
    binary_mask += VisibleElements.ControlPoints_InComponents * (1 - int(active_doc.HideAllControlPoints))
    binary_mask += VisibleElements.Curves_InComponents * (1 - int(active_doc.HideAllCurves))
    binary_mask += VisibleElements.Designations_InComponents * (1 - int(active_doc.HideAllDesignations))
    binary_mask += VisibleElements.Dimensions_InComponents * (1 - int(active_doc.HideAllDimensions))
    binary_mask += VisibleElements.Places_InComponents * (1 - int(active_doc.HideAllPlaces))
    binary_mask += VisibleElements.Planes_InComponents * (1 - int(active_doc.HideAllPlanes))
    binary_mask += VisibleElements.Sketches_InComponents * (1 - int(active_doc.HideAllSketches))
    binary_mask += VisibleElements.Surfaces_InComponents * (1 - int(active_doc.HideAllSurfaces))
    binary_mask += VisibleElements.Threads_InComponents * (1 - int(active_doc.HideAllThreads))
    binary_mask += VisibleElements.LayoutGeometry_InComponents * (1 - int(active_doc1.HideLayoutGeometry))

    return binary_mask


def set_visible_elements(active_doc: KAPI7.IKompasDocument3D, binary_mask: int) -> None:
    active_doc1: KAPI7.IKompasDocument3D1 = KAPI7.IKompasDocument3D1(active_doc)

    active_doc.HideInComponentsMode = False

    active_doc.HideAllAuxiliaryGeom = not bool(binary_mask & VisibleElements.AuxiliaryGeom)
    active_doc.HideAllAxis = not bool(binary_mask & VisibleElements.Axis)
    active_doc.HideAllControlPoints = not bool(binary_mask & VisibleElements.ControlPoints)
    active_doc.HideAllCurves = not bool(binary_mask & VisibleElements.Curves)
    active_doc.HideAllDesignations = not bool(binary_mask & VisibleElements.Designations)
    active_doc.HideAllDimensions = not bool(binary_mask & VisibleElements.Dimensions)
    active_doc.HideAllPlaces = not bool(binary_mask & VisibleElements.Places)
    active_doc.HideAllPlanes = not bool(binary_mask & VisibleElements.Planes)
    active_doc.HideAllSketches = not bool(binary_mask & VisibleElements.Sketches)
    active_doc.HideAllSurfaces = not bool(binary_mask & VisibleElements.Surfaces)
    active_doc.HideAllThreads = not bool(binary_mask & VisibleElements.Threads)
    active_doc1.HideLayoutGeometry = not bool(binary_mask & VisibleElements.LayoutGeometry)

    active_doc.HideInComponentsMode = True

    active_doc.HideAllAuxiliaryGeom = not bool(binary_mask & VisibleElements.AuxiliaryGeom_InComponents)
    active_doc.HideAllAxis = not bool(binary_mask & VisibleElements.Axis_InComponents)
    active_doc.HideAllControlPoints = not bool(binary_mask & VisibleElements.ControlPoints_InComponents)
    active_doc.HideAllCurves = not bool(binary_mask & VisibleElements.Curves_InComponents)
    active_doc.HideAllDesignations = not bool(binary_mask & VisibleElements.Designations_InComponents)
    active_doc.HideAllDimensions = not bool(binary_mask & VisibleElements.Dimensions_InComponents)
    active_doc.HideAllPlaces = not bool(binary_mask & VisibleElements.Places_InComponents)
    active_doc.HideAllPlanes = not bool(binary_mask & VisibleElements.Planes_InComponents)
    active_doc.HideAllSketches = not bool(binary_mask & VisibleElements.Sketches_InComponents)
    active_doc.HideAllSurfaces = not bool(binary_mask & VisibleElements.Surfaces_InComponents)
    active_doc.HideAllThreads = not bool(binary_mask & VisibleElements.Threads_InComponents)
    active_doc1.HideLayoutGeometry = not bool(binary_mask & VisibleElements.LayoutGeometry)


if __name__ == "__main__":
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app = get_app7(iKompasObject7)
    active_doc: KAPI7.IKompasDocument3D = KAPI7.IKompasDocument3D(app.ActiveDocument)

    bm = get_visible_elements(active_doc)

    print(bin(bm))


