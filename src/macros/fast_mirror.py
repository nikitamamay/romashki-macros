"""
Макрос предоставляет функционал для быстрого создания операции
"Зеркальный массив" именно для тел.

Макрос создает отдельные операции "Зеркальный массив" относительно выбранной
плоскости для каждого тела. Сами тела или их элементы (вершины, ребра, грани)
должны быть предварительно выбраны вместе с плоскостью.

Макрос позволяет быстро создавать зеркальный массив тел без переключения
фильтров выбора объектов.
Также макрос актуален для старых версий Компаса, в которых нет возможности
выбрать сразу несколько тел для создания зеркального массива за одну операцию.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path


PLANES_CLASSES = (
    KAPI7.IPlane3D,
    KAPI7.IPlane3DByPlaneCurve,
    KAPI7.IPlane3DTangentToFaceInPoint,
    KAPI7.IPlane3DByOffset,
    KAPI7.IPlane3DBy3Points,
    KAPI7.IPlane3DByAngle,
    KAPI7.IPlane3DByEdgeAndPoint,
    KAPI7.IPlane3DBy2Edge,
    KAPI7.IPlane3DParallelByPoint,
    KAPI7.IPlane3DPerpendicularByEdge,
    KAPI7.IPlane3DNormalToSurface,
    KAPI7.IPlane3DMiddle,
    KAPI7.IPlane3DByEdgeAndPlane,
    KAPI7.IPlane3DTangentToFace,
)


def fast_mirror() -> None:
    doc, toppart = open_part()
    selected_objs = get_selected(doc)

    bodies: list[KAPI7.IBody7] = list(filter(
        lambda obj: isinstance(obj, KAPI7.IBody7),
        selected_objs,
    ))

    elements: list[KAPI7.IBody7] = list(filter(
        lambda obj: isinstance(obj, (KAPI7.IVertex, KAPI7.IEdge, KAPI7.IFace)),
        selected_objs,
    ))

    for el in elements:
        f: KAPI7.IFeature7 = el.Owner
        for b in ensure_list(f.ResultBodies):
            if not b in bodies:
                bodies.append(b)

    if len(bodies) == 0:
        raise Exception("Выбрано 0 тел")

    planes: list[KAPI7.IPlane3D] = list(filter(
        lambda obj: isinstance(obj, PLANES_CLASSES),
        selected_objs,
    ))

    if len(planes) != 1:
        raise Exception(f"Выбрано {len(planes)} плоскостей (ожидается 1): {planes}")

    plane: KAPI7.IPlane3D = planes[0]

    feature_patterns: KAPI7.IFeaturePatterns = KAPI7.IModelContainer(toppart).FeaturePatterns

    for body in bodies:
        mp: KAPI7.IMirrorPattern = KAPI7.IMirrorPattern(feature_patterns.Add(LDefin3D.o3d_mirrorAllOperation))  # 49
        mp.Plane = plane
        mp.AddInitialObjects(body)
        mp.Update()
    toppart.Update()




class FastMirrorMacros(Macros):
    def __init__(self) -> None:
        super().__init__(
            "fast_mirror",
            "Быстрый зеркальный массив"
        )

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        btn_go = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/macros/fast_mirror.svg")), "")
        btn_go.clicked.connect(lambda: self.execute(fast_mirror))
        btn_go.setToolTip("Создать зеркальный массив выбранных тел\nотносительно выбранной плоскости")

        return {
            "кнопка запуска макроса": btn_go,
        }


if __name__ == "__main__":
    pass
