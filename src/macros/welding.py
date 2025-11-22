"""
Макрос для автоматизированного создания упрощенных твердотельных обозначений
сварных швов.

Идея создания именно твердотельных моделей сварных швов обусловлена тем, что
схематичные условные обозначения в библиотеке Компаса имеют недостатки:
* они могут быть скрыты так же, как и другие условные обозначения (размеры,
линии-выноски), и их сложно показать в модели так, чтобы они были читаемы (нужно
постоянно делать огромное число действий по скрытию и отображению элементов);
* не стандартизованы (?) для пересохранения в других форматах;
* порядок создания этих условных обозначений сварных швов в Компасе излишне
сложный и строгий (нужно постоянно назначать тип шва, катет, его параметры и т.д.)

Целью же данного макроса является именно упрощенное обозначение тех мест, где
сварные швы вообще должны быть. Более того, твердые тела, пусть они сделаны
условно (цилиндрической формы и с пересечениями), но их можно обозначить каким-то
ярким цветом и они будут выделяться на фоне обычных деталей.
Возможно и обозначать получаемые твердые тела сварных швов линиями-выносками
с обозначениями сварки по ГОСТ; можно тела разных по характеристикам швов
обозначать разными цветами.


Сценарий работы макроса следующий. Твердые тела сварных швов можно создавать
в основной сборке со сварными деталями, но удобнее задействовать еще одну модель,
предназначенную только для сварных швов; её следует вставить в основную сборку
без включения в спецификацию.
В основной сборке пользователь выбирает объекты модели, по которым происходит
сварка:
* набор точек или вершин
    для формирования одной линии сварного шва через эти точки;
* ребра, ломаные линии, отрезки, линии эскизов
    для формирования нескольких линий сварных швов по этим ребрам;
* грани и эскизы целиком и, по необходимости, точки
    для формирования сварных швов по контурам граней или ребер эскиза,
    а при выборе точек - только по тем контурам, если они содержат хотя бы одну
    из выбранных точек.
Затем выполняется команда макроса. В модели для сварных швов создаются
*неассоциативные* ломаные линии по выбранным ранее ребрам, создается эскиз
с многранником (или окружностью) и выполняется кинематическая операция
(операция по траектории) для создания твердого тела сварного шва.


Макрос реализован как прототип для проверки идеи автоматизированного создания
твердотельных обозначений сварных швов.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path

from src import math_utils
import math
import traceback


RMWELD = "RMWeld"

Point: typing.TypeAlias = tuple[float, float, float]
Line: typing.TypeAlias = list[Point]
TransformFunction: typing.TypeAlias = typing.Callable[[Point], Point]


class WeldLineSettings:
    """
    Класс настроек алгоритма создания ломаных линий сварных швов.
    """
    def __init__(
            self,
            diameter: float = 10.0,
            layer: int = -1,
            section_edges_count: int = 8,
            ) -> None:
        self.diameter: float = diameter
        """диаметр валика твердого тела шва"""

        self.section_edges_count: int = section_edges_count
        """Количество сторон многоугольника в сечении валика шва. При значении `<= 0` будет использоваться окружность."""

        self.step_default: float = diameter * 3
        """длина шага вдоль кривой по-умолчанию"""

        self.step_min: float = diameter * 0.75
        """минимальная длина шага вдоль кривой"""

        self.max_deviation_from_arc: float = diameter * 0.25
        """максимальное отклонение ломаной от дуги (длина высоты, опущенной с точки середины дуги на хорду)"""

        self.merge_distance: float = diameter * 0.2
        """расстояние между двумя точками, которые следует объединять"""

        self.layer: int = layer
        """номер слоя, на который переносятся объекты построения тел швов. Если -1, то не менять слой"""


def get_transform_function(toppart5: KAPI5.ksPart, element_part: KAPI5.ksPart) -> TransformFunction:
    """
    Возвращает функцию для преобразования координат точки из системы координат
    дочерней детали `element_part` в систему координат основной сборки `toppart5`.
    """
    assert isinstance(toppart5, KAPI5.ksPart)
    assert isinstance(element_part, KAPI5.ksPart)
    def _transform_function(point: Point) -> Point:
        return toppart5.TransformPoint(point[0], point[1], point[2], element_part)[1:]
    return _transform_function


def get_line_of_curve(
        curve: KAPI5.ksCurve3D,
        transform_function: TransformFunction,
        wls: WeldLineSettings,
        ) -> Line:
    """
    Для данной математической кривой `curve` возвращает массив точек для построения
    ломаной линии, аппроксимированной к этой кривой.

    См. также `get_lines_of_element()`.
    """
    line: Line = []

    curve_length = curve.GetLength(1)  # 1 = в миллиметрах

    minT = curve.GetParamMin()
    maxT = curve.GetParamMax()

    def _get_T_from_length(length: float) -> float:
        return  minT + (maxT - minT) / curve_length * length

    def _get_point(curve_T: float) -> Point:
        p: Point = curve.GetPoint(curve_T)[1:]
        return transform_function(p)

    # прямая
    if curve.IsLineSeg():
        start = _get_point(_get_T_from_length(0))
        end = _get_point(_get_T_from_length(curve_length))
        line.append(start)
        line.append(end)

    # кривая
    else:
        round_function = int

        # если окружность, тогда рекомендуемый шаг = длина хорды с отклонением от точки середины дуги, равным wls.max_deviation_from_arc
        if curve.IsArc() or curve.IsCircle() or curve.IsEllipse():
            if curve.IsEllipse():
                r = curve.GetCurveParam().minorRadius
            else:
                r = curve.GetCurveParam().radius

            if r > wls.max_deviation_from_arc / 2:
                step_recommended = max(
                    math.sqrt(8 * r * wls.max_deviation_from_arc - 4 * wls.max_deviation_from_arc ** 2),
                    wls.step_min
                )
                round_function = math.ceil
            else:
                step_recommended = wls.step_min
        else:
            step_recommended = wls.step_default

        segments_count = max(
            1 + 2 * int(curve.IsClosed()),
            round_function(curve_length / step_recommended)
        )
        step_real = curve_length / segments_count

        line.append(_get_point(_get_T_from_length(0)))

        for i in range(1, segments_count):
            line.append(_get_point(_get_T_from_length(step_real * i)))

        line.append(_get_point(_get_T_from_length(curve_length)))

    return line


def get_lines_of_element(
        el: KAPI5.ksEntity,
        transform_function: TransformFunction,
        wls: WeldLineSettings,
        ) -> list[Line]:
    """
    Возвращает массивы точек, представляющих собой линии сварных швов для объекта
    модели `el`.
    """
    if isinstance(el, KAPI5.ksEntity):
        # ребро, линия эскиза
        if el.type == LDefin3D.o3d_edge:
            edge: KAPI5.ksEdgeDefinition = el.GetDefinition()
            curve: KAPI5.ksCurve3D = edge.GetCurve3D()

            line = get_line_of_curve(curve, transform_function, wls)
            return [line]

        # ломаная 3D
        elif el.type == LDefin3D.o3d_polyline:
            line: Line = []
            pl: KAPI7.IPolyLine = transfer_to_7(el)
            for i in range(pl.VertexCount):
                cvp: KAPI7.ICurveVertexParam = pl.VertexParams(i)
                point_local = cvp.GetParamVertex()[1:4]
                point = transform_function(point_local)
                line.append(point)
            return [line]

        # отрезок 3D
        elif el.type == 570:
            tr_func = transform_function
            ls: KAPI7.ILineSegment3D = transfer_to_7(el)
            start = tr_func(ls.GetPoint(True)[1:])
            end = tr_func(ls.GetPoint(False)[1:])
            line = [start, end]
            return [line]

        # # сплайн 3D
        # elif el.type == LDefin3D.o3d_spline:
        #     s = transfer_to_7(el, LDefin3D.o3d_spline)
        #     print(s)

        else:
            print("not supported ksEntity.type =", el.type, el)

    else:
        print("not supported", el)

    return []


def get_point_of_element(vertex: KAPI5.ksEntity, transform_function: TransformFunction) -> Point | None:
    """
    Для вершины или 3D-точки `vertex` возвращает её координату
    в системе координат основной сборки.
    """

    if vertex.type == LDefin3D.o3d_vertex:
        vd: KAPI5.ksVertexDefinition = vertex.GetDefinition()
        point_local: Point = vd.GetPoint()[1:]
        point = transform_function(point_local)
        return point

    elif vertex.type == LDefin3D.o3d_point3D:
        point7: KAPI7.IPoint3D = transfer_to_7(vertex)
        point_local = (point7.X, point7.Y, point7.Z)
        point = transform_function(point_local)
        return point

    else:
        print("unsupported point type:", vertex.type, vertex)

    return None


def construct_line(points: Line) -> Line:
    """
    Алгоритм построения линии по ближайшим друг к другу точкам.

    Из массива неупорядоченных точек `points` создает
    массив точек (линию `Line`), упорядоченных так, что расстояние между
    двумя соседними точками этой линии минимально. Первой точкой линии выступает
    точка, наиболее удаленная от всех остальных.
    """
    def _find_min(arr: list[float], ignore_indexes: list[int]):
        return min(
            filter(
                lambda x: not x[0] in ignore_indexes,
                enumerate(arr)
            ),
            key=lambda x: x[1]
        )[0]

    if len(points) <= 2:
        return points

    distances: list[list[float]] = [[0.0 for p in points] for p in points]

    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d: float = calc_distance(points[i], points[j])
            distances[i][j] = d
            distances[j][i] = d

    farthest_point_i = max(enumerate(distances), key=lambda x: sum(x[1]))[0]
    line_indexes = [farthest_point_i]

    for _ in range(len(distances) - 1):
        last_point_i = line_indexes[-1]
        i = _find_min(distances[last_point_i], line_indexes)
        line_indexes.append(i)

    line: Line = list(map(lambda i: points[i], line_indexes))

    return line


def is_point_on_line(
        point: Point,
        line: Line,
        do_check_between_points: bool = False,
        max_deviation: float = 0.001,
        ) -> bool:
    """
    Проверяет, содержит ли линия `line` точку `point`.

    См. также `are_points_same()`, `create_welds()`.
    """
    if do_check_between_points:
        raise Exception("Not implemented")
    else:
        for line_point in line:
            if are_points_same(point, line_point, max_deviation):
                return True
        return False


def are_points_same(pointA: Point, pointB: Point, max_deviation: float) -> bool:
    """
    Проверка двух точек на совпадение.

    Точки считаются совпадающими, если лежат в пределах куба со стороной `max_deviation`.
    """
    return abs(pointA[0] - pointB[0]) < max_deviation \
        and abs(pointA[1] - pointB[1]) < max_deviation \
        and abs(pointA[2] - pointB[2]) < max_deviation


def calc_distance(pointA: Point, pointB: Point) -> float:
    """
    Возвращает евклидово расстояние между двумя точками.
    """
    return math.sqrt((pointA[0] - pointB[0]) ** 2 + (pointA[1] - pointB[1]) ** 2 + (pointA[2] - pointB[2]) ** 2)


def merge_lines(lines: list[Line], max_deviation: float) -> list[Line]:
    """
    Объединяет линии, начальные и/или конечные точки которых совпадают.

    См. также `are_points_same()`.
    """
    has_changes = True
    while has_changes:
        has_changes = False
        i = 0
        while i < len(lines):
            j = i + 1
            while j < len(lines):
                line_A = lines[i]
                start_A = line_A[0]
                end_A = line_A[-1]

                line_B = lines[j]
                start_B = line_B[0]
                end_B = line_B[-1]

                # Aaaaaaaaaaaaaaaa
                # Bbbbbb
                if are_points_same(start_A, start_B, max_deviation):
                    for point in line_B[1:]:  # no need for reversed(), since insertion at index=0 already makes sequence reversed
                        line_A.insert(0, point)
                    lines.pop(j)
                    has_changes = True

                #      Aaaaaaaaaaaaaaaa
                # bbbbbB
                elif are_points_same(start_A, end_B, max_deviation):
                    for k, point in enumerate(line_B[:-1]):
                        line_A.insert(k, point)
                    lines.pop(j)
                    has_changes = True

                # aaaaaaaaaaaaaaaA
                #                Bbbbbb
                elif are_points_same(end_A, start_B, max_deviation):
                    line_A.extend(line_B[1:])
                    lines.pop(j)
                    has_changes = True

                # aaaaaaaaaaaaaaaA
                #           bbbbbB
                elif are_points_same(end_A, end_B, max_deviation):
                    line_A.extend(reversed(line_B[:-1]))
                    lines.pop(j)
                    has_changes = True

                else:
                    j += 1
            i += 1
    return lines


def remove_empty_lines(lines: list[Line]) -> list[Line]:
    """
    Удаляет из списка `lines` некорректные линии (которые содержат меньше двух точек).

    Изменяет сам переденный список `lines`, не_создавая новый.
    """
    i = 0
    while i < len(lines):
        if len(lines[i]) < 2:
            lines.pop(i)
        else:
            i += 1
    return lines


def extend_list_with_difference(base_list: list, new_list: list, key=lambda el: el) -> None:
    """
    Изменяет список `base_list` так, чтобы он образовывал симметричную разность
    двух списков.
    Аналог `set.symmetric_difference()`.

    Добавляет в список `base_list` только те элементы из списка `new_list`, которых
    нет в `base_list`. Если элемент из `new_list` уже есть в `base_list`, он
    удаляется из `base_list`.
    """

    for new_el in new_list:
        do_add = True
        j = 0
        while j < len(base_list):
            base_el = base_list[j]
            if key(new_el) == key(base_el):
                base_list.pop(j)
                do_add = False
                break
            j += 1
        if do_add:
            base_list.append(new_el)


def create_welds(
        weldpart_path: str,
        wls: WeldLineSettings,
        do_create_polylines_only: bool = False,
        prefix: str = RMWELD,
        ) -> None:
    """
    Анализирует выбранные в текущей модели объекты.
    Формирует ломаные линии сварных швов.
    Создает твердые тела сварных швов, если `do_create_polylines_only == False`.
    """
    weldpart_path = weldpart_path.strip()
    if weldpart_path != "":
        weldpart_path = os.path.normpath(weldpart_path)

    # анализ выбранных объектов текущей модели

    doc5, toppart5 = open_part_K5()
    selected_entities: list[KAPI5.ksEntity] = get_selected_K5(doc5, (KAPI5.ksEntity))

    if len(selected_entities) == 0:
        raise Exception("Не выбраны объекты для формирования сварных швов.")

    selected_edge_objs = list(filter(
        lambda e: e.type in (LDefin3D.o3d_edge, LDefin3D.o3d_polyline, 570),  # 570 - отрезок3D
        selected_entities
    ))
    selected_vertex_objs = list(filter(
        lambda e: e.type in (LDefin3D.o3d_vertex, LDefin3D.o3d_point3D),
        selected_entities
    ))
    selected_multiedge_objs = list(filter(
        lambda e: e.type in (LDefin3D.o3d_face, LDefin3D.o3d_sketch),
        selected_entities
    ))
    print(f"выбранных точек:                  {len(selected_vertex_objs)}")
    print(f"выбранных многореберных объектов: {len(selected_multiedge_objs)}")
    print(f"выбранных реберных объектов:      {len(selected_edge_objs)}")

    lines: list[Line] = []
    vertexes_points: list[Point] = []

    # получение координат выбранных точек

    for entity in selected_vertex_objs:
        tr_func = get_transform_function(toppart5, entity.GetParent())
        p: Point|None = get_point_of_element(entity, tr_func)
        if not p is None:
            vertexes_points.append(p)

    # формирование точек ломаных линий через точки, если выбраны только точки

    if len(selected_multiedge_objs) == 0 and len(selected_vertex_objs) >= 2:
        line_of_vertexes = construct_line(vertexes_points)
        if len(line_of_vertexes) >= 2:
            lines.append(line_of_vertexes)
        print(f"Шов по отдельным точкам из {len(line_of_vertexes)} точек.")


    # формирование точек ломаных линий через ребра граней и эскизов, содержащие выбранные точки

    if len(selected_multiedge_objs) > 0:
        # определение ребер

        edges_set: list[tuple[int, KAPI5.ksCurve3D, TransformFunction]] = []
        faces_lines: list[Line] = []

        for entity in selected_multiedge_objs:
            entity_edges: list[tuple[int, KAPI5.ksCurve3D, TransformFunction]] = []
            tr_func = get_transform_function(toppart5, entity.GetParent())

            # грань (создание сварных швов по всем ребрам-границам)
            if entity.type == LDefin3D.o3d_face:
                lines: list[Line] = []
                face_def: KAPI5.ksFaceDefinition = entity.GetDefinition()
                ec: KAPI5.ksEdgeCollection = face_def.EdgeCollection()
                for i in range(ec.GetCount()):
                    edge5: KAPI5.ksEdgeDefinition = ec.GetByIndex(i)
                    curve: KAPI5.ksCurve3D = edge5.GetCurve3D()
                    edge7: KAPI7.IEdge = transfer_to_7(edge5)
                    entity_edges.append((edge7.Reference, curve, tr_func))  # FIXME правильно ли захватывается переменная tr_func ? (выбрать одновременно из деталей с разными ЛСК)

            # эскиз (создание сварных швов по всем линиям эскиза)
            if entity.type == LDefin3D.o3d_sketch:
                sketch7: KAPI7.ISketch = transfer_to_7(entity, LDefin3D.o3d_sketch)
                feature: KAPI7.IFeature7 = KAPI7.IFeature7(sketch7)
                edges: list[KAPI7.IEdge] = ensure_list(feature.ModelObjects(LDefin3D.o3d_edge))
                for edge7 in edges:
                    curve = transfer_to_K5(edge7.MathCurve)
                    entity_edges.append((edge7.Reference, curve, tr_func))  # FIXME правильно ли захватывается переменная tr_func ? (выбрать одновременно из деталей с разными ЛСК)

            # удаление общих ребер
            extend_list_with_difference(edges_set, entity_edges, key=lambda el: el[0])

        # формирование ломаных

        for _, curve, tr_func in edges_set:
            line = get_line_of_curve(curve, tr_func, wls)
            faces_lines.append(line)

        # склейка ломаных
        remove_empty_lines(faces_lines)
        merge_lines(faces_lines, wls.merge_distance)

        # если выбраны точки - удаление ломаных, не_содержащих точки
        if len(selected_vertex_objs) > 0:
            i = 0
            while i < len(faces_lines):
                line = faces_lines[i]
                for point in vertexes_points:
                    if is_point_on_line(point, line, False, wls.diameter / 100):
                        i += 1
                        break
                else:
                    faces_lines.pop(i)

        print(f"Швов по многореберным объектам: {len(faces_lines)}")
        lines.extend(faces_lines)

    # формирование точек ломаных линий для отдельных ребер (независимо от выбранных точек)

    if len(selected_edge_objs) > 0:
        edges_lines: list[Line] = []

        for entity in selected_edge_objs:
            tr_func = get_transform_function(toppart5, entity.GetParent())
            single_edge_lines = get_lines_of_element(entity, tr_func, wls)
            edges_lines.extend(single_edge_lines)

        remove_empty_lines(edges_lines)
        merge_lines(edges_lines, wls.merge_distance)

        print(f"Швов по отдельным реберным объектам: {len(edges_lines)}")
        lines.extend(edges_lines)

    # склейка линий швов, полученных разными методами (например, выделены ребра + несколько точек)

    remove_empty_lines(lines)
    merge_lines(lines, wls.merge_distance)

    # конец формирования ломаных

    print(f"Всего непрерывных сварных швов: {len(lines)}")

    if len(lines) == 0:
        raise Exception("Не сформированы линии сварных швов.")

    # создание прерывистых швов

    pass  # TODO

    # создание ломаных линий швов в модели

    if weldpart_path != "":
        previous_doc_path = remember_opened_document()

    welddoc, weldpart = open_part(weldpart_path)

    s_errors: str = ""
    polylines7: list[KAPI7.IPolyLine] = []

    for line in lines:
        try:
            pl7: KAPI7.IPolyLine = create_weld_polyline(weldpart, line, wls, not do_create_polylines_only, prefix)
            polylines7.append(pl7)
        except Exception as e:
            s_errors += traceback.format_exc() + "\n"

    # создание твердых тел сварных швов

    if not do_create_polylines_only:
        for pl7 in polylines7:
            pl5: KAPI5.ksPolyLineDefinition = transfer_to_K5(pl7)
            create_weld_body(weldpart, pl5, wls, prefix)

        if weldpart_path != "":
            welddoc.Save()

    if weldpart_path != "":
        restore_opened_document(previous_doc_path)
        kompas5, kompas7 = get_kompas_objects()
        kompas5.ksRefreshActiveWindow()

    if s_errors != "":
        raise Exception(s_errors)


def create_weld_polyline(
        part: KAPI7.IPart7,
        line: Line,
        wls: WeldLineSettings,
        do_hide: bool = False,
        prefix: str = RMWELD,
        ) -> KAPI7.IPolyLine:
    """
    Создает ломаную линию в модели `part` по точкам `line`.
    """
    assert len(line) >= 2, f"Попытка создать линию по {len(line)} точкам"

    agc = KAPI7.IAuxiliaryGeomContainer(part)
    pl: KAPI7.IPolyLine = agc.PolyLines.Add()

    # проверка линии шва на замкнутость
    if len(line) > 2 and are_points_same(line[0], line[-1], wls.merge_distance):
        pl.Closed = True
        line = line[:-1]

    for x, y, z in line:
        cvp: KAPI7.ICurveVertexParam = pl.AddVertex(-1)
        cvp.SetParamVertex(x, y, z, 0)
        cvp.Update()

    is_ok = pl.Update()
    pl.Hidden = do_hide
    pl.Name = (prefix + " " + pl.Name).strip()
    # mo1 = KAPI7.IModelObject1(pl)
    # if wls.layer != -1:
    #     mo1.LayerNumber = wls.layer
    is_ok = pl.Update()
    if is_ok:
        print(f"Создана ломаная линия '{pl.Name}'")  # на слое {mo1.LayerNumber}")
    else:
        raise Exception(f"Не удалось создать ломаную линию по {len(line)} точкам: {line}")
    return pl


def create_weld_body(
        part: KAPI7.IPart7,
        polyline5: KAPI5.ksPolyLineDefinition,
        wls: WeldLineSettings,
        prefix: str = RMWELD,
        ) -> None:
    """
    Создает твердое тело сварного шва по ломаной `polyline5` в модели `part`.
    """
    assert isinstance(part, KAPI7.IPart7)
    assert isinstance(polyline5, KAPI5.ksPolyLineDefinition)

    kompas5, kompas7 = get_kompas_objects()

    part5: KAPI5.ksPart = transfer_to_K5(part)

    # создание плоскости для эскиза
    # (через первую точку ломаной перпендикулярно первому сегменту ломаной)

    plane5_entity: KAPI5.ksEntity = part5.NewEntity(LDefin3D.o3d_planePerpendicular)
    plane5: KAPI5.ksPlanePerpendicularDefinition = plane5_entity.GetDefinition()
    edge5: KAPI5.ksEdgeDefinition = polyline5.EdgeCollection().First()
    vertex5: KAPI5.ksEntity = polyline5.GetPointParams(0).GetVertex()
    plane5.SetEdge(edge5)
    plane5.SetPoint(vertex5)
    plane5_entity.hidden = True
    is_ok = plane5_entity.Update()
    plane5_entity.name = (prefix + " " + plane5_entity.name).strip()
    is_ok = plane5_entity.Update()
    if is_ok:
        print(f"Создана плоскость '{plane5_entity.name}'")
    else:
        raise Exception(f"Не удалось создать плоскость по ломаной '{polyline5.name}'")
    plane: KAPI7.IPlane3DPerpendicularByEdge = transfer_to_7(plane5_entity)

    # создание эскиза с фигурой -- сечением шва

    mc = KAPI7.IModelContainer(part)
    sketch: KAPI7.ISketch = mc.Sketchs.Add()
    sketch.Plane = plane
    is_ok = sketch.Update()
    sketch.Name = (prefix + " " + sketch.Name).strip()
    is_ok = sketch.Update()
    if is_ok:
        print(f"Создан эскиз '{sketch.Name}'")
    else:
        raise Exception(f"Не удалось создать эскиз на плоскости '{plane5_entity.name}'")

    doc2d: KAPI7.IFragmentDocument = sketch.BeginEdit()
    view: KAPI7.IView = doc2d.ViewsAndLayersManager.Views.View(0)
    dc: KAPI7.IDrawingContainer = KAPI7.IDrawingContainer(view)

    sketch5 = transfer_to_K5(sketch)  # так же нужен для ksBossEvolutionDefinition (см. ниже)
    ref = sketch5.AddProjectionOf(vertex5)
    dg: KAPI7.IDrawingGroup = kompas5.TransferReference(ref, 0)
    point: KAPI7.IPoint = ensure_list(dg.Objects())[0]
    x, y = point.X, point.Y  # координаты центра сечения валика шва

    if wls.section_edges_count <= 0:
        circle: KAPI7.ICircle = dc.Circles.Add()
        circle.Radius = wls.diameter / 2
        circle.Xc = x
        circle.Yc = y
        circle.Update()
    else:
        rp: KAPI7.IRegularPolygon = dc.RegularPolygons.Add()
        rp.Count = wls.section_edges_count  # Количество вершин многоугольника
        rp.Describe = True  # Признак построения по вписанной окружности
        rp.Radius = wls.diameter / 2
        rp.Xc = x
        rp.Yc = y
        rp.Update()

    sketch.EndEdit()
    print(f"Завершено редактирование эскиза '{sketch.Name}'")

    # создание кинематической операции (вытягивание по траектории)

    evolution_e: KAPI5.ksEntity = part5.NewEntity(LDefin3D.o3d_bossEvolution)
    base_evolution: KAPI5.ksBossEvolutionDefinition = evolution_e.GetDefinition()
    base_evolution.SetSketch(sketch5)
    base_evolution.ChooseBodies().ChooseBodiesType = 0  # новое тело
    ec: KAPI5.ksEntityCollection = base_evolution.PathPartArray()
    ec.Add(polyline5)
    is_ok = evolution_e.Update()
    evolution_e.name = (prefix + " " + evolution_e.name).strip()
    is_ok = evolution_e.Update()
    if is_ok:
        print(f"Создано вытягивание по траектории '{evolution_e.name}'")
    else:
        raise Exception(f"Не удалось создать вытягивание по траектории по ломаной линии '{polyline5.name}' с эскизом '{sketch.Name}'")

    # переименование тела от операции вытягивания и задание слоя и цвета

    bc: KAPI5.ksBodyCollection = evolution_e.BodyCollection()
    for i in range(bc.GetCount()):
        b5: KAPI5.ksBody = bc.GetByIndex(i)
        b7: KAPI7.IBody7 = transfer_to_7(b5)
        b7.Name = (prefix + " " + b7.Name).strip()
        if wls.layer != -1:
            b7.LayerNumber = wls.layer
        cp = KAPI7.IColorParam7(b7)
        cp.UseColor = 3  # цвет слоя
        is_ok = b7.Update()
        if is_ok:
            print(f"Переименовано тело шва '{b7.Name}' на слое {b7.LayerNumber}.")
        else:
            print(f"Не удалось изменить параметры твердого тела шва '{b7.Name}'")


def find_weld_polylines_without_bodies(
        part: KAPI7.IPart7,
        prefix: str = RMWELD,
        ) -> list[KAPI7.IPolyLine]:
    """
    Возвращает ломаные линии сварных швов, по которым не созданы твердые тела швов.

    Признаки этих ломаных линий:
    * имеют особое наименование,
    * не_имеют дочерних операций вытягивания по траектории.
    """
    polylines: list[KAPI7.IPolyLine] = []

    agc = KAPI7.IAuxiliaryGeomContainer(part)
    pls: KAPI7.IPolyLines = agc.PolyLines

    for i in range(pls.Count):
        pl: KAPI7.IPolyLine = pls.Item(i)
        if pl.Name.startswith(prefix):
            mo1 = KAPI7.IModelObject1(pl)
            children: list[KAPI7.IModelObject] = ensure_list(mo1.Childrens(1))  # 1 - все отношения (ksRelationTypeEnum)
            for mo in children:
                if mo.Name.startswith(prefix) and mo.Type == 11276:  # 11276 - элемент по траектории
                    break
            else:
                polylines.append(pl)

    return polylines

def find_and_create_weld_bodies(
        weldpart_path: str,
        wls: WeldLineSettings,
        do_hide_polylines: bool = False,
        prefix: str = RMWELD,
        ) -> None:
    """
    Находит в модели ломаные линии сварных швов с несозданными твердыми телами,
    и создает твердые тела швов по этим линиям.

    См. также `find_weld_polylines_without_bodies()`.
    """
    if weldpart_path != "":
        previous_doc_path = remember_opened_document()

    doc, toppart = open_part(weldpart_path)
    polylines7 = find_weld_polylines_without_bodies(toppart, prefix)

    print(f"Найдено {len(polylines7)} ломаных линий без твердотельных построений: {[pl.Name for pl in polylines7]}")

    errors = ""

    for pl7 in polylines7:
        try:
            pl5: KAPI5.ksPolyLineDefinition = transfer_to_K5(pl7)
            create_weld_body(toppart, pl5, wls, prefix)
            if do_hide_polylines:
                pl7.Hidden = True
                pl7.Update()
        except Exception as e:
            errors += traceback.format_exc() + "\n"

    print("Создание твердых тел завершено.")

    if weldpart_path != "":
        welddoc.Save()
        restore_opened_document(previous_doc_path)

        kompas5, kompas7 = get_kompas_objects()
        kompas5.ksRefreshActiveWindow()

    if errors != "":
        raise Exception(errors)


class WeldSpecInputWidget(QtWidgets.QWidget):
    data_edited = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self._sb_diameter = gui_widgets.SpinBox()
        self._sb_diameter.setPrefix("⌀")
        self._sb_diameter.valueChanged.connect(lambda: self.data_edited.emit())

        self._sb_layer = QtWidgets.QSpinBox()
        self._sb_layer.setRange(-1, 10**9)
        self._sb_layer.setSingleStep(1)
        self._sb_layer.valueChanged.connect(lambda: self.data_edited.emit())

        self._layout = QtWidgets.QGridLayout()
        self._layout.setContentsMargins(0,0,0,0)
        self._layout.addWidget(QtWidgets.QLabel("Диаметр условного валика шва"), 0, 0, 1, 1)
        self._layout.addWidget(self._sb_diameter, 0, 1, 1, 1)
        self._layout.addWidget(QtWidgets.QLabel("Слой для твёрдых тел шва\n(укажите -1 для использования активного слоя)"), 1, 0, 1, 1)
        self._layout.addWidget(self._sb_layer, 1, 1, 1, 1)
        self.setLayout(self._layout)

    def set_data(self, diameter: float, layer: int) -> None:
        self._sb_diameter.setValue(diameter)
        self._sb_layer.setValue(layer)

    def get_data(self) -> tuple[float, int]:
        return self._sb_diameter.value(), self._sb_layer.value()

    def clear(self) -> None:
        self.set_data(10.0, -1)


class WeldingMacros(Macros):
    DATAROLE_DIAMETER = 101
    DATAROLE_LAYER = 102

    def __init__(self) -> None:
        super().__init__(
            "welding",
            "Сварные швы"
        )

        self._welddoc_path = ""

    def check_config(self) -> None:
        try:
            assert isinstance(self._config["prefix"], str)
        except:
            self._config["prefix"] = RMWELD
            config.save_delayed()

        try:
            assert isinstance(self._config["do_create_in_active_document"], bool)
        except:
            self._config["do_create_in_active_document"] = True
            config.save_delayed()

        try:
            assert isinstance(self._config["section_edges_count"], int)
        except:
            self._config["section_edges_count"] = 8
            config.save_delayed()

        try:
            assert isinstance(self._config["weld_specs"], list)
            assert len(self._config["weld_specs"]) > 0
            for spec in self._config["weld_specs"]:
                assert isinstance(spec, list)
                assert len(spec) == 3
                assert isinstance(spec[0], str)
                assert isinstance(spec[1], (float, int))
                assert isinstance(spec[2], int)
        except:
            self._config["weld_specs"] = [
                ["◺5", 10.0, -1],
            ]
            config.save_delayed()

        try:
            assert isinstance(self._config["active_weld_spec"], int)
            assert 0 <= self._config["active_weld_spec"] < len(self._config["weld_specs"])
        except:
            self._config["active_weld_spec"] = 0
            config.save_delayed()

    def settings_widget(self) -> QtWidgets.QWidget:
        def _apply_changes() -> None:
            self._config["prefix"] = le_prefix.text()
            self._config["do_create_in_active_document"] = cb_use_active_model.isChecked()
            self._config["section_edges_count"] = sb_section_edges_count.value()
            config.save_delayed()

        def _apply_list_changes() -> None:
            self._config["weld_specs"].clear()
            for item in weld_specs_list.iterate_items():
                name: str = item.data(QtCore.Qt.ItemDataRole.DisplayRole)
                diameter: float = item.data(self.DATAROLE_DIAMETER)
                layer: int = item.data(self.DATAROLE_LAYER)
                self._config["weld_specs"].append([name, diameter, layer])

            config.save_delayed()

        def _set_item_data(item: QtGui.QStandardItem, name: str, diam: float, layer: int) -> None:
            item.setData(name, QtCore.Qt.ItemDataRole.DisplayRole)
            item.setData(diam, self.DATAROLE_DIAMETER)
            item.setData(layer, self.DATAROLE_LAYER)

        def _create_new_weld_spec() -> QtGui.QStandardItem:
            item = QtGui.QStandardItem()
            _set_item_data(item, "◺5", 10.0, -1)
            return item

        def _weld_spec_data_changed() -> None:
            diam, layer = wsip.get_data()
            item = weld_specs_list.get_one_selected_item()
            if not item is None:
                name = item.data(QtCore.Qt.ItemDataRole.DisplayRole)
                _set_item_data(item, name, diam, layer)
                _apply_list_changes()

        def _selection_changed() -> None:
            item = weld_specs_list.get_one_selected_item()
            if not item is None:
                wsip.setEnabled(True)
                diam = item.data(self.DATAROLE_DIAMETER)
                layer = item.data(self.DATAROLE_LAYER)
                wsip.set_data(diam, layer)
            else:
                wsip.clear()
                wsip.setEnabled(False)

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        cb_use_active_model = QtWidgets.QCheckBox("Создавать построения в активной модели, а не во вспомогательной")
        cb_use_active_model.setChecked(self._config["do_create_in_active_document"])
        cb_use_active_model.stateChanged.connect(_apply_changes)

        sb_section_edges_count = QtWidgets.QSpinBox()
        sb_section_edges_count.setRange(0, 1000)
        sb_section_edges_count.setValue(self._config["section_edges_count"])
        sb_section_edges_count.valueChanged.connect(_apply_changes)

        le_prefix = QtWidgets.QLineEdit(self._config["prefix"])
        le_prefix.setPlaceholderText(RMWELD)
        le_prefix.textChanged.connect(_apply_changes)

        weld_specs_list = gui_widgets.StringListSelector(_create_new_weld_spec)
        for m in self._config["weld_specs"]:
            name, diam, layer = m
            item = QtGui.QStandardItem()
            _set_item_data(item, name, diam, layer)
            weld_specs_list.add_new_item(item)

        wsip = WeldSpecInputWidget()

        l.addWidget(cb_use_active_model, 0, 0, 1, 2)
        l.addWidget(QtWidgets.QLabel("Префикс для наименований построений и тел:"), 1, 0, 1, 1)
        l.addWidget(le_prefix, 1, 1, 1, 2)

        l.addWidget(QtWidgets.QLabel("Количество сторон многоугольника в сечении шва:"), 2, 0, 1, 1)
        l.addWidget(sb_section_edges_count, 2, 1, 1, 1)
        l.addWidget(gui_widgets.ToolTipWidget(
            "При значении '0' будет использоваться окружность\n"
            "в качестве сечения валика шва.\n\n"
            "Рекомендуется использовать 8-гранники\n"
            "для более корректного проецирования в чертежи."
            ), 2, 2, 1, 1)

        l.addWidget(weld_specs_list, 3, 0, 1, 3)
        l.addWidget(wsip, 4, 0, 1, 3)

        wsip.data_edited.connect(_weld_spec_data_changed)
        weld_specs_list.selection_changed.connect(_selection_changed)
        weld_specs_list.list_changed.connect(lambda: self.toolbar_update_requested.emit(False))
        weld_specs_list.list_changed.connect(lambda: _apply_list_changes())

        weld_specs_list.clear_selection()

        return w

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        def _select_active_weld_spec() -> None:
            i = cmbx_weld_specs.currentIndex()
            if i >= len(self._config["weld_specs"]):
                self.request_settings()
                if i > 0:
                    cmbx_weld_specs.setCurrentIndex(0)
            else:
                self._config["active_weld_spec"] = i
                config.save_delayed()

        cmbx_weld_specs = QtWidgets.QComboBox()

        for t in self._config["weld_specs"]:
            name, diam, layer = t
            cmbx_weld_specs.addItem(name)
        cmbx_weld_specs.addItem(QtGui.QIcon(get_resource_path("img/settings.svg")), "Настроить...")
        cmbx_weld_specs.setIconSize(QtCore.QSize(16, 16))

        if self._config["active_weld_spec"] < cmbx_weld_specs.count():
            cmbx_weld_specs.setCurrentIndex(self._config["active_weld_spec"])
        cmbx_weld_specs.setToolTip("Выбор параметров сварного шва")
        cmbx_weld_specs.currentIndexChanged.connect(_select_active_weld_spec)

        btn_create_weld = QtWidgets.QToolButton()
        btn_create_weld.setIcon(QtGui.QIcon(get_resource_path("img/macros/weld.svg")))
        btn_create_weld.clicked.connect(lambda: self.execute(self._create_welds))
        btn_create_weld.setToolTip("Создать сварные швы\n(ломаные линии и твердые тела)\nпо выбранным объектам модели")

        btn_create_lines = QtWidgets.QToolButton()
        btn_create_lines.setIcon(QtGui.QIcon(get_resource_path("img/macros/weld_lines.svg")))
        btn_create_lines.clicked.connect(lambda: self.execute(self._create_welds_lines))
        btn_create_lines.setToolTip("Создать только ломаные линии сварных швов\nпо выбранным объектам модели")

        btn_create_bodies = QtWidgets.QToolButton()
        btn_create_bodies.setIcon(QtGui.QIcon(get_resource_path("img/macros/weld_bodies.svg")))
        btn_create_bodies.clicked.connect(lambda: self.execute(self._create_welds_bodies))
        btn_create_bodies.setToolTip("Создать твёрдые тела сварных швов\nпо ломаным линиям без тел")

        return {
            "селектор выбора параметров сварного шва": cmbx_weld_specs,
            "кнопка создания сварных швов": btn_create_weld,
            "кнопка создания ломаных линий швов": btn_create_lines,
            "кнопка создания твердых тел швов": btn_create_bodies,
        }

    def _check_for_weldpart(self) -> bool:
        if self._config["do_create_in_active_document"]:
            self._welddoc_path = ""
        else:
            if self._welddoc_path == "":
                self._change_welddoc_path()
            if self._welddoc_path == "":
                self.show_warning(
                    "<p>Не указан путь к модели сварных швов.<br>Укажите путь и запустите команду заново.</p>"
                    "<p>Или создавайте сварные швы в текущей модели с использованием опции \"Создавать построения в активной модели, а не во вспомогательной\".</p>"
                )
                self.request_settings()
                return False
        return True

    def _create_welds(self) -> None:
        if not self._check_for_weldpart(): return
        wls = self._get_active_spec()
        create_welds(self._welddoc_path, wls, False, self._config["prefix"])

    def _create_welds_lines(self) -> None:
        if not self._check_for_weldpart(): return
        wls = self._get_active_spec()
        create_welds(self._welddoc_path, wls, True, self._config["prefix"])

    def _create_welds_bodies(self) -> None:
        if not self._check_for_weldpart(): return
        wls = self._get_active_spec()
        find_and_create_weld_bodies(self._welddoc_path, wls, True, self._config["prefix"])

    def _change_welddoc_path(self) -> None:
        try:
            opened_document_path = remember_opened_document()
        except:
            opened_document_path = ""

        path, filter_ = QtWidgets.QFileDialog.getOpenFileName(
            self._parent_widget,
            "Указать путь к модели сварных швов",
            os.path.dirname(opened_document_path),
            f"{gui_widgets.EXT_ASSEMBLY};;{gui_widgets.EXT_PART};;{gui_widgets.EXT_ALL}",
            gui_widgets.EXT_ASSEMBLY,
        )
        self._welddoc_path = path

    def _get_active_spec(self) -> WeldLineSettings:
        if len(self._config["weld_specs"]) == 0:
            self.request_settings()
            raise Exception("Нет ни одного шаблона сварных швов")

        if not (0 <= self._config["active_weld_spec"] < len(self._config["weld_specs"])):
            raise Exception(f"Некорректный индекс выбранного шаблона сварного шва: {self._config["active_weld_spec"]}")

        name, diameter, layer = self._config["weld_specs"][self._config["active_weld_spec"]]
        wls = WeldLineSettings(diameter, layer, self._config["section_edges_count"])
        return wls


if __name__ == "__main__":

    wls = WeldLineSettings()
    wls.layer = -1

    weldpart_path = ""


    action = 0b11

    if action & 0b01:
        create_welds(weldpart_path, wls, True, RMWELD)

    if action & 0b10:
        find_and_create_weld_bodies(weldpart_path, wls, True, RMWELD)



