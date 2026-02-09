"""
Главный модуль графического интерфейса приложения.

Здесь описаны классы главного окна, панели инструментов, окна настроек.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

import typing
import traceback
import sys

from .. import config

from ..utils.resources import get_resource_path
from ..utils.delayed_handler import DelayedHandler

from . import widgets as gui_widgets
from .settings import SettingsWindow
from .toolbar import ToolBar, TOOLBAR_SEPARATOR_NAME


from ..macros_gui.MACROS_GUI import macroses, Macros, get_macros


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
        if event is not None:
            if self.lbl_settings.geometry().contains(event.pos()):
                menu = self.createPopupMenu()
                if not menu is None:
                    menu.exec(event.globalPos())
                    event.accept()
        return super().contextMenuEvent(event)

    def createPopupMenu(self) -> QtWidgets.QMenu | None:
        menu = super().createPopupMenu()
        if not menu is None:
            menu.addAction(QtGui.QIcon(get_resource_path("img/settings.svg")), "Настройки...", lambda: self.show_settings())
        return menu

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
                        macros: Macros = get_macros(m)  # next(filter(lambda el: el.code_name == m, macroses))
                        obj = macros.toolbar_widgets()[w]
                        tb.add_object(m, w, obj)
                    except Exception as e:
                        tb_spec["contents"].pop(i)
                        print(f"Ошибка: {e.__class__.__name__}: {e}")
                        print(f'У панели инструментов "{tb_spec["name"]}" виджет "{m}/{w}" не будет отображен.')
                        # print(traceback.format_exc())
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
