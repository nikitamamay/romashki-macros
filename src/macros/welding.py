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
сварка: ребра; грани; ломаные линии; эскизы целиком; линии эскизов; набор
точек и вершин линии сварного шва.
Затем выполняется команда макроса. В модели для сварных швов создаются
*неассоциативные* ломаные линии по выбранным ранее ребрам, создается эскиз
с окружностью и выполняется кинематическая операция (операция по траектории)
для создания твердого тела сварного шва.


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


Point: typing.TypeAlias = tuple[float, float, float]
Line: typing.TypeAlias = list[Point]
TransformFunction: typing.TypeAlias = typing.Callable[[Point], Point]


class WeldLineSettings:
    """
    Класс настроек алгоритма создания ломаных линий сварных швов.
    """
    def __init__(self, diameter: float = 10.0, max_angle_deviation: float = 20.0):
        self.diameter: float = diameter
        """диаметр валика твердого тела шва"""

        self.step_default: float = diameter * 1.6
        """длина шага вдоль кривой по-умолчанию"""

        self.step_min: float = diameter / 2
        """минимальная длина шага вдоль кривой"""

        self.max_angle_deviation: float = max_angle_deviation  # в градусах
        """максимальный угол сектора при аппроксимации окружностей"""


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
        if curve.IsArc() or curve.IsCircle() or curve.IsEllipse():
            if curve.IsEllipse():
                r = curve.GetCurveParam().minorRadius
            else:
                r = curve.GetCurveParam().radius
            step_max = 2 * r * math.sin(math.radians(wls.max_angle_deviation))
            # step_recommended = min(step_max, step_default)
            step_recommended = max(step_max, wls.step_min)
        else:
            step_recommended = wls.step_default
        segments_count = max(1, math.ceil(curve_length / step_recommended))
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

        # грань (создание сварных швов по всем ребрам-границам)
        elif el.type == LDefin3D.o3d_face:
            lines: list[Line] = []
            face_def: KAPI5.ksFaceDefinition = el.GetDefinition()
            ec: KAPI5.ksEdgeCollection = face_def.EdgeCollection()
            for i in range(ec.GetCount()):
                edge: KAPI5.ksEdgeDefinition = ec.GetByIndex(i)
                curve: KAPI5.ksCurve3D = edge.GetCurve3D()

                line = get_line_of_curve(curve, transform_function, wls)
                lines.append(line)
            return lines

        # эскиз (создание сварных швов по всем линиям эскиза)
        elif el.type == LDefin3D.o3d_sketch:
            lines: list[Line] = []
            parent_part = el.GetParent()

            sketch7: KAPI7.ISketch = transfer_to_7(el, LDefin3D.o3d_sketch)
            f: KAPI7.IFeature7 = KAPI7.IFeature7(sketch7)
            edges: list[KAPI7.IEdge] = ensure_list(f.ModelObjects(LDefin3D.o3d_edge))
            for edge in edges:
                curve = transfer_to_K5(edge.MathCurve)
                line = get_line_of_curve(curve, transform_function, wls)
                lines.append(line)

            return lines

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


def create_weld(part: KAPI7.IPart7, line: Line, diameter: float = 10) -> None:
    """
    Создает твёрдое тело сварного шва в модели `part`.
    """
    kompas5, kompas7 = get_kompas_objects()

    # создание ломаной линии

    agc = KAPI7.IAuxiliaryGeomContainer(part)
    pl: KAPI7.IPolyLine = agc.PolyLines.Add()

    # проверка линии шва на замкнутость
    if are_points_same(line[0], line[-1], diameter / 10):
        pl.Closed = True
        line = line[:-1]

    for x, y, z in line:
        cvp: KAPI7.ICurveVertexParam = pl.AddVertex(-1)
        cvp.SetParamVertex(x, y, z, 0)
        cvp.Update()

    pl.Hidden = True
    pl.Update()

    # создание плоскости для эскиза
    # (через первую точку ломаной перпендикулярно первому сегменту ломаной)

    pl5: KAPI5.ksPolyLineDefinition = kompas5.TransferInterface(pl, 1, 0)

    part5: KAPI5.ksPart = kompas5.TransferInterface(part, 1, 0)
    plane5_entity: KAPI5.ksEntity = part5.NewEntity(LDefin3D.o3d_planePerpendicular)
    plane5: KAPI5.ksPlanePerpendicularDefinition = plane5_entity.GetDefinition()
    edge5: KAPI5.ksEdgeDefinition = pl5.EdgeCollection().First()
    vertex5: KAPI5.ksEntity = pl5.GetPointParams(0).GetVertex()
    plane5.SetEdge(edge5)
    plane5.SetPoint(vertex5)
    plane5_entity.hidden = True
    plane5_entity.Update()
    plane: KAPI7.IPlane3DPerpendicularByEdge = kompas5.TransferInterface(plane5_entity, 2, 0)

    # создание эскиза с кругом --- сечением шва

    mc = KAPI7.IModelContainer(part)
    sketch: KAPI7.ISketch = mc.Sketchs.Add()
    sketch.Plane = plane
    sketch.Update()

    doc2d: KAPI7.IFragmentDocument = sketch.BeginEdit()
    view: KAPI7.IView = doc2d.ViewsAndLayersManager.Views.View(0)
    dc: KAPI7.IDrawingContainer = KAPI7.IDrawingContainer(view)
    circle: KAPI7.ICircle = dc.Circles.Add()
    circle.Radius = diameter / 2
    circle.Update()

    sketch5 = kompas5.TransferInterface(sketch, 1, 0)
    ref = sketch5.AddProjectionOf(vertex5)
    dg: KAPI7.IDrawingGroup = kompas5.TransferReference(ref, 0)
    point: KAPI7.IPoint = ensure_list(dg.Objects())[0]

    do1 = KAPI7.IDrawingObject1(circle)
    constraint: KAPI7.IParametriticConstraint = do1.NewConstraint()  # ограничение, в общем-то, необязательно
    constraint.ConstraintType = 11  # ksCMergePoints
    constraint.Index = 0
    constraint.Partner = point
    constraint.PartnerIndex = 0
    constraint.Create()

    sketch.EndEdit()

    # создание кинематической операции (вытягивание по траектории)

    evolution_e: KAPI5.ksEntity = part5.NewEntity(LDefin3D.o3d_bossEvolution)
    base_evolution: KAPI5.ksBossEvolutionDefinition = evolution_e.GetDefinition()
    base_evolution.SetSketch(sketch5)
    base_evolution.ChooseBodies().ChooseBodiesType = 0  # новое тело
    ec: KAPI5.ksEntityCollection = base_evolution.PathPartArray()
    ec.Add(pl5)
    evolution_e.Update()


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


def merge_lines(lines: list[Line], max_deviation: float = 2) -> list[Line]:
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


def create_welds(welds_part_path: str, wls: WeldLineSettings) -> None:
    """
    Анализирует выбранные в текущей модели объекты. Создает твердотельные модели
    сварных швов в модели по пути `welds_part_path`.
    """

    welds_part_path = os.path.normpath(welds_part_path)  # это важно. Если передать путь с прямыми слэшами "/", Компас молча что-то делает, но по факту ничего не происходит
    opened = remember_opened_document()

    # анализ выбранных объектов текущей модели

    doc5, toppart5 = open_part_K5()
    selected = get_selected_K5(doc5)

    if len(selected) == 0:
        raise Exception("Не выбраны объекты для формирования сварных швов.")

    lines: list[Line] = []
    line_of_vertexes: Line = []

    for el in selected:
        if isinstance(el, KAPI5.ksEntity):
            tr_func = get_transform_function(toppart5, el.GetParent())

            if el.type in (LDefin3D.o3d_vertex, LDefin3D.o3d_point3D):
                p = get_point_of_element(el, tr_func)
                if not p is None:
                    line_of_vertexes.append(p)

            else:
                element_lines = get_lines_of_element(el, tr_func, wls)
                lines.extend(element_lines)
        else:
            print("selected is not a ksEntity", el)

    # обработка отдельно выбранных точек
    line_of_vertexes = construct_line(line_of_vertexes)
    lines.append(line_of_vertexes)

    # удаление пустых линий из списка
    i = 0
    while i < len(lines):
        if len(lines[i]) <= 1:
            lines.pop(i)
        else:
            i += 1

    # склеивание стыкующихся линий в одну большую
    merge_lines(lines, wls.diameter / 5)

    print(f"Всего непрерывных сварных швов: {len(lines)}")

    if len(lines) == 0:
        raise Exception("Не сформированы линии сварных швов.")

    # создание твердых тел сварных швов

    welddoc, weldpart = open_part(welds_part_path, True)

    s_errors: str = ""

    for line in lines:
        try:
            create_weld(weldpart, line, wls.diameter)
        except Exception as e:
            s_errors += traceback.format_exc() + "\n"


    welddoc.Save()

    # возврат к ранее открытому документу

    restore_opened_document(opened)

    kompas5, kompas7 = get_kompas_objects()
    kompas5.ksRefreshActiveWindow()

    if s_errors != "":
        raise Exception(s_errors)



class WeldingMacros(Macros):
    def __init__(self) -> None:
        super().__init__(
            "welding",
            "Сварные швы"
        )

        self._welddoc_path = ""


    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        btn_create_weld = gui_widgets.ButtonWithList(QtGui.QIcon(get_resource_path("img/macros/weld.svg")), "")
        btn_create_weld.clicked.connect(self._create_welds)
        btn_create_weld.setToolTip("Создать тела сварных швов\nпо выбранным объектам модели")

        # for i, m in enumerate(self._config["rvd_sizes"]):
        #     D, d = m
        #     name = f"⌀{d} / ⌀{D}"
        #     btn_create_weld._menu.addAction(name, (lambda i: lambda: _apply_size(i))(i))

        btn_create_weld._menu.addSeparator()

        btn_create_weld._menu.addAction(
            os.path.basename(self._welddoc_path) if self._welddoc_path != "" else "<не указана модель сварных швов>"
        )

        btn_create_weld._menu.addSeparator()

        btn_create_weld._menu.addAction(
            QtGui.QIcon(get_resource_path("img/macros/doc_model.svg")),
            "Сменить модель сварных швов...",
            self._change_welddoc_path,
        )

        btn_create_weld._menu.addAction(
            QtGui.QIcon(get_resource_path("img/settings.svg")),
            "Настроить...",
            self.request_settings,
        )

        return {
            "кнопка создания сварных швов": btn_create_weld,
        }

    def _create_welds(self) -> None:
        if self._welddoc_path == "":
            self._change_welddoc_path()
        if self._welddoc_path == "":
            self.show_warning(
                "<p>Не указан путь к модели сварных швов.</p>"
                "<p>Укажите путь и запустите команду заново.</p>"
            )
            return

        self.execute(
            lambda: create_welds(self._welddoc_path, WeldLineSettings(10.0))  # FIXME диаметр шва сделать из config
        )

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
        self.toolbar_update_requested.emit(True)


if __name__ == "__main__":
    path = r"D:\modeling\KompasExperiments\обозначения-сварки\010 Рама сварная\(сварные швы).a3d"
    wls = WeldLineSettings()
    create_welds(path, wls)

