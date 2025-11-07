"""
Один из самых продвинутых и наиболее полезных макросов в этой коллекции.

Макрос предоставляет функционал по автоматизированному созданию DXF-разверток
для листовых деталей.

Принцип работы макроса описывается следующим образом. В 3D-модели пользователем
создается ориентация (вид, проекция), ортогональная развертке детали, для указания
направления проецирования.
Затем автоматически создается временный чертеж с ассоциативным видом по заранее
созданной ориентации модели, чтобы получить контуры детали.
Контуры переносятся во фрагмент.
Далее дается возможность пользователю редактировать фрагмент, как правило, в целях
удаления каких-то линии, например, резьбовых отверстий.
Затем выполняется сохранение в формате DXF или в формате Компас-Фрагмент с указанием
в имени файла толщины, обозначения и наименования детали.

Можно создать DXF-контур из вида чертежа. Для этого нужно выделить вид на чертеже
и запустить команду. Линии вида перенесутся во фрагмент, который так же можно
отредактировать и сохранить.

У этого макроса поддерживается автоматическое определение толщины детали (для указания
в имени DXF-файла) по свойствам листового тела, если оно создано в 3D-модели, либо
по наименьшему габариту модели, в которой не создавались листовые тела (например,
пластина создана операцией выдавливания).


Так как этот макрос реализует функцию для создания ориентации (проекции) в 3D-модели,
здесь есть функция создания ориентации в модели под кодовым названием "Главный вид"
для последующего создания на чертеже ассоциативного вида по этой ориентации.
Это актуально для старых версий Компаса, в которых нет возможности изменить ориентацию
стандартных видов для дальнейшего проецирования в чертеж, а нужно создавать новый вид
(ориентацию).

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src import math_utils

from src.resources import get_resource_path

import src.macros.stamp as stamp

import traceback


FASTDXF_PROJECTION_NAME = "FAST_DXF_PROJECTION"
FASTDXF_DWG_VIEW_NAME = "DXF"
MAIN_PROJECTION_NAME = "Главный вид"


_remembered_path: str = ""

def remember_path(s: str) -> None:
    global _remembered_path
    _remembered_path = s

def get_path() -> str:
    global _remembered_path
    return _remembered_path



def get_dimensions(part: KAPI7.IPart7) -> tuple[float, float, float]:
    bodies: list[KAPI7.IBody7] = ensure_list(KAPI7.IFeature7(part).ResultBodies)
    if len(bodies) == 0:
        return (0, 0, 0)

    _, x1, y1, z1, x2, y2, z2 = bodies[0].GetGabarit()

    for body in bodies[1:]:
        _, b_x1, b_y1, b_z1, b_x2, b_y2, b_z2 = body.GetGabarit()
        x1 = min(x1, b_x1)
        y1 = min(y1, b_y1)
        z1 = min(z1, b_z1)
        x2 = max(x2, b_x2)
        y2 = max(y2, b_y2)
        z2 = max(z2, b_z2)

    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1
    return (dx, dy, dz)


def get_gabarit5(part5: KAPI5.ksPart) -> tuple[float, float, float, float, float, float]:
    _, x1, y1, z1, x2, y2, z2 = part5.GetGabarit(True, False)
    return (x1, y1, z1, x2, y2, z2)


def get_part_geometry_thickness(part: KAPI7.IPart7) -> float:
    smc = KAPI7.ISheetMetalContainer(part)

    sheet_metal_objects: list[KAPI7.ISheetMetalBody | KAPI7.ISheetMetalPlate] = []

    smbs_list: list[KAPI7.ISheetMetalBodies] = [
        smc.SheetMetalBodies,  # операция "Листовое тело"
    ]

    try:
        smbs_list.extend([
            smc.SheetMetalRuledShells,  # операция "Обечайка" (с Компас v18.1)
            smc.SheetMetalLinearRuledShells,  # операция "Линейчатая обечайка" (с Компас v18.1)
        ])
    except:
        pass

    for sm_bodies_container in smbs_list:
        for i in range(sm_bodies_container.Count):
            sm_body: KAPI7.ISheetMetalBody = sm_bodies_container.SheetMetalBody(i)
            sheet_metal_objects.append(sm_body)

    try:
        sm_plates_container: KAPI7.ISheetMetalPlates = smc.SheetMetalPlates  # операция "Пластина" (с Компас v18.1)

        for i in range(sm_plates_container.Count):
            sm_plate: KAPI7.ISheetMetalPlate = sm_plates_container.SheetMetalBody(i)
            sheet_metal_objects.append(sm_plate)
    except:
        # print("Warning: не удается получить контейнер листовых пластин")
        pass

    sm_objs_count = len(sheet_metal_objects)
    print(f"Количество листовых тел в модели: {sm_objs_count}.", end=" ")

    thickness: float = 0.0
    if sm_objs_count > 0:
        print(f"Толщина берётся из свойств листовых тел.", end=" ")
        for sm_obj in sheet_metal_objects:
            thickness += sm_obj.Thickness
        thickness /= sm_objs_count
    else:
        print(f"Толщина рассчитывается исходя из габаритов модели.", end=" ")
        dx, dy, dz = get_dimensions(part)
        thickness = min(dx, dy, dz)
    print(f"Толщина: {thickness} мм.")
    return thickness



def _get_dxf_path(directory: str, thickness: float, marking: str, name: str) -> str:
    str_thickness = math_utils.round_tail_str(thickness)
    str_thickness = str_thickness.replace(".", ",")
    path = os.path.normpath(f"{directory}/S={str_thickness} {f'{marking} {name}'.strip()}.dxf")
    return path

def get_dxf_path_from_3d(part: KAPI7.IPart7) -> str:
    d = os.path.dirname(part.FileName)
    t = get_part_geometry_thickness(part)
    m = part.Marking
    n = part.Name
    return _get_dxf_path(d, t, m, n)


def get_dxf_path_from_2d(doc_dwg: KAPI7.IKompasDocument2D, view_dxf: KAPI7.IView) -> str:
    """
    Возвращает имя DXF-файла при создании DXF-фрагмента из чертежа:

    * если вид `view_dxf` ассоциативный (вид с модели), генерирует имя DXF-файла из свойств модели;
    * проверяет все виды чертежа, и если они ссылаются на одну и ту же модель, генерирует имя DXF-файла из свойств этой модели;
    * в противном случае генерирует имя DXF-файла из имени файла чертежа.
    """
    filepath: str = ""

    try:
        # если view_dxf - вид с модели (т.е. у него есть aview_dxf.SourceFileName)
        # то генерируется имя из свойств 3D-модели:

        print(0, view_dxf)
        aview_dxf = KAPI7.IAssociationView(view_dxf)
        filepath = aview_dxf.SourceFileName
        print(1, filepath)
        if not (filepath == "" or filepath is None):
            doc, part = open_part(filepath, is_hidden=True)
            return get_dxf_path_from_3d(part)

        # иначе - если view_dxf - неассоциативный вид - проверяются все виды в чертеже...

        vlm: KAPI7.IViewsAndLayersManager = doc_dwg.ViewsAndLayersManager
        views: KAPI7.IViews = vlm.Views

        for i in range(views.Count):
            view: KAPI7.IView = views.View(i)
            try:
                aview = KAPI7.IAssociationView(view)
                fp = aview.SourceFileName
                if fp == "":
                    continue
            except:
                continue

            if filepath == "":
                filepath = fp
            else:
                if filepath != fp:
                    raise  # ошибка: виды на чертеже ссылаются на разные модели

        if filepath == "":
            raise  # ошибка: на чертеже нет вообще ни одного вида с модели

        # если в чертеже есть виды с модели и они все ссылаются на одну модель
        # то генерируется имя из свойств 3D-модели:

        doc, part = open_part(filepath, is_hidden=True)
        return get_dxf_path_from_3d(part)

    # если всё плохо - имя DXF-файла генерируется из имени файла чертежа
    except:
        path = doc_dwg.PathName
        d, base = os.path.split(path)
        n, ext = os.path.splitext(base)
        return _get_dxf_path(d, 0, "", n)


def create_DXF_from_part(filepath: str = "", do_close_afterall: bool = True):
    doc5, part5 = open_part_K5(filepath, True)
    if not check_view_projection_K5(doc5):
        raise Exception(f"В модели не создана ориентация \"{FASTDXF_PROJECTION_NAME}\"")

    doc_part, part = open_part(filepath)
    dxf_path = get_dxf_path_from_3d(part)
    remember_path(dxf_path)

    doc_dwg: KAPI7.IKompasDocument2D = _create_drawing_from_part(doc_part.PathName)

    view_dwg: KAPI7.IView = get_dxf_view(doc_dwg, False)

    doc_fragm: KAPI7.IKompasDocument2D = create_dxf_from_dwg_view(view_dwg)

    if do_close_afterall:
        doc_dwg.Close(0)
    # остается открытым Фрагмент с контуром для редактирования - например, убрать резьбы/фаски


def create_DXF_from_dwg(do_rename_view: bool = False):
    doc_dwg: KAPI7.IKompasDocument2D = open_doc2d("")

    view_dwg: KAPI7.IView = get_dxf_view(doc_dwg, True)

    if do_rename_view and view_dwg.Name != FASTDXF_DWG_VIEW_NAME:
        another_view = get_view_by_name(doc_dwg, FASTDXF_DWG_VIEW_NAME, False)
        if not (another_view is None) and not (another_view is view_dwg):
            raise Exception(f"Уже существует вид '{FASTDXF_DWG_VIEW_NAME}', а выбран вид '{view_dwg.Name}'")

        old_name = view_dwg.Name
        view_dwg.Name = FASTDXF_DWG_VIEW_NAME
        is_renamed: bool = view_dwg.Update()
        if is_renamed:
            print(f"Вид '{old_name}' переименован в '{FASTDXF_DWG_VIEW_NAME}'.")
        else:
            print(f"Не удалось переименовать вид '{old_name}' в '{FASTDXF_DWG_VIEW_NAME}'.")

    dxf_path = get_dxf_path_from_2d(doc_dwg, view_dwg)
    remember_path(dxf_path)

    doc_fragm: KAPI7.IKompasDocument2D = create_dxf_from_dwg_view(view_dwg)
    # остается открытым Фрагмент с контуром для редактирования - например, убрать резьбы/фаски


def save_fragm(path: str) -> None:
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app: KAPI7.IApplication = get_app7(iKompasObject7)

    doc_fragm: KAPI7.IKompasDocument2D = KAPI7.IKompasDocument2D(app.ActiveDocument)

    doc_fragm.SaveAs(path)
    print(f"Сохранено в '{path}'")



def rename_selected_view(active_doc: KAPI7.IKompasDocument2D, new_name: str, single_only: bool = True) -> None:
    views: list[KAPI7.IView] = get_selected(KAPI7.IKompasDocument2D1(active_doc), (KAPI7.IView, KAPI7.IAssociationView))
    if single_only and len(views) != 1:
        raise Exception(f"Допускается только один выбранный вид. Текущее количество выбранных видов: {len(views)}.")
    if len(views) > 0:
        view = KAPI7.IView(views[0])
        view.Name = new_name
        view.Update()


def check_view_projection_K5(doc: KAPI5.ksDocument3D) -> bool:
    """ Проверка, есть ли в модели проекция (ориентация) с кодовым названием для DXF """

    vpc: KAPI5.ksViewProjectionCollection = doc.GetViewProjectionCollection()

    for i in range(vpc.GetCount()):
        vp: KAPI5.ksViewProjection = vpc.GetByIndex(i)
        if vp.name == FASTDXF_PROJECTION_NAME:
            return True
    return False



def create_current_view_projection_K5(doc: KAPI5.ksDocument3D, projection_name: str, do_set_current: bool = True) -> None:
    """
    Создание в детали проекции (ориентации).

    Используется для задания направления проецирования в чертеж для последующего DXF.
    """

    vpc: KAPI5.ksViewProjectionCollection = doc.GetViewProjectionCollection()
    vpc.DetachByName(projection_name)

    vp: KAPI5.ksViewProjection = vpc.NewViewProjection()
    vp.name = projection_name
    vpc.Add(vp)

    if do_set_current:
        vp.SetCurrent()


def _create_drawing_from_part(part_filename: str) -> KAPI7.IKompasDocument2D:
    """ Создание чертежа и проекционного вида в нем """
    print(part_filename)
    if part_filename == "":
        raise Exception("Путь к файлу детали некорректный")

    app = get_app7()
    app.HideMessage = 2  # Не показывать и отвечать "НЕТ"

    doc_dwg = create_document2d(app, DocumentTypeEnum.ksDocumentDrawing)

    vlm: KAPI7.IViewsAndLayersManager = doc_dwg.ViewsAndLayersManager
    views: KAPI7.IViews = vlm.Views

    view: KAPI7.IAssociationView = KAPI7.IAssociationView(views.Add(2))
    view.SourceFileName = part_filename
    view.Unfold = True
    view.BendLinesVisible = True
    view.ProjectionName = FASTDXF_PROJECTION_NAME
    view.Name = FASTDXF_DWG_VIEW_NAME

    rc = view.Update()
    if rc == False:
        raise Exception("Не удалось создать вид в чертеже")

    app.HideMessage = 0  # Показывать

    return doc_dwg

def get_dxf_view(doc_dwg: KAPI7.IKompasDocument2D, use_selected_view: bool = True) -> KAPI7.IView:
    if use_selected_view:
        doc_dwg2d1 = KAPI7.IKompasDocument2D1(doc_dwg)
        selected_views: list[KAPI7.IView] = get_selected(doc_dwg2d1, (KAPI7.IView, KAPI7.IAssociationView))
        if len(selected_views) != 0:
            return selected_views[0]
    return get_view_by_name(doc_dwg, FASTDXF_DWG_VIEW_NAME)


def create_dxf_from_dwg_view(view_dwg: KAPI7.IView) -> KAPI7.IKompasDocument2D:
    """ Копирование геометрии из вида чертежа во фрагмент. """

    print(f"Используется вид чертежа '{view_dwg.Name}'")

    app = get_app7()
    doc_fragm: KAPI7.IKompasDocument2D = create_document2d(app, DocumentTypeEnum.ksDocumentFragment)

    view_fragm: KAPI7.IView = get_system_view(doc_fragm)

    dc_dwg: KAPI7.IDrawingContainer = KAPI7.IDrawingContainer(view_dwg)
    dc_fragm: KAPI7.IDrawingContainer = KAPI7.IDrawingContainer(view_fragm)

    d_types = {}

    visible_layers_numbers: list[int] = get_visible_layers_numbers(app, view_dwg)

    for obj in dc_dwg.Objects(0):

        key = str(type(obj))
        if not key in d_types:
            d_types[key] = 0
        d_types[key] += 1

        try:
            obj.LayerNumber
        except:
            continue

        if obj.LayerNumber in visible_layers_numbers:
            copy_dwg_object(obj, dc_fragm)

    view_fragm.Update()

    return doc_fragm


def copy_dwg_object(obj, target_dc: KAPI7.IDrawingContainer) -> None:
    o2: KAPI7.IDrawingObject = None

    if isinstance(obj, KAPI7.ILineSegment):
        o1: KAPI7.ILineSegment = obj
        o2: KAPI7.ILineSegment = target_dc.LineSegments.Add()
        o2.Style = o1.Style
        o2.X1 = o1.X1
        o2.X2 = o1.X2
        o2.Y1 = o1.Y1
        o2.Y2 = o1.Y2

    elif isinstance(obj, KAPI7.IArc):
        o1: KAPI7.IArc = obj
        o2: KAPI7.IArc = target_dc.Arcs.Add()
        o2.Style = o1.Style
        o2.Xc = o1.Xc
        o2.Yc = o1.Yc
        o2.Angle1 = o1.Angle1
        o2.Angle2 = o1.Angle2
        o2.Radius = o1.Radius
        o2.Direction = o1.Direction

    elif isinstance(obj, KAPI7.ICircle):
        o1: KAPI7.ICircle = obj
        o2: KAPI7.ICircle = target_dc.Circles.Add()
        o2.Style = o1.Style
        o2.Xc = o1.Xc
        o2.Yc = o1.Yc
        o2.Radius = o1.Radius

    elif isinstance(obj, KAPI7.IEllipseArc):
        o1: KAPI7.IEllipseArc = obj
        o2: KAPI7.IEllipseArc = target_dc.EllipseArcs.Add()
        o2.Style = o1.Style
        o2.Angle = o1.Angle
        o2.Angle1 = o1.Angle1
        o2.Angle2 = o1.Angle2
        o2.Direction = o1.Direction
        o2.SemiAxisA = o1.SemiAxisA
        o2.SemiAxisB = o1.SemiAxisB
        o2.Style = o1.Style
        o2.T1 = o1.T1
        o2.T2 = o1.T2
        o2.Xc = o1.Xc
        o2.Yc = o1.Yc

    elif isinstance(obj, KAPI7.INurbs):
        o1: KAPI7.INurbs = obj
        o2: KAPI7.INurbs = target_dc.Nurbses.Add()
        o2.Style = o1.Style
        _, p, w, k = o1.GetNurbsParams()
        d = o1.Degree
        c = o1.Closed
        o2.SetNurbsParams(p, w, k, d, c)


    else:
        pass
        # print("Unsupported for now:", obj)

    if not o2 is None:
        o2.Update()


def get_visible_layers_numbers(app: KAPI7.IApplication, view: KAPI7.IView) -> list:
    layer_numbers: list[int] = []
    ls: KAPI7.ILayers = view.Layers
    for i in range(ls.Count):
        l: KAPI7.ILayer = ls.Layer(i)
        if l.Visible:
            layer_numbers.append(l.LayerNumber)
    return layer_numbers




class MacrosFastDXF(Macros):
    def __init__(self) -> None:
        super().__init__("fast_dxf", "Быстрое создание DXF")

    def check_config(self) -> None:
        try:
            assert isinstance(self._config["do_rename_selected_view_to_DXF"], bool)
        except:
            self._config["do_rename_selected_view_to_DXF"] = False

    def settings_widget(self) -> QtWidgets.QWidget:
        def _apply_changes():
            self._config["do_rename_selected_view_to_DXF"] = cb_do_rename_view_in_dwg.isChecked()
            config.save_delayed()

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        cb_do_rename_view_in_dwg = QtWidgets.QCheckBox(f"При создании DXF-фрагмента из 2D-чертежа присваивать выбранному виду название '{FASTDXF_DWG_VIEW_NAME}'")
        cb_do_rename_view_in_dwg.setChecked(self._config["do_rename_selected_view_to_DXF"])
        cb_do_rename_view_in_dwg.stateChanged.connect(_apply_changes)

        l.addWidget(cb_do_rename_view_in_dwg, 0, 0, 1, 1)
        return w

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        btn_main_projection = QtWidgets.QToolButton()
        btn_main_projection.setIcon(QtGui.QIcon(get_resource_path("img/macros/main_projection.svg")))
        btn_main_projection.setToolTip("Создать/обновить ориентацию главного вида в открытой модели")
        btn_main_projection.clicked.connect(lambda: self.execute(self._create_main_projection))

        btn_dxf_from_part = QtWidgets.QToolButton()
        btn_dxf_from_part.setIcon(QtGui.QIcon(get_resource_path("img/macros/dxf_from_part.svg")))
        btn_dxf_from_part.setToolTip("Создать DXF для открытой детали")
        btn_dxf_from_part.clicked.connect(lambda: self.execute(create_DXF_from_part))

        btn_dxf_from_dwg = QtWidgets.QToolButton()
        btn_dxf_from_dwg.setIcon(QtGui.QIcon(get_resource_path("img/macros/dxf_from_dwg.svg")))
        btn_dxf_from_dwg.setToolTip(f"Создать DXF из вида \"{FASTDXF_DWG_VIEW_NAME}\" в открытом чертеже")
        btn_dxf_from_dwg.clicked.connect(lambda: self.execute(lambda: create_DXF_from_dwg(self._config["do_rename_selected_view_to_DXF"])))

        btn_dxf_projection = QtWidgets.QToolButton()
        btn_dxf_projection.setIcon(QtGui.QIcon(get_resource_path("img/macros/dxf_part_orientation.svg")))
        btn_dxf_projection.setToolTip(f"Создать/обновить ориентацию \"{FASTDXF_PROJECTION_NAME}\" в открытой модели")
        btn_dxf_projection.clicked.connect(lambda: self.execute(self._update_viewprojection))

        btn_save_fragm = QtWidgets.QToolButton()
        btn_save_fragm.setIcon(QtGui.QIcon(get_resource_path("img/macros/dxf_save_fragm.svg")))
        btn_save_fragm.setToolTip(f"Сохранить фрагмент как DXF")
        btn_save_fragm.clicked.connect(lambda: self.execute(self._save_fragm))

        return {
            "обновить ориентацию главного вида в модели": btn_main_projection,
            "обновить DXF-ориентацию в модели": btn_dxf_projection,
            "создать DXF для открытой детали": btn_dxf_from_part,
            "создать DXF из открытого чертежа": btn_dxf_from_dwg,
            "сохранить текущий фрагмент в DXF": btn_save_fragm,
        }

    def _create_main_projection(self) -> None:
        doc, part = open_part_K5()
        create_current_view_projection_K5(doc, MAIN_PROJECTION_NAME, True)

    def _update_viewprojection(self) -> None:
        doc, part = open_part_K5()
        create_current_view_projection_K5(doc, FASTDXF_PROJECTION_NAME, True)

    def _save_fragm(self) -> None:
        QtWidgets.qApp.restoreOverrideCursor()
        path: str = get_path()
        ext_dxf = f"DXF (*.dxf)"
        ext_frw = f"Компас-Фрагмент (*.frw)"

        path, _f = QtWidgets.QFileDialog.getSaveFileName(
            self._parent_widget,
            "Сохранить как DXF",
            path,
            f"{ext_dxf};;{ext_frw};;Все файлы (*)",
            ext_dxf,
        )
        if path != "":
            QtWidgets.qApp.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
            save_fragm(path)
            QtWidgets.qApp.restoreOverrideCursor()


if __name__ == "__main__":
    doc5, part5 = open_part_K5()
    print(get_gabarit5(part5))
