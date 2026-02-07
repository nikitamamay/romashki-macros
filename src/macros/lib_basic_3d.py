"""
test_gabarit
по мотивам https://forum.ascon.ru/index.php?topic=20903

получение габарита тела в заданной ЛСК

2026.02.07
"""

from .HEAD import *
# from . import lib_attributes

import math
from .. import math_utils
from .. import math_utils_3d

import typing
import traceback
import os


LCS_GABARIT = "ЛСК_ГАБАРИТ"
""" Имя ЛСК для определения габарита детали """


def get_gabarit_cs(part: KAPI7.IPart7) -> math_utils_3d.Matrix3x3:
    agc: KAPI7.IAuxiliaryGeomContainer = KAPI7.IAuxiliaryGeomContainer(part)
    lcss: KAPI7.ILocalCoordinateSystems = agc.LocalCoordinateSystems
    for i in range(lcss.Count):
        lcs: KAPI7.ILocalCoordinateSystem = lcss.LocalCoordinateSystem(i)
        if lcs.Name == LCS_GABARIT:
            vx = lcs.GetVector(LDefin3D.o3d_axisOX)[1:]
            vy = lcs.GetVector(LDefin3D.o3d_axisOY)[1:]
            vz = lcs.GetVector(LDefin3D.o3d_axisOZ)[1:]
            return math_utils_3d.Matrix3x3.from_array([vx, vy, vz])
    else:
        # TODO вернуть АСК детали в сборке через get_transform_function() (или Placement ?)
        pass

    return math_utils_3d.Matrix3x3.get_identity_matrix()



def get_gabarit_in_lcs():
    """
    Печатает габарит каждого тела модели, рассчитанный по вершинам этих твёрдых
    тел в локальной системе координат с именем "ЛСК_ГАБАРИТ" или глобальной системе
    координат, если такая локальная не найдена.

    Вероятно, даст неверные результаты, если крайней точкой тела (детали)
    будет не вершина, а ребро или поверхность. Например, в случае тела вращения.

    Может быть применимо для очень простых случаев, например, для определения
    габаритов листовых деталей и профилей металлоконструкций.
    """
    doc, part = open_part()

    point_gabarit_min: math_utils_3d.Point3d = math_utils_3d.Point3d()
    point_gabarit_max: math_utils_3d.Point3d = math_utils_3d.Point3d()
    gabarit_cs: math_utils_3d.Matrix3x3 = get_gabarit_cs(part)

    m_rotate, _ = math_utils_3d.get_CS_transform_function(
        gabarit_cs,
        math_utils_3d.Matrix3x3.get_identity_matrix(),
    )

    def update_gabarit_points(point: math_utils_3d.Point3d) -> None:
        point_gabarit_max.x = max(point.x, point_gabarit_max.x)
        point_gabarit_max.y = max(point.y, point_gabarit_max.y)
        point_gabarit_max.z = max(point.z, point_gabarit_max.z)
        point_gabarit_min.x = min(point.x, point_gabarit_min.x)
        point_gabarit_min.y = min(point.y, point_gabarit_min.y)
        point_gabarit_min.z = min(point.z, point_gabarit_min.z)


    bodies: list[KAPI7.IBody7] = ensure_list(KAPI7.IFeature7(part).ResultBodies)
    # bodies = get_selected(doc, KAPI7.IBody7)

    if len(bodies) == 0:
        raise Exception(f"Не найдены тела в модели")

    for body in bodies:
        f: KAPI7.IFeature7 = KAPI7.IFeature7(body)
        vertexes: typing.Iterable[KAPI7.IVertex] = filter(
            lambda el: isinstance(el, KAPI7.IVertex),
            ensure_list(f.ModelObjects(0))  # ksObjectVertex 11279 Вершина - но это так не работает; выдает пустой список.
        )

        i = 1
        try:
            vertex = next(vertexes)
            point = math_utils_3d.Point3d.from_array(vertex.GetPoint()[1:]).transform(m_rotate)
            point_gabarit_min = point.copy()
            point_gabarit_max = point.copy()
        except StopIteration:
            raise Exception(f"Не найдены вершины для тела '{body.Name}'")

        for vertex in vertexes:
            point = math_utils_3d.Point3d.from_array(vertex.GetPoint()[1:]).transform(m_rotate)
            update_gabarit_points(point)
            i += 1

        gabarit = [abs(x) for x in math_utils_3d.Vector3d.from_points(point_gabarit_max, point_gabarit_min).to_array()]
        print(f"тело '{body.Name}', {i} вершин, gabarit={gabarit}")






if __name__ == "__main__":
    get_gabarit_in_lcs()
