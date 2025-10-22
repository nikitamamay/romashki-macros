"""
Макрос предназначен для работы с определенным образом созданными моделями
рукавов высокого давления.

Модели рукавов представляют собой сборку из двух заранее смоделированных
фитингов; сплайна, эскиза окружности и кинематической операции (операции по
траектории), которая моделирует тело рукава.

Макрос предоставляет функционал:
* для изменения диаметра окружности, представляющей собой наружный диаметр РВД,
* для изменения толщины стенки кинематической операции (операции по траектории)
    с этой окружностью.

Макрос актуален для старой версии Компаса без библиотеки "Гибкие шланги".

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path


import traceback



def set_sketch_circle_diameter(diameter: float) -> None:
    doc, toppart = open_part()

    sketches: list[KAPI7.ISketch] = get_selected(doc, KAPI7.ISketch)

    for sketch in sketches:
        doc2d: KAPI7.IFragmentDocument = sketch.BeginEdit()
        view: KAPI7.IView = doc2d.ViewsAndLayersManager.Views.View(0)
        dc: KAPI7.IDrawingContainer = KAPI7.IDrawingContainer(view)
        circles: list[KAPI7.ICircle] = ensure_list(dc.Objects(2))  #  Окружность
        if len(circles) == 1:
            circles[0].Radius = diameter / 2
            circles[0].Update()

        sketch.EndEdit()


def set_evolution_wall_thickness(thickness: float) -> None:
    assert isinstance(thickness, (float, int))
    doc5, toppart5 = open_part_K5()
    selected = get_selected_K5(doc5)
    for entity in selected:
        if entity.type == LDefin3D.o3d_bossEvolution:
            base_evolution: KAPI5.ksBaseEvolutionDefinition = entity.GetDefinition()
            # base_evolution.SetThinParam(True, 1, thickness, thickness)
            tp: KAPI5.ksThinParam = base_evolution.ThinParam()
            tp.normalThickness = thickness
            tp.reverseThickness = thickness
            tp.thinType = 1
            tp.thin = True  # FIXME не_срабатывает с первого раза. Почему?
            entity.Update()
    doc5.RebuildDocument()



class RVDSizeInputWidget(QtWidgets.QWidget):
    data_edited = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self._sb_D = gui_widgets.SpinBox()
        self._sb_D.setPrefix("⌀")
        self._sb_D.valueChanged.connect(lambda: self.data_edited.emit())

        self._sb_d = gui_widgets.SpinBox()
        self._sb_d.setPrefix("⌀")
        self._sb_d.valueChanged.connect(lambda: self.data_edited.emit())

        self._layout = QtWidgets.QGridLayout()
        self._layout.setContentsMargins(0,0,0,0)
        self._layout.addWidget(QtWidgets.QLabel("Диаметр наружный"), 0, 0, 1, 1)
        self._layout.addWidget(self._sb_D, 0, 1, 1, 1)
        self._layout.addWidget(QtWidgets.QLabel("Диаметр внутренний"), 1, 0, 1, 1)
        self._layout.addWidget(self._sb_d, 1, 1, 1, 1)
        self.setLayout(self._layout)

    def set_data(self, D: float, d: float) -> None:
        self._sb_D.setValue(D)
        self._sb_d.setValue(d)

    def get_data(self) -> tuple[float, float]:
        return self._sb_D.value(), self._sb_d.value()

    def clear(self) -> None:
        self.set_data(0, 0)


class FastRVDMacros(Macros):
    DATAROLE_D_MAJOR = 101
    DATAROLE_D_MINOR = 102

    def __init__(self) -> None:
        super().__init__(
            "fast_rvd",
            "РВД"
        )

    def check_config(self) -> None:
        try:
            assert isinstance(self._config["rvd_sizes"], list)
            for el in self._config["rvd_sizes"]:
                assert isinstance(el, (list, tuple))
                assert len(el) == 2
                D, d = el
                assert isinstance(D, float)
                assert isinstance(d, float)
        except:
            self._config["rvd_sizes"] = [
                [15.0, 6.4],
                [16.6, 7.9],
                [19.0, 9.5],
                [22.2, 12.7],
                [25.4, 15.9],
                [29.3, 19.1],
                [37.2, 25.4],
            ]
            config.save_delayed()

    def settings_widget(self) -> QtWidgets.QWidget:
        def _save_list() -> None:
            self._config["rvd_sizes"].clear()
            for item in rvd_sizes_list.iterate_items():
                D: float = item.data(self.DATAROLE_D_MAJOR)
                d: float = item.data(self.DATAROLE_D_MINOR)
                self._config["rvd_sizes"].append([D, d])
            config.save_delayed()

        def _set_item_data(item: QtGui.QStandardItem, D: float, d: float) -> None:
            item.setData(f"⌀{d} / ⌀{D}", QtCore.Qt.ItemDataRole.DisplayRole)
            item.setData(D, self.DATAROLE_D_MAJOR)
            item.setData(d, self.DATAROLE_D_MINOR)

        def _create_new_size() -> QtGui.QStandardItem:
            item = QtGui.QStandardItem()
            D, d = 16, 8
            _set_item_data(item, D, d)
            return item

        def _rvd_size_data_changed() -> None:
            D, d = siw.get_data()
            item = rvd_sizes_list.get_one_selected_item()
            if not item is None:
                _set_item_data(item, D, d)
                _save_list()

        def _selection_changed() -> None:
            item = rvd_sizes_list.get_one_selected_item()
            if not item is None:
                siw.setEnabled(True)
                D = item.data(self.DATAROLE_D_MAJOR)
                d = item.data(self.DATAROLE_D_MINOR)
                siw.set_data(D, d)
            else:
                siw.setEnabled(False)
                siw.clear()

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        rvd_sizes_list = gui_widgets.StringListSelector(_create_new_size)
        for m in self._config["rvd_sizes"]:
            D, d = m
            item = QtGui.QStandardItem()
            _set_item_data(item, D, d)
            rvd_sizes_list.add_new_item(item)

        siw = RVDSizeInputWidget()

        l.addWidget(rvd_sizes_list, 0, 0, 1, 1)
        l.addWidget(siw, 1, 0, 1, 1)

        siw.data_edited.connect(_rvd_size_data_changed)
        rvd_sizes_list.selection_changed.connect(_selection_changed)
        rvd_sizes_list.list_changed.connect(lambda: self.toolbar_update_requested.emit(False))
        rvd_sizes_list.list_changed.connect(lambda: _save_list())

        rvd_sizes_list.clear_selection()

        return w

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        def _apply_size(size_index: int) -> None:
            D, d = self._config["rvd_sizes"][size_index]
            t = (D - d) / 2
            self.execute(
                lambda: set_sketch_circle_diameter(D)
            )
            self.execute(
                lambda: set_evolution_wall_thickness(t)
            )

        btn_apply = gui_widgets.ButtonWithList(QtGui.QIcon(get_resource_path("img/macros/rvd.svg")), "")
        btn_apply.clicked.connect(lambda: self.execute(lambda: _apply_size(0)))
        btn_apply.setToolTip("Применить первый в списке размер РВД\nдля эскиза и кинематической операции")

        for i, m in enumerate(self._config["rvd_sizes"]):
            D, d = m
            name = f"⌀{d} / ⌀{D}"
            btn_apply.menu().addAction(name, (lambda i: lambda: _apply_size(i))(i))

        btn_apply.menu().addSeparator()

        btn_apply.menu().addAction(
            QtGui.QIcon(get_resource_path("img/settings.svg")),
            "Настроить список...",
            self.request_settings,
        )

        return {
            "кнопка применения размеров": btn_apply,
        }




if __name__ == "__main__":

    D = 16
    d = 7.9
    t = (D - d) / 2

    set_sketch_circle_diameter(D)
    set_evolution_wall_thickness(t)
