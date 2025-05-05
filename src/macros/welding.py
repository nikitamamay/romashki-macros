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


Сценарий работы следующий. Помимо основной сборки со сварными деталями,
задействована еще одна модель непосредственно для твердых тел сварных швов.
В основной сборке пользователь выбирает ребра, по которым происходит сварка.
Затем выполняется команда макроса. В модели для сварных швов создаются
*неассоциативные* ломаные линии по выбранным ранее ребрам, создается эскиз
с окружностью и выполняется кинематическая операция (операция по траектории)
для создания твердого тела сварного шва.
Модель со сварными швами должна быть вставлена в основную сборку для их отображения.


Макрос реализован как прототип для проверки идеи автоматизированного создания
твердотельных обозначений сварных швов.
На данный момент является незаконченной разработкой.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path

from src import math_utils
import math



def get_points_of_element(el, toppart5: KAPI5.ksPart, step_default: float = 16, max_angle_deviation: float = 20, step_min: float = 5) -> list[list[tuple[float, float, float]]]:
    lines: list[list[tuple[float, float, float]]] = []

    if isinstance(el, KAPI5.ksEntity):
        if el.type == LDefin3D.o3d_edge:
            line: list[tuple[float, float, float]] = []
            edge: KAPI5.ksEdgeDefinition = el.GetDefinition()
            curve: KAPI5.ksCurve3D = edge.GetCurve3D()
            curve_length = curve.GetLength(1)  # 1 = в миллиметрах

            minT = curve.GetParamMin()
            maxT = curve.GetParamMax()
            def _get_T_from_length(length: float) -> float:
                return (maxT - minT) / curve_length * length + minT
            def _get_point(curve_T: float) -> tuple[float, float, float]:
                x, y, z = curve.GetPoint(curve_T)[1:]
                return toppart5.TransformPoint(x, y, z, el.GetParent())[1:]

            if curve.IsLineSeg():  # прямая
                start = _get_point(_get_T_from_length(0))
                end = _get_point(_get_T_from_length(curve_length))
                line.append(start)
                line.append(end)

            else:  # кривая
                if curve.IsArc() or curve.IsCircle() or curve.IsEllipse():
                    if curve.IsEllipse():
                        r = curve.GetCurveParam().minorRadius
                    else:
                        r = curve.GetCurveParam().radius
                    step_max = 2 * r * math.sin(math.radians(max_angle_deviation))
                    # step_recommended = min(step_max, step_default)
                    step_recommended = max(step_max, step_min)
                else:
                    step_recommended = step_default
                segments_count = max(1, math.ceil(curve_length / step_recommended))
                step_real = curve_length / segments_count

                line.append(_get_point(_get_T_from_length(0)))

                for i in range(1, segments_count):
                    line.append(_get_point(_get_T_from_length(step_real * i)))

                line.append(_get_point(_get_T_from_length(curve_length)))
            lines.append(line)

        # elif el.type == LDefin3D.o3d_sketch:
        #     sketch: KAPI5.ksSketchDefinition = el.GetDefinition()
        #     sketch7: KAPI7.ISketch = transfer_to_7(sketch, LDefin3D.o3d_sketch)
        #     sketch7.
        #     for e in []:
        #         lines.extend(get_points_of_element(
        #             e, toppart5, step_default, max_angle_deviation, step_min,
        #         ))

        else:
            print("not supported ksEntity.type =", el.type, el)
    else:
        print("not a ksEntity!", el)
    return lines


def create_weld(part: KAPI7.IPart7, points: list[tuple[float, float, float]], diameter: float = 10) -> None:
    kompas5, kompas7 = get_kompas_objects()

    agc = KAPI7.IAuxiliaryGeomContainer(part)

    pl: KAPI7.IPolyLine = agc.PolyLines.Add()

    if are_points_same(points[0], points[-1], 0.1):
        pl.Closed = True
        points = points[:-1]

    for x, y, z in points:
        cvp: KAPI7.ICurveVertexParam = pl.AddVertex(-1)
        cvp.SetParamVertex(x, y, z, 0)
        cvp.Update()

    pl.Hidden = True
    pl.Update()

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
    constraint: KAPI7.IParametriticConstraint = do1.NewConstraint()
    constraint.ConstraintType = 11  # ksCMergePoints
    constraint.Index = 0
    constraint.Partner = point
    constraint.PartnerIndex = 0
    constraint.Create()

    sketch.EndEdit()


    evolution_e: KAPI5.ksEntity = part5.NewEntity(LDefin3D.o3d_bossEvolution)
    base_evolution: KAPI5.ksBossEvolutionDefinition = evolution_e.GetDefinition()
    base_evolution.SetSketch(sketch5)
    base_evolution.ChooseBodies().ChooseBodiesType = 0  # новое тело
    ec: KAPI5.ksEntityCollection = base_evolution.PathPartArray()
    ec.Add(pl5)
    evolution_e.Update()


def are_points_same(dotA: tuple[float, float, float], dotB: tuple[float, float, float], max_deviation: float = 2) -> bool:
    xA, yA, zA = dotA
    xB, yB, zB = dotB
    return abs(xA - xB) < max_deviation and abs(yA - yB) < max_deviation and abs(zA - zB) < max_deviation


def connect_points(lines: list[list[tuple[float, float, float]]], max_deviation: float = 2) -> list[list[tuple[float, float, float]]]:
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


def create_welds(weldfilepath: str, diameter: float) -> None:
    weldfilepath = os.path.normpath(weldfilepath)  # это важно. Если передать путь с прямыми слэшами "/", Компас молча что-то делает, но по факту ничего не происходит
    opened = remember_opened_document()

    doc5, toppart5 = open_part_K5()
    selected = get_selected_K5(doc5)

    if len(selected) == 0:
        raise Exception("Не выбраны ребра для формирования сварных швов.")

    points_arrays: list[list] = []

    for el in selected:
        points = get_points_of_element(el, toppart5, step_default=diameter*1.6, step_min=diameter)
        if len(points) >= 2:
            points_arrays.append(points)

    connect_points(points_arrays, diameter / 5)

    if len(points_arrays) == 0:
        raise Exception("Не сформированы линии сварных швов.")

    print(f"Всего непрерывных сварных швов: {len(points_arrays)}")

    welddoc, weldpart = open_part(weldfilepath, True)

    for points in points_arrays:
        create_weld(weldpart, points, diameter)

    welddoc.Save()
    restore_opened_document(opened)

    kompas5, kompas7 = get_kompas_objects()
    kompas5.ksRefreshActiveWindow()



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
        btn_create_weld.setToolTip("Создать тела сварных швов\nпо выбранным ребрам")

        # for i, m in enumerate(self._config["rvd_sizes"]):
        #     D, d = m
        #     name = f"⌀{d} / ⌀{D}"
        #     btn_create_weld.menu().addAction(name, (lambda i: lambda: _apply_size(i))(i))

        btn_create_weld.menu().addSeparator()

        btn_create_weld.menu().addAction(
            os.path.basename(self._welddoc_path) if self._welddoc_path != "" else "<не указана модель сварных швов>"
        )

        btn_create_weld.menu().addSeparator()

        btn_create_weld.menu().addAction(
            QtGui.QIcon(get_resource_path("img/macros/doc_model.svg")),
            "Сменить модель сварных швов...",
            self._change_welddoc_path,
        )

        btn_create_weld.menu().addAction(
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
            lambda: create_welds(self._welddoc_path, 10)  # FIXME диаметр шва сделать из config
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
    path = r"D:\Projects\kompas1\010 Рама сварная\work_Сварные швы рамы.a3d"
    diam = 10
    create_welds(path, diam)

