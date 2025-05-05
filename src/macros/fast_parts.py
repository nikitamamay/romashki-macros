"""
Узко специализированный макрос, предназначенный для работы по определенной
методологии моделирования сверху-вниз.

Методология в общей сути повторяет методологию проектирования сверху-вниз
в Siemens NX, но адаптирована для Компас и предполагает двухэтапное моделирование.
Первым этапом создается многотельная (тела представляют будущие детали) work-модель
с ассоциативными взаимосвязями построений этих тел.
Вторым этапом создаются результирующие (out-) детали и сборки по всем правилам
оформления 3D-моделей (с обозначениями, наименованиями, с заданным материалом);
в out-детали ассоциативно копируются созданные в work-модели тела; а в out-сборки
вставляются out-детали с фиксацией в центре системы координат.

Макрос предоставляет функционал:
1. Создание новой детали из выбранного тела в текущей модели в вставка этой
детали в другую (результирующую) сборку в начале системы координат с фиксацией.

    При этом создается новая деталь. В нее вставляется текущая модель как
    компоновочная геометрия и выполняется операция "Копировать объекты" из этой
    вставленной компоновочной геометрии. Копируется тело. Деталь получает
    обозначение и наименование и сохраняется. Затем она вставляется в результирующую
    сборку.

2. Создание новой детали со вставкой текущей модели в эту деталь в качестве
компоновочной геометрии.

    Этот функционал полезен для быстрого создания результирующих деталей или сборок,
    в которых неуместен функционал под пунктом 1. То есть создается новая деталь,
    а текущая модель вставляется в нее в качестве компоновочной геометрии, выполняется
    переключение документа на эту деталь, и дальнейшие построения предоставляются
    пользователю. Как правило, так создаются листовые гнутые тела; ведь при простом
    копировании тела, построенного в компоновочной геометрии как гнутым листовым,
    теряется его свойства и развертка; поэтому его нужно строить заново (по крайней
    мере, в Компас16).

3. Ориентация (то есть наложение сопряжений "Параллельность" или "Перпендикулярность"
с плоскостями АСК компонента) выбранных компонентов параллельно ближайшим
осям абсолютной системы координат сборки или параллельно/перпендикулярно
выбранным произвольным плоскостям или осям.

    Этот функционал полезен при особом способе создания сопряжений: этой командой
    создается два сопряжения, которые однозначно ориентируют компонент (блокируют
    вращательные степени свободы). Далее пользователю остается только задать сопряжение
    "Совпадение" между точкой компонента и точкой компоновочной геометрии для
    однозначного размещения (блокирования поступательных степенй свободы) компонента.

4. Вставка выбранных компонентов компоновочной геометрии в текущую сборку
с наложением сопряжения "Совпадение" между вставленным компонентом и компонентом
компоновочной геометрии.

    Этот функционал полезен для переноса в результрующую сборку компонентов
    из work-сборки.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path

from src.macros.do_not_disturb import set_silent_mode, get_silent_mode

PLANES = [
    LDefin3D.o3d_planeXOY,
    LDefin3D.o3d_planeXOZ,
    LDefin3D.o3d_planeYOZ,
    LDefin3D.o3d_planeOffset,
    LDefin3D.o3d_planeAngle,
    LDefin3D.o3d_plane3Points,
    LDefin3D.o3d_planeNormal,
    LDefin3D.o3d_planeTangent,
    LDefin3D.o3d_planeEdgePoint,
    LDefin3D.o3d_planeParallel,
    LDefin3D.o3d_planePerpendicular,
    LDefin3D.o3d_planeLineToEdge,
    LDefin3D.o3d_planeLineToPlane,
]
AXES = [
    LDefin3D.o3d_axisOX,
    LDefin3D.o3d_axisOY,
    LDefin3D.o3d_axisOZ,
    LDefin3D.o3d_axis2Planes,
    LDefin3D.o3d_axis2Points,
    LDefin3D.o3d_axisConeFace,
    LDefin3D.o3d_axisEdge,
    LDefin3D.o3d_axisOperation,
]



def unique(arr: typing.Iterable, key=lambda el: el) -> typing.Iterable:
    unique_keys = set()
    for el in arr:
        k = key(el)
        if not k in unique_keys:
            unique_keys.add(k)
            yield el


def str_max_length(s: str, max_length: int) -> str:
    if len(s) > max_length:
        return s[:max_length - 3] + "..."
    return s


def get_axis_vector(axis: KAPI7.IAxis3D) -> tuple[float, float, float]:
    assert isinstance(axis, KAPI7.IAxis3D)
    mc: KAPI7.IMathCurve3D = axis.MathCurve
    _, x, y, z = mc.GetTangentVector(0)
    return x, y, z

def get_axis_vector_K5(axis: KAPI5.ksDefaultObject) -> tuple[float, float, float]:
    assert isinstance(axis, KAPI5.ksDefaultObject)
    mc = axis.GetCurve3D()
    _, x, y, z = mc.GetTangentVector(0)
    return x, y, z

def get_scalar_product(v1: tuple[float, float, float], v2: tuple[float, float, float]) -> float:
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]


def get_axes(part_or_cs: KAPI7.IPart7|KAPI7.ILocalCoordinateSystem) -> tuple[KAPI7.IAxis3D, KAPI7.IAxis3D, KAPI7.IAxis3D]:
    assert isinstance(part_or_cs, (KAPI7.IPart7, KAPI7.ILocalCoordinateSystem))
    axis_X: KAPI7.IAxis3D = part_or_cs.DefaultObject(LDefin3D.o3d_axisOX)
    axis_Y: KAPI7.IAxis3D = part_or_cs.DefaultObject(LDefin3D.o3d_axisOY)
    axis_Z: KAPI7.IAxis3D = part_or_cs.DefaultObject(LDefin3D.o3d_axisOZ)
    return (axis_X, axis_Y, axis_Z)


def get_axes_K5(part_or_cs5: KAPI5.ksPart) -> list[KAPI5.ksEntity]:
    # assert isinstance(part_or_cs5, (KAPI7.IPart7, KAPI7.ILocalCoordinateSystem))
    axis_X: KAPI5.ksEntity = part_or_cs5.GetDefaultEntity(LDefin3D.o3d_axisOX)
    axis_Y: KAPI5.ksEntity = part_or_cs5.GetDefaultEntity(LDefin3D.o3d_axisOY)
    axis_Z: KAPI5.ksEntity = part_or_cs5.GetDefaultEntity(LDefin3D.o3d_axisOZ)
    return (axis_X, axis_Y, axis_Z)


def get_constraint_type(plane_or_axis: KAPI5.ksEntity) -> int:
    if plane_or_axis.type in PLANES:
        return LDefin3D.mc_Perpendicular
    elif plane_or_axis.type in AXES:
        return LDefin3D.mc_Parallel
    else:
        raise Exception("Неподдерживаемый тип ksEntity:", plane_or_axis.type, plane_or_axis)


def get_normal_vector_K5(plane_or_axis: KAPI5.ksEntity) -> tuple[float, float, float]:
    if plane_or_axis.type in PLANES:
        surface: KAPI5.ksSurface = plane_or_axis.GetDefinition().GetSurface()
        return surface.GetNormal(0, 0)[1:]
    elif plane_or_axis.type in AXES:
        curve: KAPI5.ksCurve3D = plane_or_axis.GetDefinition().GetCurve3D()
        return curve.GetTangentVector(0)[1:]
    else:
        raise Exception("Неподдерживаемый тип ksEntity:", plane_or_axis.type, plane_or_axis)


def get_closest_axis_K5(
        initial_v: tuple[float, float, float],
        target_axes: list[KAPI5.ksEntity],
        ) -> KAPI5.ksEntity:
    closest = 0
    sp = get_scalar_product(initial_v, get_axis_vector_K5(target_axes[0].GetDefinition()))
    for i in range(1, len(target_axes)):
        target_v = get_axis_vector_K5(target_axes[i].GetDefinition())
        new_sp = get_scalar_product(initial_v, target_v)
        if abs(new_sp) > abs(sp):
            closest = i
            sp = new_sp
    return target_axes[closest]


def get_closest(entity: KAPI5.ksEntity, part_vectors: list[tuple[float, float, float]]) -> tuple[float, int]:
    """
    Возвращает `scalar_product` и индекс `closest_i` вектора из `part_vectors` с наибольшим `scalar_product`.
    """
    e_v = get_normal_vector_K5(entity)
    m = list(map(
            lambda el: (get_scalar_product(el[1], e_v), el[0]),
            enumerate(part_vectors)
        ))
    s = sorted(
        m,
        key=lambda el: abs(el[0]),
        reverse=True,  # реверс нужен, так как наибольшее скалярное произведение = почти параллельность
    )
    return s[0]



def orient_part() -> None:
    doc, toppart = open_part()

    parts = get_selected(doc, KAPI7.IPart7)
    if len(parts) == 0:
        raise Exception("Компоненты не выбраны")

    CSs = get_selected(doc, KAPI7.ILocalCoordinateSystem)
    if len(CSs) != 1:
        print(f"Выбрано {len(CSs)} ЛСК; используется АСК детали.")
        target_axes = get_axes(toppart)
    else:
        cs: KAPI7.ILocalCoordinateSystem = CSs[0]
        print(f"Используется ЛСК \"{cs.Name}\".")
        target_axes = get_axes(cs)

    for part in parts:
        part_axes = get_axes(part)


def orient_part_K5() -> None:
    doc5, toppart5 = open_part_K5()

    parts: list[KAPI5.ksPart] = get_selected_K5(doc5, KAPI5.ksPart)
    if len(parts) == 0:
        raise Exception("Компоненты не выбраны")

    target_geom = get_selected_K5(doc5, KAPI5.ksEntity)
    if len(target_geom) == 0:
        print(f"Не выбрана вспомогательная геометрия; используется АСК сборки.")
        target_geom = get_axes_K5(toppart5)[:2]
    else:
        print(f"Выбраны {len(target_geom)} элементов вспомогательной геометрии.")


    for part in parts:
        plcm: KAPI5.ksPlacement = part.GetPlacement()
        part_axes = get_axes_K5(part)
        part_vectors = [plcm.GetVector(i)[1:] for i in range(3)]  # FIXME нет перевода из СК детали в СК сборки?
        pos_x, pos_y, pos_z = plcm.GetOrigin()[1:]

        constraint_specs = []

        for entity in target_geom:
            scalar_product, closest_i = get_closest(entity, part_vectors)
            constraint_type = get_constraint_type(entity)  # LDefin3D.mc_Parallel для осей и LDefin3D.mc_Perpendicular для плоскостей

            constraint_specs.append([scalar_product, closest_i, entity, constraint_type])

        constraint_specs = unique(
            sorted(
                constraint_specs,
                key=lambda el: abs(el[0]),
                reverse=True,  # нужен реверс, так как наибольшее скалярное произведение = почти параллельность
            ),
            lambda el: el[1],
        )

        for spec in constraint_specs:
            KAPI5.ksEntity
            _, closest_i, entity, constraint_type = spec

            res = doc5.AddMateConstraint(
                constraint_type,
                part_axes[closest_i],
                entity,
                0,
                2,
                0,
            )

            print(repr(str_max_length(f"{part.marking} {part.name}".strip(), 75)), "-", repr(entity.name), res)

        # не работает?
        plcm.SetOrigin(pos_x, pos_y, pos_z)
        part.UpdatePlacement()

        part.Update()




def constrain_closest_points() -> None:
    doc5, toppart5 = open_part_K5()

    parts: list[KAPI5.ksPart] = get_selected_K5(doc5, KAPI5.ksPart)
    if len(parts) == 0:
        raise Exception("Компоненты не выбраны")

    # FIXME
    raise Exception("Not implemented")




def create_fast_part(target_asm_filepath: str, new_part_path: str):
    new_part_path = os.path.normpath(new_part_path)

    name, ext = os.path.splitext(os.path.basename(new_part_path))
    is_assembly = (ext == ".a3d")

    app = get_app7()
    doc, toppart = open_part()

    prev_silent_mode = app.HideMessage
    app.HideMessage = 1

    child_doc, child_part = create_part(
        DocumentTypeEnum.ksDocumentAssembly if is_assembly else DocumentTypeEnum.ksDocumentPart
    )
    part_lg: KAPI7.IPart7 = add_part(child_part, doc.PathName, True)
    child_doc.RebuildDocument()
    child_part.Name = name
    child_part.Update()
    child_doc.SaveAs(new_part_path)

    asm_doc, asm_part = open_part(target_asm_filepath, True)

    part_in_asm: KAPI7.IPart7 = add_part(asm_part, new_part_path, False)  # FIXME не добавляется деталь?
    part_in_asm.Fixed = True
    part_in_asm.Update()
    asm_part.Update()
    asm_doc.RebuildDocument()
    asm_doc.Save()

    open_part(new_part_path)  # FIXME не открывает эту созданную деталь. Проблема в методе open_part ?
    app.HideMessage = prev_silent_mode


def create_parts_from_selected_bodies(target_asm_filepath: str, parts_target_folder: str, do_close_child_docs: bool):
    active_doc, work_part = open_part()

    active_doc_path = remember_opened_document()

    body_strs: list[str] = [get_body_str(b) for b in get_selected(active_doc, KAPI7.IBody7)]
    print(f"{len(body_strs)} bodies are selected:", body_strs)

    asm_doc, asm_part = open_part(target_asm_filepath)

    if parts_target_folder == "":
        parts_target_folder = asm_doc.Path
    ensure_folder(parts_target_folder)

    for b_str in body_strs:
        child_doc, child_part = create_part(DocumentTypeEnum.ksDocumentPart)
        part_lg: KAPI7.IPart7 = add_part(child_part, active_doc_path, True)

        # body: KAPI7.IBody7 = part_lg.GetBodyById(b_marking)  # нет такой функции в Компас16
        body: KAPI7.IBody7 = get_body_by_str(part_lg, b_str)

        mo_p_pl: KAPI7.IModelObject = KAPI7.IModelObject(part_lg)
        mo_p_pl.Hidden = True
        mo_p_pl.Update()

        copy_geometry(child_part, [body])
        child_doc.RebuildDocument()

        child_part.Marking = body.Marking
        child_part.Name = body.Name

        # mo_p_pl: KAPI7.IModelObject = KAPI7.IModelObject(part_lg)
        # mo_p_pl.Hidden = True  # FIXME добавить опцию в config о скрытии компоновочной геометрии? (а надо?)
        child_part.Update()

        filename = f"{child_part.Marking} {child_part.Name}.m3d".strip()
        child_doc_filename = os.path.normpath(f"{parts_target_folder}/{filename}")
        child_doc.SaveAs(child_doc_filename)
        print(f"Сохранено в '{child_doc_filename}'")
        if do_close_child_docs:
            try:
                child_doc.Close(1)  # с сохранением
            except Exception as e:
                print(f"Cannot close document '{child_doc.PathName}'")

        part_in_asm: KAPI7.IPart7 = add_part(asm_part, child_doc_filename, False)
        part_in_asm.Fixed = True
        part_in_asm.Update()

        asm_doc.Active = True
        asm_doc.RebuildDocument()
        asm_doc.Save()




def get_body_str(body: KAPI7.IBody7) -> str:
    return body.Marking + body.Name


def get_body_by_str(part: KAPI7.IPart7, body_str: str) -> KAPI7.IBody7:
    feature: KAPI7.IFeature7 = KAPI7.IFeature7(part)
    arr = ensure_list(feature.ResultBodies)
    for body in arr:
        if get_body_str(body) == body_str:
            return body
    raise Exception(f"Не удается найти тело '{body_str}' в {part}")



def add_part(top_part: KAPI7.IPart7, filename: str, is_layout_geometry: bool = False) -> KAPI7.IPart7:
    parts: KAPI7.IParts7 = top_part.Parts

    child_part: KAPI7.IPart7 = parts.AddFromFile(filename, True, False)
    if not child_part.Valid:
        raise Exception("Что-то пошло не так при добавлении детали: ", filename, child_part)

    child_part.IsLayoutGeometry = is_layout_geometry
    child_part.Update()
    return child_part


def copy_geometry(top_part: KAPI7.IPart7, objects: list[KAPI7.IModelObject]) -> None:
    if len(objects) == 0:
        raise Exception("Массив объектов для операции 'Копирование объектов' не может быть пустым")

    mc: KAPI7.IModelContainer = KAPI7.IModelContainer(top_part)
    csg: KAPI7.ICopiesGeometry = mc.CopiesGeometry
    cg: KAPI7.ICopyGeometry = csg.Add()

    res = cg.AddInitialObjects(objects)
    if res:
        cg.Update()
    else:
        raise Exception("Не удалось скопировать геометрию", top_part.Marking, top_part.Name, objects)


def insert_parts_from_lg() -> None:
    doc5, toppart5 = open_part_K5()
    parts5: list[KAPI5.ksPart] = get_selected_K5(doc5, KAPI5.ksPart)
    for part5 in parts5:
        new_part5: KAPI5.ksPart = doc5.GetPart(LDefin3D.pNew_Part)
        doc5.SetPartFromFile(part5.fileName, new_part5, True)
        new_part5.Update()
        toppart5.Update()

        ent_old: KAPI5.ksEntity = part5.GetDefaultEntity(LDefin3D.o3d_pointCS)
        ent_new: KAPI5.ksEntity = new_part5.GetDefaultEntity(LDefin3D.o3d_pointCS)

        # оказывается, сопряжение "Совпадение" создается на системы координат (а не на точку!)
        res = doc5.AddMateConstraint(
            LDefin3D.mc_Coincidence,
            ent_old,
            ent_new,
            0,
            2,
            0,
        )
        print(part5.marking, part5.name, "- совпадение установлено:", res)


def copy_bodies_from_lg() -> None:
    doc, toppart = open_part()
    bodies: list[KAPI7.IBody7] = get_selected(doc, KAPI7.IBody7)
    if len(bodies) > 0:
        copy_geometry(toppart, bodies)



class MacrosFastParts(Macros):
    def __init__(self) -> None:
        super().__init__(
            "fast_parts",
            "Работа с компонентами",
        )

        self._last_selected_target_asm_path = ""

    def check_config(self):
        try:
            assert isinstance(self._config["do_close_child_docs"], bool)
        except:
            self._config["do_close_child_docs"] = False

    def settings_widget(self):
        def _set_do_close_child_docs(state: bool) -> None:
            self._config["do_close_child_docs"] = state
            config.save_delayed()

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        cb = QtWidgets.QCheckBox("Закрывать файлы деталей при их создании из выбранных тел")
        cb.setChecked(self._config["do_close_child_docs"])
        cb.stateChanged.connect(_set_do_close_child_docs)

        l.addWidget(cb, 0, 0, 1, 1)
        return w

    def toolbar_widgets(self):
        btn_fast_parts = QtWidgets.QPushButton(
            QtGui.QIcon(get_resource_path("img/macros/fast_parts_work_to_out.svg")),
            ""
        )
        btn_fast_parts.setToolTip("Создать out-детали из выбранных тел")
        btn_fast_parts.clicked.connect(self._create_out_parts)


        btn_create_fast_part = QtWidgets.QPushButton(
            QtGui.QIcon(get_resource_path("img/macros/fast_part_single.svg")),
            ""
        )
        btn_create_fast_part.setToolTip("Создать out-модель с компоновочной геометрией и вставить её в сборку")
        btn_create_fast_part.clicked.connect(self._create_single_out_part)


        btn_orient = QtWidgets.QPushButton(
            QtGui.QIcon(get_resource_path("img/macros/orient.svg")),
            ""
        )
        btn_orient.setToolTip(
            "Ориентировать выбранные компоненты\n"
            "параллельно осям АСК сборки"
        )
        btn_orient.clicked.connect(lambda: self.execute(orient_part_K5))


        btn_insert_parts_from_lg = QtWidgets.QPushButton(
            QtGui.QIcon(get_resource_path("img/macros/insert_parts_from_lg.svg")),
            ""
        )
        btn_insert_parts_from_lg.setToolTip(
            "Вставить выбранные компоненты\n"
            "компоновочной геометрии в текущую сборку")
        btn_insert_parts_from_lg.clicked.connect(
            lambda: self.execute(self._create_parts_and_bodies_from_lg)
        )

        return {
            "кнопка ориентирования компонентов": btn_orient,
            "кнопка создания out-деталей": btn_fast_parts,
            "кнопка создания одной out-модели": btn_create_fast_part,
            "кнопка вставки компонентов": btn_insert_parts_from_lg,
        }


    def _create_out_parts(self) -> None:
        doc, part = open_part()
        path_dir = doc.Path

        if self._last_selected_target_asm_path == "":
            self._last_selected_target_asm_path = path_dir

        # get_selected(doc)  # для вызова print() этих выбранных объектов

        target_asm_path, filter_ = QtWidgets.QFileDialog.getOpenFileName(
            self._parent_widget,
            "Выбрать путь к файлу out-сборки",
            self._last_selected_target_asm_path,
            f"{gui_widgets.EXT_ASSEMBLY};;{gui_widgets.EXT_PART};;{gui_widgets.EXT_ALL}",
            gui_widgets.EXT_ASSEMBLY,
        )

        if target_asm_path == "":
            print("Команда отменена")
            return

        self._last_selected_target_asm_path = target_asm_path

        parts_dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self._parent_widget,
            "Выбрать путь к папке создаваемых деталей",
            path_dir,
        )

        if parts_dir_path == "":
            print("Команда отменена")
            return

        self.execute(
            lambda: create_parts_from_selected_bodies(target_asm_path, parts_dir_path, self._config["do_close_child_docs"])
        )

    def _create_single_out_part(self) -> None:
        try:
            path_dir = os.path.dirname(remember_opened_document())
        except:
            path_dir = ""

        if self._last_selected_target_asm_path == "":
            self._last_selected_target_asm_path = path_dir

        target_asm_path, filter_ = QtWidgets.QFileDialog.getOpenFileName(
            self._parent_widget,
            "Выбрать путь к файлу out-сборки",
            self._last_selected_target_asm_path,
            f"{gui_widgets.EXT_ASSEMBLY};;{gui_widgets.EXT_PART};;{gui_widgets.EXT_ALL}",
            gui_widgets.EXT_ASSEMBLY,
        )

        if target_asm_path == "":
            print("Команда отменена")
            return

        self._last_selected_target_asm_path = target_asm_path

        fast_part_path, filter_ = QtWidgets.QFileDialog.getSaveFileName(
            self._parent_widget,
            "Выбрать путь к файлу out-модели",
            path_dir,
            f"{gui_widgets.EXT_ASSEMBLY};;{gui_widgets.EXT_PART};;{gui_widgets.EXT_ALL}",
            gui_widgets.EXT_ASSEMBLY,
        )

        if fast_part_path == "":
            print("Команда отменена")
            return

        self.execute(
            lambda: create_fast_part(target_asm_path, fast_part_path)
        )

    def _create_parts_and_bodies_from_lg(self) -> None:
        insert_parts_from_lg()
        copy_bodies_from_lg()


if __name__ == "__main__":
    orient_part_K5()
