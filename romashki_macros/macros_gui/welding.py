"""
Модуль графического интерфейса макроса `welding`.

Графический интерфейс позволяет:
* создавать сварные швые (ломаные линии и твердые тела сразу) по шаблону;
* создавать только ломаные линий швов;
* создавать твердые тела швов по ранее созданным ломаным линиям;
* удалять построения тел швов;
* настраивать:
    * опцию создания сварных швов в текущей модели или в отдельной;
    * опцию запрета на удаление сварных швов в других моделях;
    * префикс имени построений;
    * сечение условного валика шва;
    * список шаблонов размеров условного валика шва и слоя в 3D-модели.

"""
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config
from ..utils import config_reader

from ..gui import widgets as gui_widgets
from ..gui.macros import Macros

from ..utils.resources import get_resource_path
import re

from ..macros.welding import *


re_weld_spec_name = re.compile(r'^◺\d+[\.\,]?\d*$|◺\d+[\.\,]?\d* слой \d+$')


class WeldSpecInputWidget(QtWidgets.QWidget):
    data_edited = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self._sb_diameter = gui_widgets.SpinBox()
        # self._sb_diameter.setPrefix("⌀")
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
        config_reader.ensure_dict_value(self.config(), "prefix", str, RMWELD)
        config_reader.ensure_dict_value(self.config(), "do_create_in_active_document", bool, True)
        config_reader.ensure_dict_value(self.config(), "do_remove_in_weldpart_only", bool, True)
        config_reader.ensure_dict_value(self.config(), "section_edges_count", int, 8)

        config_reader.ensure_dict_value_list(
            self.config(), "weld_specs", list,
            lambda spec: config_reader.isinstance_for_list_values(spec, [str, (float, int), int]))
        if len(self.config()["weld_specs"]) == 0:
            self.config()["weld_specs"].append(["◺5", 10.0, -1])

        config_reader.ensure_dict_value(self.config(), "active_weld_spec", int, 0)

    def settings_widget(self) -> QtWidgets.QWidget:
        def _apply_changes() -> None:
            self.config()["prefix"] = le_prefix.text()
            self.config()["do_create_in_active_document"] = cb_use_active_model.isChecked()
            self.config()["do_remove_in_weldpart_only"] = cb_do_remove_in_weldpart_only.isChecked()
            self.config()["section_edges_count"] = sb_section_edges_count.value()
            config.save_delayed()
            if self.config()["do_create_in_active_document"]:
                self._welddoc_path = ""
            _update_widgets()

        def _apply_list_changes() -> None:
            self.config()["weld_specs"].clear()
            for item in weld_specs_list.iterate_items():
                name: str = item.data(QtCore.Qt.ItemDataRole.DisplayRole)
                diameter: float = item.data(self.DATAROLE_DIAMETER)
                layer: int = item.data(self.DATAROLE_LAYER)
                self.config()["weld_specs"].append([name, diameter, layer])

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
                if re_weld_spec_name.match(name):
                    s_layer = f" слой {layer}" if layer != -1 else ""
                    name = f"◺{math_utils.round_tail_str(diam / 2)}{s_layer}"
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

        def _update_widgets() -> None:
            s_model = "в активной" if self.config()["do_create_in_active_document"] else "во вспомогательной"
            cb_do_remove_in_weldpart_only.setText(f"Разрешить удаление сварных швов только {s_model} модели")

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        cb_use_active_model = QtWidgets.QCheckBox("Создавать построения в активной модели, а не во вспомогательной")
        cb_use_active_model.setChecked(self.config()["do_create_in_active_document"])
        cb_use_active_model.stateChanged.connect(_apply_changes)

        cb_do_remove_in_weldpart_only = QtWidgets.QCheckBox(f"Разрешить удаление сварных швов только в {0} модели")
        cb_do_remove_in_weldpart_only.setChecked(self.config()["do_remove_in_weldpart_only"])
        cb_do_remove_in_weldpart_only.stateChanged.connect(_apply_changes)

        sb_section_edges_count = QtWidgets.QSpinBox()
        sb_section_edges_count.setRange(0, 1000)
        sb_section_edges_count.setValue(self.config()["section_edges_count"])
        sb_section_edges_count.valueChanged.connect(_apply_changes)

        le_prefix = QtWidgets.QLineEdit(self.config()["prefix"])
        le_prefix.setPlaceholderText(RMWELD)
        le_prefix.textChanged.connect(_apply_changes)

        weld_specs_list = gui_widgets.StringListSelector(_create_new_weld_spec)
        for m in self.config()["weld_specs"]:
            name, diam, layer = m
            item = QtGui.QStandardItem()
            _set_item_data(item, name, diam, layer)
            weld_specs_list.add_new_item(item)

        wsip = WeldSpecInputWidget()

        l.addWidget(cb_use_active_model, 0, 0, 1, 2)
        l.addWidget(cb_do_remove_in_weldpart_only, 1, 0, 1, 2)
        l.addWidget(QtWidgets.QLabel("Префикс для наименований построений и тел:"), 2, 0, 1, 1)
        l.addWidget(le_prefix, 2, 1, 1, 2)

        l.addWidget(QtWidgets.QLabel("Количество сторон многоугольника в сечении шва:"), 3, 0, 1, 1)
        l.addWidget(sb_section_edges_count, 3, 1, 1, 1)
        l.addWidget(gui_widgets.ToolTipWidget(
            "При значении '0' будет использоваться окружность\n"
            "в качестве сечения валика шва.\n\n"
            "Рекомендуется использовать 8-гранники\n"
            "для более корректного проецирования в чертежи."
            ), 3, 2, 1, 1)

        l.addWidget(weld_specs_list, 4, 0, 1, 3)
        l.addWidget(wsip, 5, 0, 1, 3)

        wsip.data_edited.connect(_weld_spec_data_changed)
        weld_specs_list.selection_changed.connect(_selection_changed)
        weld_specs_list.list_changed.connect(lambda: self.toolbar_update_requested.emit(False))
        weld_specs_list.list_changed.connect(lambda: _apply_list_changes())

        weld_specs_list.clear_selection()

        _update_widgets()

        return w

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        def _select_active_weld_spec() -> None:
            i = cmbx_weld_specs.currentIndex()
            if i >= len(self.config()["weld_specs"]):
                self.request_settings()
                if i > 0:
                    cmbx_weld_specs.setCurrentIndex(0)
            else:
                self.config()["active_weld_spec"] = i
                config.save_delayed()

        cmbx_weld_specs = QtWidgets.QComboBox()

        for t in self.config()["weld_specs"]:
            name, diam, layer = t
            cmbx_weld_specs.addItem(name)
        cmbx_weld_specs.addItem(QtGui.QIcon(get_resource_path("img/settings.svg")), "Настроить...")
        cmbx_weld_specs.setIconSize(QtCore.QSize(16, 16))

        if self.config()["active_weld_spec"] < cmbx_weld_specs.count():
            cmbx_weld_specs.setCurrentIndex(self.config()["active_weld_spec"])
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

        btn_delete_welds = QtWidgets.QToolButton()
        btn_delete_welds.setIcon(QtGui.QIcon(get_resource_path("img/macros/weld_delete.svg")))
        btn_delete_welds.clicked.connect(lambda: self.execute(self._remove_welds))
        btn_delete_welds.setToolTip("Удалить сварные швы\nпо выбранным элементам")

        return {
            "селектор выбора параметров сварного шва": cmbx_weld_specs,
            "кнопка создания сварных швов": btn_create_weld,
            "кнопка создания ломаных линий швов": btn_create_lines,
            "кнопка создания твердых тел швов": btn_create_bodies,
            "кнопка удаления швов": btn_delete_welds,
        }

    def _check_for_weldpart(self) -> bool:
        if self.config()["do_create_in_active_document"]:
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
        create_welds(self._welddoc_path, wls, False, self.config()["prefix"])

    def _create_welds_lines(self) -> None:
        if not self._check_for_weldpart(): return
        wls = self._get_active_spec()
        create_welds(self._welddoc_path, wls, True, self.config()["prefix"])

    def _create_welds_bodies(self) -> None:
        if not self._check_for_weldpart(): return
        wls = self._get_active_spec()
        find_and_create_weld_bodies(self._welddoc_path, wls, True, self.config()["prefix"])

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
        if len(self.config()["weld_specs"]) == 0:
            self.request_settings()
            raise Exception("Нет ни одного шаблона сварных швов")

        if not (0 <= self.config()["active_weld_spec"] < len(self.config()["weld_specs"])):
            raise Exception(f"Некорректный индекс выбранного шаблона сварного шва: {self.config()["active_weld_spec"]}")

        name, diameter, layer = self.config()["weld_specs"][self.config()["active_weld_spec"]]
        wls = WeldLineSettings(diameter, layer, self.config()["section_edges_count"])
        return wls

    def _remove_welds(self) -> None:
        if not self._check_for_weldpart(): return
        remove_welds(self.config()["prefix"], self.config()["do_remove_in_weldpart_only"], self._welddoc_path)



