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

Есть функция удаления ранее созданных сварных швов. Для этого нужно выделить
объект, принадлежащий сварному шву --- например, грань, ребро или вершину
твердого тела этого шва --- и выполнить команду. Удалится связанная с этим
построением ломаная линия и все её дочерние построения, включая плоскость эскиза,
эскиз и операция выдавливания по траектории.


Макрос реализован как прототип для проверки идеи автоматизированного создания
твердотельных обозначений сварных швов.

"""



from .lib_macros.core import *

from ..utils import math_utils
# from ..utils import math_utils_3d  # TODO перейти на это вместо моих собственных объявлений Point и функций

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
        return toppart5.TransformPoint(point[0], point[1], point[2], element_part)[1:]  # TODO отказаться от вызова Компас-API здесь; заменить на умножение на матрицу преобразования
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
        vd: KAPI5.ksVertexDefinition = vertex.GetDefinition()  # KAPI7.IVertex появился только в Компас18.1
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
        do_check_between_line_points: bool = False,
        max_deviation: float = 0.001,
        ) -> bool:
    """
    Проверяет, содержит ли линия `line` точку `point`.

    См. также `are_points_same()`, `create_welds()`.
    """
    if do_check_between_line_points:
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
    selected_entities: list[KAPI5.ksEntity] = get_selected_K5(doc5, (KAPI5.ksEntity,))

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
            create_weld_body(weldpart, pl7, wls, prefix)

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
        pl7: KAPI7.IPolyLine,
        wls: WeldLineSettings,
        prefix: str = RMWELD,
        ) -> None:
    """
    Создает твердое тело сварного шва по ломаной `polyline5` в модели `part`.
    """
    assert isinstance(part, KAPI7.IPart7)
    assert isinstance(pl7, KAPI7.IPolyLine)

    kompas5, kompas7 = get_kompas_objects()

    part5: KAPI5.ksPart = transfer_to_K5(part)
    polyline5: KAPI5.ksPolyLineDefinition = transfer_to_K5(pl7, LDefin3D.o3d_polyline)

    # создание плоскости для эскиза
    # (через первую точку ломаной перпендикулярно первому сегменту ломаной)

    ec: KAPI5.ksEdgeCollection = polyline5.EdgeCollection()
    if ec is None:
        # FIXME некоторые ломаные после transfer_to_K5 оказываются пустыми объектами;
        # не имеют имени ('' object has no attribute 'name')
        # и у них EdgeCollection() is None.
        # Причина этой ошибки не_выявлена и воспроизвести ошибку не_получается.
        # Возможно ранее, во время разработки, в функции create_weld_polyline()
        # созданная ломаная оказывалась как будто некорректной...
        raise Exception(f"Не удалось получить EdgeCollection у ломаной '{pl7.Name}'")

    plane5_entity: KAPI5.ksEntity = part5.NewEntity(LDefin3D.o3d_planePerpendicular)
    plane5: KAPI5.ksPlanePerpendicularDefinition = plane5_entity.GetDefinition()
    edge5: KAPI5.ksEdgeDefinition = ec.First()
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
        raise Exception(f"Не удалось создать плоскость по ломаной '{pl7.Name}'")
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
        raise Exception(f"Не удалось создать вытягивание по траектории по ломаной линии '{pl7.Name}' с эскизом '{sketch.Name}'")

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
        pl: KAPI7.IPolyLine = pls.PolyLine(i)
        if pl.Name.startswith(prefix):
            mo1 = KAPI7.IModelObject1(pl)
            children: list[KAPI7.IModelObject] = ensure_list(mo1.Childrens(1))  # 1 - все отношения (ksRelationTypeEnum)
            for mo in children:
                if mo.Name.startswith(prefix) and mo.Type == 11276:  # KompasAPIObjectTypeEnum.ksObjectEvolution - 11276 - элемент по траектории
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

    welddoc, weldpart = open_part(weldpart_path, True)
    polylines7 = find_weld_polylines_without_bodies(weldpart, prefix)

    print(f"Найдено {len(polylines7)} ломаных линий без твердотельных построений: {[pl.Name for pl in polylines7]}")

    errors = ""

    for pl7 in polylines7:
        try:
            create_weld_body(weldpart, pl7, wls, prefix)
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


def remove_welds(
        prefix: str = RMWELD,
        do_remove_in_weldpart_only: bool = True,
        weldpart_path: str = "",
        ) -> None:
    """
    Удаляет ломаные линии и твердотельные построения сварных швов по их
    элементам, которые выбрал пользователь.

    Для выбранных объектов (вершин, ребер, граней твердых тел; самих твердых
    тел; ребер и вершин ломаных; самих ломаных) в текущей модели определяет,
    зависят ли построения этих объектов от ломаных линий с префиксом `prefix`
    в названии.

    Среди найденных ломаных линий  удаляются только те из них,
    которые принадлежат модели в файле `weldpart_path`
    при условии `do_remove_in_weldpart_only == True`.
    В противном случае ломаные удаляются из любых моделей, которым они принадлежат.
    Актуально для случаев, когда в текущей модели уже есть подсборки со своими
    сварными швами, которые удалять нельзя.

    При удалении ломаной линии соответственно удаляются все зависимые от неё
    построения, включая плоскость эскиза, эскиз и операция выдавливания по
    траектории.
    """
    doc, toppart = open_part()
    selected_objs: list = get_selected(doc)

    if weldpart_path == "":
        weldpart_path = toppart.FileName

    if not do_remove_in_weldpart_only:
        _is_part_accepted = lambda feature_part: True
    else:
        _is_part_accepted = lambda feature_part: feature_part.FileName == weldpart_path

    features_to_delete: dict[int, tuple[KAPI7.IFeature7, KAPI7.IPart7]] = {}
    """ { (int) KAPI7.IPolyLine.Reference : (KAPI7.IFeature7) KAPI7.IPolyLine.Owner } """

    errors: str = ""

    # получение ломаных линий, которые связаны с построениями объектов, которые выделены пользователем

    for obj in selected_objs:
        def _f():
            # FIXME проверить, что возвращает при выборе ребер в Компас16 - ведь KAPI7.IEdge появился только в Компас18

            print(f"Выбранный объект '{obj.Name}' {obj}:")

            # если выбрана сама ломаная в дереве построения модели
            if isinstance(obj, KAPI7.IPolyLine):
                pl: KAPI7.IPolyLine = obj
                feature: KAPI7.IFeature7 = pl.Owner
                feature_part: KAPI7.IPart7 = pl.Part
                if pl.Name.startswith(prefix):
                    print(f"\tявляется ломаной")
                    if not _is_part_accepted(feature_part): return print("\tне используется, т.к. за пределами weldpart")
                    features_to_delete[obj.Reference] = (feature, feature_part)
                return

            # если выбран KAPI7.IModelObject
            if hasattr(obj, "Part") and hasattr(obj, "Owner") and hasattr(obj, "Reference"):
                feature: KAPI7.IFeature7 = obj.Owner
                feature_part: KAPI7.IPart7 = obj.Part

            # если выбрано тело
            elif isinstance(obj, KAPI7.IBody7):
                body_feature: KAPI7.IFeature7 = KAPI7.IFeature7(obj)
                body_creating_obj = ensure_list(body_feature.SubFeatures(0, True, True))[0]
                feature: KAPI7.IFeature7 = KAPI7.IFeature7(body_creating_obj)
                feature_part: KAPI7.IPart7 = KAPI7.IPart7(feature.OwnerFeature)
                print(f"\tявляется телом от операции '{feature.Name}'")

            # если выбрано непонятно что
            else:
                raise Exception(f"\tне поддерживается: {obj} type={type(obj)}")

            if not _is_part_accepted(feature_part): return print("\tне используется, т.к. за пределами weldpart")

            # получение ломаных линий модели, которой принадлежит выбранный объект

            agc = KAPI7.IAuxiliaryGeomContainer(feature_part)
            pls: KAPI7.IPolyLines = agc.PolyLines

            part_polylines_features = {}
            for i in range(pls.Count):
                pl: KAPI7.IPolyLine = pls.Item(i)
                if pl.Name.startswith(prefix):
                    # part_polylines_features[pl.Reference] = [pl, pl.Owner]
                    part_polylines_features[pl.Reference] = pl

            # если feature выбранного объекта - это ломаная линия
            # (т.е. если выбраны ребро или точка самой ломаной)

            for pl in part_polylines_features.values():
                pl_feature: KAPI7.IFeature7 = pl.Owner
                if feature == pl_feature:
                    features_to_delete[pl.Reference] = (pl_feature, feature_part)
                    print(f"\tявляется элементом ломаной '{pl_feature.Name}'")
                    return

            # далее идет поиск по родителям feature выбранного obj.
            # (т.е. если что-то из родителей этой feature - ломаная линия)
            # (т.е. если выбраны ребро, грань или точка элемента выдавливания по траектории или др.)

            mo1 = KAPI7.IModelObject1(feature)
            parents: list[KAPI7.IModelObject] = ensure_list(mo1.Parents(1))  # 1 - все отношения (ksRelationTypeEnum)

            for parent_obj in parents:
                if parent_obj.Name.startswith(prefix) and parent_obj.Type == 11048:  # KompasAPIObjectTypeEnum.ksObjectPolyLine - 11048 - 3D ломаная
                    parent_feature: KAPI7.IFeature7 = parent_obj.Owner
                    features_to_delete[parent_obj.Reference] = (parent_feature, parent_obj.Part)
                    print(f"\tявляется дочерним для ломаной '{parent_feature.Name}'")
                    return

            # не_связан с построениями ломаных
            print(f"\tне_связан с построениями сварых швов '{prefix}'")

        try:
            _f()
        except Exception as e:
            s_e = traceback.format_exc()
            print(s_e)
            errors += s_e + "\n\n"

    print(f"\nК удалению {len(features_to_delete)} ломаных линий", end="")

    if len(features_to_delete) == 0:
        print(f".")
        return

    # для ускорения BeginEdit()/EndEdit(): группировка ломаных по моделям, к которым они принадлжат

    parts_and_features_to_delete: list[tuple[KAPI7.IPart7, list[KAPI7.IFeature7]]] = []

    for pl_feature, pl_feature_part in features_to_delete.values():
        for grouped_part, grouped_features in parts_and_features_to_delete:
            if pl_feature_part.FileName == grouped_part.FileName:
                grouped_features.append(pl_feature)
                break
        else:
            parts_and_features_to_delete.append((pl_feature_part, [pl_feature]))

    print(f" в {len(parts_and_features_to_delete)} моделях.\n")

    # удаление ломаных в их моделях

    docs: KAPI7.IDocuments = get_app7().Documents

    for grouped_part, grouped_features in parts_and_features_to_delete:
        print(f"В компоненте '{grouped_part.Name}' ('{grouped_part.FileName}'):")
        if grouped_part != toppart:
            odp: KAPI7.IOpenDocumentParam = docs.GetOpenDocumentParam()
            grouped_part.BeginEdit(odp)
            print(f"\tредактирование на месте начато")

        for pl_feature in grouped_features:
            pl_feature_name = pl_feature.Name
            is_ok = pl_feature.Delete()
            if is_ok:
                print(f"\tудалена ломаная '{pl_feature_name}' и её дочерние построения.")
            else:
                print(f"\tне удалось удалить ломаную '{pl_feature_name}'")

        if grouped_part != toppart:
            grouped_part.EndEdit(False)
            print(f"\tредактирование на месте окончено")

    print(f"Удаление сварных швов окончено.")

    if errors != "":
        raise Exception(errors)




if __name__ == "__main__":

    wls = WeldLineSettings()
    wls.layer = -1

    weldpart_path = ""


    # action = 0b11

    # if action & 0b01:
    #     create_welds(weldpart_path, wls, True, RMWELD)

    # if action & 0b10:
    #     find_and_create_weld_bodies(weldpart_path, wls, True, RMWELD)

    remove_welds(do_remove_in_weldpart_only=False)


