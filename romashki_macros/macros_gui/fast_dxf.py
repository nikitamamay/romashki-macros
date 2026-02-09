
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config

from ..gui import widgets as gui_widgets
from ..gui.macros import Macros

from ..utils import math_utils

from ..utils.resources import get_resource_path

from ..macros.fast_dxf import *

import traceback


class MacrosFastDXF(Macros):
    def __init__(self) -> None:
        super().__init__("fast_dxf", "Быстрое создание DXF")

    def check_config(self) -> None:
        try:
            assert isinstance(self._config["do_rename_selected_view_to_DXF"], bool)
        except:
            self._config["do_rename_selected_view_to_DXF"] = False

        try:
            assert isinstance(self._config["filename_template"], str)
        except:
            self._config["filename_template"] = f"S={TEMPLATE_KEYWORD_THICKNESS} {TEMPLATE_KEYWORD_MARKING} {TEMPLATE_KEYWORD_NAME}"


    def settings_widget(self) -> QtWidgets.QWidget:
        def _apply_changes():
            self._config["do_rename_selected_view_to_DXF"] = cb_do_rename_view_in_dwg.isChecked()
            self._config["filename_template"] = le_filename_fmt.text()
            _show_filename_example()
            config.save_delayed()

        def _show_filename_example():
            fp = get_dxf_path(self._config["filename_template"], "./", 2.5, "АБВГ.000.001", "Пластина")
            lbl_filename_example.setText(fp)

        def _context_menu_event(le: QtWidgets.QLineEdit, event: QtGui.QContextMenuEvent) -> None:
            menu = le.createStandardContextMenu()
            if menu is None: raise Exception("No menu")
            menu.addSeparator()
            menu.addAction("Вставить шаблон: Наименование", lambda: le.insert(TEMPLATE_KEYWORD_NAME))
            menu.addAction("Вставить шаблон: Обозначение", lambda: le.insert(TEMPLATE_KEYWORD_MARKING))
            menu.addAction("Вставить шаблон: Толщина", lambda: le.insert(TEMPLATE_KEYWORD_THICKNESS))
            menu.exec(event.globalPos())
            event.accept()

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        le_filename_fmt = QtWidgets.QLineEdit(self._config["filename_template"])
        le_filename_fmt.contextMenuEvent = lambda ev: _context_menu_event(le_filename_fmt, ev)
        le_filename_fmt.setFont(gui_widgets.get_monospace_font())
        le_filename_fmt.setToolTip("Нажмите правой кнопкой мыши для дополнительных опций")
        le_filename_fmt.textEdited.connect(_apply_changes)

        lbl_filename_example = QtWidgets.QLabel()
        lbl_filename_example.setFont(gui_widgets.get_monospace_font())
        lbl_filename_example.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        lbl_filename_example.setToolTip("Пример имени файла")

        cb_do_rename_view_in_dwg = QtWidgets.QCheckBox(f"При создании DXF-фрагмента из 2D-чертежа присваивать выбранному виду название '{FASTDXF_DWG_VIEW_NAME}'")
        cb_do_rename_view_in_dwg.setChecked(self._config["do_rename_selected_view_to_DXF"])
        cb_do_rename_view_in_dwg.stateChanged.connect(_apply_changes)

        l.addWidget(QtWidgets.QLabel("Шаблон имени файла: "), 0, 0, 1, 1)
        l.addWidget(le_filename_fmt, 0, 1, 1, 1)
        l.addWidget(lbl_filename_example, 1, 1, 1, 1)
        l.addWidget(cb_do_rename_view_in_dwg, 2, 0, 1, 2)

        _show_filename_example()

        return w

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        btn_main_projection = QtWidgets.QToolButton()
        btn_main_projection.setIcon(QtGui.QIcon(get_resource_path("img/macros/main_projection.svg")))
        btn_main_projection.setToolTip("Создать/обновить ориентацию главного вида в открытой модели")
        btn_main_projection.clicked.connect(lambda: self.execute(self._create_main_projection))

        btn_dxf_from_part = QtWidgets.QToolButton()
        btn_dxf_from_part.setIcon(QtGui.QIcon(get_resource_path("img/macros/dxf_from_part.svg")))
        btn_dxf_from_part.setToolTip("Создать DXF для открытой детали")
        btn_dxf_from_part.clicked.connect(lambda: self.execute(lambda: create_DXF_from_part(self._config["filename_template"])))

        btn_dxf_from_dwg = QtWidgets.QToolButton()
        btn_dxf_from_dwg.setIcon(QtGui.QIcon(get_resource_path("img/macros/dxf_from_dwg.svg")))
        btn_dxf_from_dwg.setToolTip(f"Создать DXF из вида \"{FASTDXF_DWG_VIEW_NAME}\" в открытом чертеже")
        btn_dxf_from_dwg.clicked.connect(lambda: self.execute(lambda: create_DXF_from_dwg(self._config["filename_template"], self._config["do_rename_selected_view_to_DXF"])))

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

