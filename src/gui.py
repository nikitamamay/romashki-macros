"""
Главный модуль графического интерфейса приложения.

Здесь описаны классы главного окна, панели инструментов, окна настроек.

"""

from src.resources import get_resource_path

from PyQt5 import QtCore, QtGui, QtWidgets

import typing
import traceback
import sys

from src.delayed_handler import DelayedHandler
from src import config
from src.macros import macroses, Macros, get_macros
from src import gui_widgets
from src.gui_settings_interface import *
from src.gui_settings_general import *


class SettingsWindow(QtWidgets.QWidget):
    ITEM_ROLE_SECTION_INDEX = 0x0100
    ITEM_ROLE_PAGE_CODENAME = 0x0101

    SECTION_INDEX_OFFSET = 100
    SECTION_INTERFACE = 1
    SECTION_GENERAL = 2

    SECTION_INTERFACE_S = "$$$interface$$$"
    SECTION_GENERAL_S = "$$$general$$$"

    event_hided = QtCore.pyqtSignal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.resize(900, 400)

        self.setWindowTitle(f"Настройки - {config.PROGRAM_NAME}")

        self.model_sections = QtGui.QStandardItemModel()

        self.view_sections = QtWidgets.QListView()
        self.view_sections.setModel(self.model_sections)
        self.view_sections.clicked.connect(self.changed_section)
        self.view_sections.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Expanding
        )

        self.icw = InterfaceCustomizationWidget()

        self.gsw = GeneralSettingsWidget()

        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(self.view_sections, 0, 0, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setLayout(self._layout)

        self.init_sections()

    def init_sections(self) -> None:
        self.model_sections.clear()

        sections = [
            ["Общие настройки", self.SECTION_GENERAL, self.ITEM_ROLE_PAGE_CODENAME],
            ["Интерфейс", self.SECTION_INTERFACE, self.SECTION_INTERFACE_S],
        ]

        for i, macros in enumerate(macroses):
            sections.append([f'Макрос «{macros.full_name}»', self.SECTION_INDEX_OFFSET + i, self.ITEM_ROLE_PAGE_CODENAME])

        for name, index, codename in sections:
            item = QtGui.QStandardItem(name)
            item.setData(index, self.ITEM_ROLE_SECTION_INDEX)
            item.setData(codename, self.ITEM_ROLE_PAGE_CODENAME)
            self.model_sections.appendRow(item)

    def changed_section(self) -> None:
        selected: list[QtCore.QModelIndex] = self.view_sections.selectedIndexes()
        if len(selected) == 0:
            i = self.SECTION_INTERFACE
        else:
            i = selected[0].data(self.ITEM_ROLE_SECTION_INDEX)

        item = self._layout.itemAtPosition(0, 1)
        if not item is None:
            w = item.widget()
            self._layout.removeWidget(w)
            w.setParent(None)

        if i == self.SECTION_INTERFACE:
            w = self.icw

        elif i == self.SECTION_GENERAL:
            w = self.gsw

        elif i >= self.SECTION_INDEX_OFFSET:
            i -= self.SECTION_INDEX_OFFSET
            macros: Macros = macroses[i]
            w = macros.settings_widget()

        else:
            raise Exception(f"Bad section index: {i}")

        w.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        l = w.layout()
        if not l is None:
            l.setContentsMargins(5,0,0,0)
        self._layout.addWidget(w, 0, 1)

    def hideEvent(self, a0: QtGui.QHideEvent) -> None:
        super().hideEvent(a0)
        self.event_hided.emit()

    def open_page(self, page_codename: str = "") -> None:
        if page_codename != "":
            for i in range(self.model_sections.rowCount()):
                index = self.model_sections.index(i, 0)
                if index.data(self.ITEM_ROLE_PAGE_CODENAME) == page_codename:
                    self.view_sections.selectionModel().clearSelection()
                    self.view_sections.selectionModel().select(
                        index,
                        QtCore.QItemSelectionModel.SelectionFlag.Select
                    )
                    self.changed_section()
                    return


class ToolBar(QtWidgets.QToolBar):
    move_event = QtCore.pyqtSignal()
    hide_event = QtCore.pyqtSignal()

    def __init__(self, title: str, parent = None):
        super().__init__(title, parent)
        self._contents: list[tuple[str, str]] = []

    def moveEvent(self, a0: QtGui.QMoveEvent | None) -> None:
        self.move_event.emit()
        return super().moveEvent(a0)

    def hideEvent(self, a0: QtGui.QHideEvent | None) -> None:
        self.hide_event.emit()
        return super().hideEvent(a0)

    def add_object(self, macros_codename: str, widget_codename: str, obj: QtWidgets.QWidget|QtWidgets.QAction|None) -> None:
        self._contents.append([macros_codename, widget_codename])
        if macros_codename == TOOLBAR_SEPARATOR_NAME:
            self.addSeparator()
        elif isinstance(obj, QtWidgets.QWidget):
            self.addWidget(obj)
        elif isinstance(obj, QtWidgets.QAction):
            self.addAction(obj)
        else:
            raise Exception(f"Unsupported element type: ({(macros_codename, widget_codename, obj)})")

    def get_contents(self) -> list[tuple[str, str]]:
        return self._contents


class MainWindow(QtWidgets.QMainWindow):
    TOOLBAR_AREA = QtCore.Qt.ToolBarArea.TopToolBarArea
    TOOLBAR_WRAP_WIDTH = 800

    # сделано для корректной обработки многопоточности с DelayedHandler
    _init_toolbar_signal = QtCore.pyqtSignal()
    _save_toolbars_order_signal = QtCore.pyqtSignal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(300, 20)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint, False)

        self._toolbars: list[QtWidgets.QToolBar] = []

        self.lbl_settings = QtWidgets.QLabel("< ПКМ для перехода в настройки >")
        self.lbl_settings.sizeHint = lambda: QtCore.QSize(0, 0)
        self.lbl_settings.minimumSizeHint = lambda: QtCore.QSize(0, 0)
        self.lbl_settings.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(self.lbl_settings)

        self.settings_window = SettingsWindow(self)
        self.settings_window.setWindowFlag(QtCore.Qt.WindowType.Window, True)
        self.settings_window.event_hided.connect(self.init_toolbars)

        self.settings_window.icw.widgets_changed.connect(self.init_toolbars)
        self.settings_window.icw.toolbars_reset.connect(self.wrap_toolbars)
        self.settings_window.icw.icon_size_changed.connect(self.init_toolbars)
        self.settings_window.icw.stays_on_top_changed.connect(self.apply_stays_on_top)

        self.settings_window.gsw.config_reset_requested.connect(self.reset_app_config)

        for m in macroses:
            m.set_parent_widget(self)
            m.settings_requested.connect(self.show_settings)
            m.toolbar_update_requested.connect(self._toolbar_init_requested)


        self._dh = DelayedHandler()
        self._init_toolbar_task_id = self._dh.create_task(
            self._init_toolbar_signal.emit,
            5.0
        )
        self._save_toolbars_order_task_id = self._dh.create_task(
            self._save_toolbars_order_signal.emit,
            5.0
        )
        self._init_toolbar_signal.connect(self.init_toolbars)
        self._save_toolbars_order_signal.connect(self.save_toolbars_order)

        self.init_toolbars()
        self.apply_stays_on_top()

        self.resize(self.sizeHint())  # сделать окно минимального размера
        gui_widgets.move_to_screen_center(self)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent | None) -> None:
        if self.centralWidget().geometry().contains(event.pos()):
            menu = QtWidgets.QMenu("Контекстное меню")
            menu.addAction(QtGui.QIcon(get_resource_path("img/settings.svg")), "Настройки", lambda: self.show_settings())
            menu.exec(event.globalPos())
            event.accept()
        return super().contextMenuEvent(event)

    def show_settings(self, macros_code_name: str = "") -> None:
        gui_widgets.move_to_screen_center(self.settings_window)
        self.settings_window.show()
        self.settings_window.open_page(macros_code_name)

    def init_toolbars(self) -> None:
        icon_size = QtCore.QSize(config.get_icon_size(), config.get_icon_size())

        for tb in self._toolbars:
            self.removeToolBar(tb)
        self._toolbars.clear()

        for tb_spec in config.toolbars():
            tb = ToolBar(tb_spec["name"], self)
            tb.setAllowedAreas(self.TOOLBAR_AREA)
            tb.setFloatable(False)
            tb.setHidden(tb_spec["is_hidden"])
            tb.setIconSize(icon_size)

            if tb_spec["has_break_before"]:
                self.addToolBarBreak(self.TOOLBAR_AREA)
            self.addToolBar(tb)
            self._toolbars.append(tb)

            i = 0
            while i < len(tb_spec["contents"]):
                m, w = tb_spec["contents"][i]

                if m == TOOLBAR_SEPARATOR_NAME:
                    tb.add_object(m, w, None)
                else:
                    try:
                        macros: Macros = next(filter(lambda el: el.code_name == m, macroses))
                        obj = macros.toolbar_widgets()[w]
                        tb.add_object(m, w, obj)
                    except Exception as e:
                        tb_spec["contents"].pop(i)
                        print(f'У панели инструментов "{tb_spec["name"]}" виджет "{m}/{w}" не будет отображен.')
                        print(traceback.format_exc())
                        config.save_delayed()
                        continue
                i += 1

        for tb in self._toolbars:
            tb.hide_event.connect(lambda: self._dh.do_task(self._save_toolbars_order_task_id))
            tb.move_event.connect(lambda: self._dh.do_task(self._save_toolbars_order_task_id))

    def save_toolbars_order(self) -> None:
        config.toolbars().clear()
        for tb in sorted(self._toolbars, key=lambda tb: tb.pos().x() + tb.pos().y() * 10000):
            tb_spec = {
                "name": tb.windowTitle(),
                "has_break_before": self.toolBarBreak(tb),
                "is_hidden": tb.isHidden(),
                "contents": tb.get_contents(),
            }
            config.toolbars().append(tb_spec)
        config.save_delayed()

    def wrap_toolbars(self) -> None:
        width = 0
        for tb in self._toolbars:  # sorted(self._toolbars, key=lambda tb: tb.pos().x() + tb.pos().y() * 10000):
            width += tb.sizeHint().width()
            if width > self.TOOLBAR_WRAP_WIDTH:
                self.insertToolBarBreak(tb)
                width = 0
        self.resize(self.sizeHint())  # сделать окно минимального размера
        gui_widgets.move_to_screen_center(self)
        self.save_toolbars_order()

    def apply_stays_on_top(self) -> None:
        self.setWindowFlag(
            QtCore.Qt.WindowType.WindowStaysOnTopHint,
            config.interface()["stays_on_top"]
        )
        self.show()

    def _toolbar_init_requested(self, is_immediate: bool = True):
        if is_immediate:
            self.init_toolbars()
        else:
            self._dh.do_task(self._init_toolbar_task_id)

    def closeEvent(self, a0: QtGui.QCloseEvent | None) -> None:
        self.save_toolbars_order()
        config.save()
        return super().closeEvent(a0)

    def reset_app_config(self) -> None:
        config.cr.reset_config()
        sys.exit(0)



if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    w = MainWindow()
    w.show()

    app.exec()
