"""
Макрос служит для удобной организации истории дерева построения модели.

Макрос предоставляет функционал по переносу сразу нескольких элементов дерева
построения (features) перед или после некоторого другого элемента дерева.

Также в этом макросе предполагалось сделать функционал по автоматической
сортировке выбранных элементов дерева построения, но он не разработан.

"""


from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path

import re


EntityTypes = {
    "o3d_unknown"                    : 0,   # неизвестный (включает все объекты)
    "o3d_planeXOY"                   : 1,   # плоскость XOY
    "o3d_planeXOZ"                   : 2,   # плоскость XOZ
    "o3d_planeYOZ"                   : 3,   # плоскость YOZ
    "o3d_pointCS"                    : 4,   # точка начала системы координат
    "o3d_sketch"                     : 5,   # эскиз
    "o3d_face"                       : 6,   # поверхность
    "o3d_edge"                       : 7,   # грань
    "o3d_vertex"                     : 8,   # вершина
    "o3d_axis2Planes"                : 9,   # ось по двум плоскостям
    "o3d_axis2Points"                : 10,  # ось по двум точкам
    "o3d_axisConeFace"               : 11,  # ось конической грани
    "o3d_axisEdge"                   : 12,  # ось проходящая через ребро
    "o3d_axisOperation"              : 13,  # ось операции
    "o3d_planeOffset"                : 14,  # смещённая плоскость
    "o3d_planeAngle"                 : 15,  # плоскость под углом
    "o3d_plane3Points"               : 16,  # плоскость по 3-м точкам
    "o3d_planeNormal"                : 17,  # нормальная плоскость
    "o3d_planeTangent"               : 18,  # касательная плоскость
    "o3d_planeEdgePoint"             : 19,  # плоскость через ребро и вершину
    "o3d_planeParallel"              : 20,  # плоскость через вершину параллельно другой плоскости
    "o3d_planePerpendicular"         : 21,  # плоскость через вершину перпендикулярно ребру
    "o3d_planeLineToEdge"            : 22,  # плоскость через ребро пар-но/пер-но другому ребру
    "o3d_planeLineToPlane"           : 23,  # плоскость через ребро пар-но/пер-но грани
    "o3d_baseExtrusion"              : 24,  # базовая операция выдавливания
    "o3d_bossExtrusion"              : 25,  # приклеивание выдавливанием
    "o3d_cutExtrusion"               : 26,  # вырезать выдавливанием
    "o3d_baseRotated"                : 27,  # базовая операция вращения
    "o3d_bossRotated"                : 28,  # приклеивание вращением
    "o3d_cutRotated"                 : 29,  # вырезать вращением
    "o3d_baseLoft"                   : 30,  # базовая операция вращения
    "o3d_bossLoft"                   : 31,  # приклеивание вращением
    "o3d_cutLoft"                    : 32,  # вырезать вращением
    "o3d_chamfer"                    : 33,  # операция "фаска"
    "o3d_fillet"                     : 34,  # операция "скругления"
    "o3d_meshCopy"                   : 35,  # операция копирования по сетке
    "o3d_circularCopy"               : 36,  # операция копирования по концентрической сетке
    "o3d_curveCopy"                  : 37,  # операция копирования по кривой
    "o3d_circPartArray"              : 38,  # операция массив по концентрической сетке для сборки
    "o3d_meshPartArray"              : 39,  # операция массив по сетке для сборки
    "o3d_curvePartArray"             : 40,  # операция массив по кривой для сборки
    "o3d_derivPartArray"             : 41,  # операция массив по кривой для сборки
    "o3d_incline"                    : 42,  # операция "уклон"
    "o3d_shellOperation"             : 43,  # операция "оболочка"
    "o3d_ribOperation"               : 44,  # операция "ребро жесткости"
    "o3d_baseEvolution"              : 45,  # кинематическая операция
    "o3d_bossEvolution"              : 46,  # приклеинть кинематически
    "o3d_cutEvolution"               : 47,  # вырезать кинематически
    "o3d_mirrorOperation"            : 48,  # операция "зеркальная копия"
    "o3d_mirrorAllOperation"         : 49,  # операция "зеркально отразить все"
    "o3d_cutByPlane"                 : 50,  # операция "сечение поверхностью"
    "o3d_cutBySketch"                : 51,  # операция "сечение эскизом"
    "o3d_holeOperation"              : 52,  # отверстие
    "o3d_polyline"                   : 53,  # ломаная
    "o3d_conicSpiral"                : 54,  # Коническая спираль
    "o3d_spline"                     : 55,  # сплайн
    "o3d_cylindricSpiral"            : 56,  #
    "o3d_importedSurface"            : 57,  # импортирванная поверхность
    "o3d_thread"                     : 58,  # ПК [4/10/2003] Условное отображение резьбы
    "o3d_EvolutionSurface"           : 59,  # Кинематическая поверхность
    "o3d_ExtrusionSurface"           : 60,  # Поверхность выдавливания
    "o3d_RotatedSurface"             : 61,  # Поверхность вращения
    "o3d_LoftSurface"                : 62,  # Поверхность по сечениям
    "o3d_MacroObject"                : 63,  # Макрообъект 3D
    "o3d_UnionComponents"            : 64,
    "o3d_MoldCavity"                 : 65,
    "o3d_planeMiddle"                : 66,
    "o3d_controlPoint"               : 67,  # Контрольная точка
    "o3d_conjunctivePoint"           : 68,  # Присоединительная точка
    "o3d_aggregate"                  : 69,
    "o3d_point3D"                    : 70,  # точка 3D
    "o3d_axisOX"                     : 71,  # ось OX
    "o3d_axisOY"                     : 72,  # ось OY
    "o3d_axisOZ"                     : 73,  # ось OZ
    "o3d_sheetMetalBody"             : 74,
    "o3d_sheetMetalBend"             : 75,
    "o3d_sheetMetalLineBend"         : 76,
    "o3d_sheetMetalHole"             : 77,
    "o3d_sheetMetalCut"              : 78,
    "o3d_UnHistoried"                : 79,
    "o3d_baselineDimension3D"        : 80,
    "o3d_lineDimension3D"            : 81,
    "o3d_radialDimension3D"          : 82,
    "o3d_diametralDimension3D"       : 83,
    "o3d_angleDimension3D"           : 84,
    "o3d_localCoordinateSystem"      : 85,
    "o3d_leader3D"                   : 86,
    "o3d_markLeader3D"               : 87,
    "o3d_rough3D"                    : 88,
    "o3d_positionLeader3D"           : 89,
    "o3d_brandLeader3D"              : 90,
    "o3d_base3D"                     : 91,
    "o3d_tolerance3D"                : 92,
    "o3d_SplitLine"                  : 93,
    "o3d_SurfacePatch"               : 94,
    "o3d_FaceRemover"                : 95,
    "o3d_SurfaceSewer"               : 96,
    "o3d_NurbsSurface"               : 97,
    "o3d_SurfacesIntersectionCurve"  : 98,
    "o3d_lastEntityElement"          : 99,  # Всегда последний из Entity!!!
}
EntityTypeNames = {v: k for k, v in EntityTypes.items()}
EntityTypes_lowercase = {k.lower(): v for k, v in EntityTypes.items()}

DATAROLE_O3D_TYPE = 101
DATAROLE_O3D_TYPES_ARRAY = 102

re_entity_type = re.compile(r'^o3d_\w+?', re.I)
re_entity_number = re.compile(r'^\b\d+\b', re.I)


remembered_features = []



def get_text_o3d(type_index: int) -> str:
    name = EntityTypeNames[type_index] if type_index in EntityTypeNames else str(type_index)
    return f"{type_index} | {name}"

def get_o3d_number(text: str) -> int:
    m = re_entity_number.search(text)
    if m:
        number = m.group(0)
        return int(number)

    m = re_entity_type.search(text)
    if m:
        name = m.group(0).lower()
        if name in EntityTypes_lowercase:
            return EntityTypes_lowercase[name]

    return 0



def get_selected_features5() -> list[KAPI5.ksFeature]:
    doc5, toppart5 = open_part_K5()
    doc5.enableRollBackFeaturesInCollections = True  # для возможности перемещения features под те features, которые уже под Указателем  --- НЕ_РАБОТАЕТ
    selected: list[KAPI5.ksEntity] = get_selected_K5(doc5, KAPI5.ksEntity)
    selected_features = list(map(lambda e: e.GetFeature(), selected))
    print(f"selected {len(selected_features)} features:", selected_features)
    return selected_features


def f1(selected_features: list[KAPI5.ksFeature], rb_points: dict[str, list[int]]) -> None:
    """
    Автосортировка дерева построения модели:
    функция для автоматического перемещения выбранных features
    перед/после определенных features (`rb_points`).
    """
    raise Exception("not implemented")



def f2_remember():
    global remembered_features
    remembered_features.clear()
    remembered_features.extend(get_selected_features5())
    if len(remembered_features) == 0:
        raise Exception("Не выбраны элементы дерева построения")


def f2_move():
    selected = get_selected_features5()
    if len(selected) == 0:
        raise Exception("Не выбран целевой элемент дерева построения")
    target_after = selected[0]

    doc5, toppart5 = open_part_K5()
    fc: KAPI5.ksFeatureCollection = toppart5.GetFeature().SubFeatureCollection(True, True)

    moved = 0
    for f in remembered_features:
        i_before = fc.FindIt(target_after) - 1
        target_before = fc.GetByIndex(i_before)

        if f == target_before:
            continue

        if not doc5.PlaceFeatureAfter(f, target_before):
            print(f"Не удалось перенести элемент '{f.name}' под элемент '{target_before.name}'")
        else:
            moved += 1

    fc.refresh()
    remembered_features.clear()

    print(f"Перемещено {moved} элементов дерева построения")



class O3DTypeCompleter(QtWidgets.QCompleter):
    def __init__(self, parent = None) -> None:
        super().__init__([get_text_o3d(i) for i in EntityTypeNames.keys()], parent)
        self.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        self.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)


class O3DTypeDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(
            self,
            parent: QtWidgets.QWidget,
            option: QtWidgets.QStyleOptionViewItem,
            index: QtCore.QModelIndex
            ) -> QtWidgets.QWidget:
        editor = QtWidgets.QLineEdit(parent)
        editor.setFrame(False)
        editor.setCompleter(O3DTypeCompleter())
        editor.setPlaceholderText("число-индекс или название для o3d_xxx...")
        return editor

    def setEditorData(self, editor: QtWidgets.QLineEdit, index: QtCore.QModelIndex) -> None:
        value: int = index.model().data(index, DATAROLE_O3D_TYPE)
        editor.setText(str(value))

    def setModelData(self, editor: QtWidgets.QLineEdit, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex) -> None:
        text: str = editor.text().strip()
        type_number = get_o3d_number(text)
        item_text = get_text_o3d(type_number)
        model.setData(index, type_number, DATAROLE_O3D_TYPE)
        model.setData(index, item_text, QtCore.Qt.ItemDataRole.DisplayRole)

    def updateEditorGeometry(self, editor: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        editor.setGeometry(option.rect)


class FastRollbackMacros(Macros):
    def __init__(self) -> None:
        super().__init__(
            "fast_rollback",
            "Быстрое перемещение указателя дерева построения"
        )
        self._to_config_message = ""

    def check_config(self) -> None:
        try:
            assert isinstance(self._config["rollback_points"], dict)
            for key, value in self._config["rollback_points"].items():
                assert isinstance(key, str)
                assert isinstance(value, list)
                for num in value:
                    assert isinstance(num, int)
        except:
            # rollback_points --- это элементы (features) дерева построения
            # с такими характерными именами, которые служат исключительно для
            # автоматической сортировки дерева построения.
            # Этими features могут быть, например, создание Точки в (0, 0, 0),
            # и эта точка должна быть скрыта, чтобы её случайно не выбрать и
            # не задействовать в построениях.
            self._config["rollback_points"] = {
                "<после эскизов>": [5, 85],
                "<после выдавливаний>": [25, 28, 31, 46, 26, 29, 32, 47, 50, 43, 74, 75, 78],
                "<после скруглений>": [34, 33],
                "<после массивов>": [48, 49, 38, 39, 40, 41],
            }
            config.save_delayed()

    def settings_widget(self) -> QtWidgets.QWidget:
        def _create_new_o3d_type_item(o3d_type: int = 0) -> QtGui.QStandardItem:
                o3d_type_item = QtGui.QStandardItem(get_text_o3d(o3d_type))
                o3d_type_item.setData(o3d_type, DATAROLE_O3D_TYPE)
                return o3d_type_item

        def _point_selection_changed() -> None:
            list_o3d_types.clear_items(is_silent=True)
            rb_point_item = list_rb_points.get_one_selected_item()
            if not rb_point_item is None:
                rb_point_name = rb_point_item.text()
                o3d_types = self._config["rollback_points"][rb_point_name]
                for o3d_type in o3d_types:
                    o3d_type_item = _create_new_o3d_type_item(o3d_type)
                    list_o3d_types.add_new_item(o3d_type_item, is_silent=True)

        def _list_o3d_types_changed() -> None:
            rb_point_item = list_rb_points.get_one_selected_item()
            o3d_types = [o3d_type_item.data(DATAROLE_O3D_TYPE) for o3d_type_item in list_o3d_types.iterate_items()]
            if not rb_point_item is None:
                rb_point_item.setData(o3d_types, DATAROLE_O3D_TYPES_ARRAY)
                _save_config()

        def _save_config() -> None:
            self._config["rollback_points"].clear()
            for rb_point_item in list_rb_points.iterate_items():
                name = rb_point_item.text()
                o3d_types = rb_point_item.data(DATAROLE_O3D_TYPES_ARRAY)
                self._config["rollback_points"][name] = o3d_types
            print(self._config["rollback_points"])
            config.save_delayed()

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        list_rb_points = gui_widgets.StringListSelector()

        for rb_point_name, o3d_types in self._config["rollback_points"].items():
            rb_point_item = QtGui.QStandardItem(rb_point_name)
            rb_point_item.setData(o3d_types, DATAROLE_O3D_TYPES_ARRAY)
            list_rb_points.add_new_item(rb_point_item, is_silent=True)

        o3d_delegate = O3DTypeDelegate()
        list_o3d_types = gui_widgets.StringListSelector(_create_new_o3d_type_item)
        list_o3d_types.view().setItemDelegate(o3d_delegate)

        lbl_msg = QtWidgets.QLabel(self._to_config_message)
        lbl_msg.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse \
            | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        l.addWidget(QtWidgets.QLabel("Названия целевых элементов дерева построения:"), 0, 0, 1, 2)
        l.addWidget(list_rb_points, 1, 0, 1, 1)
        l.addWidget(list_o3d_types, 1, 1, 1, 1)
        l.addWidget(lbl_msg, 2, 0, 1, 2)

        list_rb_points.clear_selection()

        list_o3d_types.list_changed.connect(_list_o3d_types_changed)
        list_rb_points.list_changed.connect(_save_config)
        list_rb_points.selection_changed.connect(_point_selection_changed)

        return w

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        def btn_move_toggle(state):
            if state == True:
                if not self.execute(f2_remember):
                    btn_move_features.setChecked(False)  # FIXME сразу же срабатывает этот же обработчик (ветка else)
            else:
                self.execute(f2_move)

        btn_autosort_tree = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/macros/autosort_tree.svg")), "")
        btn_autosort_tree.clicked.connect(lambda: self.execute(self._autosort_tree))
        btn_autosort_tree.setToolTip("Выстроить выбранные элементы дерева автоматически по порядку")

        btn_move_features = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/macros/manual_move_features.svg")), "")
        btn_move_features.setCheckable(True)
        btn_move_features.toggled.connect(btn_move_toggle)
        btn_move_features.setToolTip(
            "Реорганизовать элементы дерева построения вручную.\n"
            "Выбрать и нажать первый раз для запоминания объектов для переноса;\n"
            "выбрать один элемент и нажать второй раз --- для переноса перед указанным элементом.")

        return {
            "кнопка автоматического выстроения по порядку": btn_autosort_tree,
            "кнопка ручного переноса": btn_move_features,
        }

    def _autosort_tree(self) -> None:
        self._to_config_message = ""
        unspecified_features: list[KAPI5.ksFeature] = []

        selected_features: list[KAPI5.ksFeature] = get_selected_features5()
        specified_types = self._get_specified_o3d_types()
        for f in selected_features:
            if not f.type in specified_types:
                unspecified_features.append(f)

        if len(unspecified_features) != 0:
            for f in unspecified_features:
                msg += f"'{f.name}' - {get_text_o3d(f.type)}\n"

            self._to_config_message = \
                "Необходимо настроить, перед какими элементами дерева размещать следующие объекты:\n" \
                f"<code>{msg}</code>"

            self.show_warning(
                f"{self._to_config_message}"
                "Выполните настройки и запустите команду снова."
            )
            self.request_settings()
            return

        f1(selected_features, self._config["rollbac"])


    def _get_specified_o3d_types(self) -> set[int]:
        specified_types = set()
        for o3d_types in self._config["rollback_points"].values():
            for o3d_type in o3d_types:
                specified_types.add(o3d_type)
        return specified_types
