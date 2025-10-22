"""
Модуль графического интерфейса приложения.

Здесь описаны классы виджетов настроек интерфейса приложения.

"""

from src.resources import get_resource_path

from PyQt5 import QtCore, QtGui, QtWidgets

from src import config
from src.macros import macroses, Macros, get_macros
from src import gui_widgets

import typing


TOOLBAR_SEPARATOR_NAME = "$$$separator$$$"


class ToolBarEditWidget(QtWidgets.QWidget):
    data_edited = QtCore.pyqtSignal()

    ITEM_ROLE_TOOLBAR_ITEM_SPEC = 101

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self._tb_name: str = ""
        self._tb_is_hidden: bool = False
        self._tb_has_break_before: bool = False
        self._tb_contents: list = []

        self.view_available = QtWidgets.QTreeView(self)
        self.view_available.setHeaderHidden(True)
        self.view_available.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.view_available.doubleClicked.connect(lambda: self.add_widget())

        self.btn_add = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/add.svg")), "")
        self.btn_add.clicked.connect(self.add_widget)

        self.view_displayed = gui_widgets.StringListSelector()
        self.view_displayed.set_adding_allowed(False)
        self.view_displayed.set_duplicating_allowed(False)
        self.view_displayed.set_name_editing_allowed(False)

        self._layout_2 = QtWidgets.QGridLayout()
        self._layout_2.setContentsMargins(0, 0, 0, 0)
        self._layout_2.addWidget(self.view_available, 0, 0, 1, 1)
        self._layout_2.addWidget(self.btn_add, 1, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
        self._layout_2.addWidget(self.view_displayed, 0, 1, 2, 1)
        self.setLayout(self._layout_2)

        self.model_available = QtGui.QStandardItemModel()
        self.view_available.setModel(self.model_available)

        self.view_displayed.list_changed.connect(self.data_edited.emit)

        self.init_available_widgets()

    def clear(self) -> None:
        self.view_displayed.clear_items(True)

    def set_data(self, tb_data: dict) -> None:
        self._tb_name = tb_data["name"]
        self._tb_is_hidden = tb_data["is_hidden"]
        self._tb_has_break_before = tb_data["has_break_before"]
        self._tb_contents = tb_data["contents"].copy()
        self._init_displayed_widgets()

    def get_data(self) -> dict:
        tb_spec = {
            "name": self._tb_name,
            "is_hidden": self._tb_is_hidden,
            "has_break_before": self._tb_has_break_before,
            "contents": [],
        }
        for item in self.view_displayed.iterate_items():
            item_spec = item.data(self.ITEM_ROLE_TOOLBAR_ITEM_SPEC)
            tb_spec["contents"].append(item_spec)
        return tb_spec

    def init_available_widgets(self) -> None:
        self.model_available.clear()

        if True:
            item_directory = QtGui.QStandardItem("Элементы интерфейса")
            self.model_available.appendRow(item_directory)

            item_spec = [TOOLBAR_SEPARATOR_NAME, ""]
            item = QtGui.QStandardItem()
            item.setData("Разделитель", QtCore.Qt.ItemDataRole.DisplayRole)
            item.setData(item_spec, self.ITEM_ROLE_TOOLBAR_ITEM_SPEC)
            item_directory.appendRow(item)

        for macros in macroses:
            item_directory = QtGui.QStandardItem(macros.full_name)
            self.model_available.appendRow(item_directory)

            for w_name, obj in macros.toolbar_widgets().items():
                item_spec = [macros.code_name, w_name]
                item = QtGui.QStandardItem()
                if isinstance(obj, QtWidgets.QAbstractButton):
                    item.setIcon(obj.icon())
                if isinstance(obj, QtWidgets.QAction):
                    item.setIcon(obj.icon())
                item.setData(w_name, QtCore.Qt.ItemDataRole.DisplayRole)
                item.setData(w_name, QtCore.Qt.ItemDataRole.ToolTipRole)
                item.setData(item_spec, self.ITEM_ROLE_TOOLBAR_ITEM_SPEC)
                item_directory.appendRow(item)

    def _init_displayed_widgets(self) -> None:
        self.view_displayed.clear_items()
        for item_spec in self._tb_contents:
            self._add_item_to_displayed_widgets(item_spec, True)

    def _add_item_to_displayed_widgets(self, item_spec, is_silent: bool) -> None:
        item = QtGui.QStandardItem()
        item.setData(f"{item_spec[0]} / {item_spec[1]}", QtCore.Qt.ItemDataRole.DisplayRole)
        item.setData(f"{item_spec[0]} / {item_spec[1]}", QtCore.Qt.ItemDataRole.ToolTipRole)
        item.setData(item_spec, self.ITEM_ROLE_TOOLBAR_ITEM_SPEC)
        self.view_displayed.add_new_item(item, is_silent, True)

    def add_widget(self) -> None:
        selected: list[QtCore.QModelIndex] = self.view_available.selectedIndexes()
        if len(selected) == 0:
            return

        index = selected[0]

        if not index.parent().isValid():  # if selected is top-level
            rows_count = self.model_available.rowCount(index)
            for row in range(rows_count):
                child_index = index.child(row, 0)
                item_spec = child_index.data(self.ITEM_ROLE_TOOLBAR_ITEM_SPEC)
                self._add_item_to_displayed_widgets(item_spec, False)
            return

        item_spec = index.data(self.ITEM_ROLE_TOOLBAR_ITEM_SPEC)
        self._add_item_to_displayed_widgets(item_spec, False)


class InterfaceCustomizationWidget(QtWidgets.QWidget):
    icon_size_changed = QtCore.pyqtSignal()
    widgets_changed = QtCore.pyqtSignal()
    stays_on_top_changed = QtCore.pyqtSignal()
    toolbars_reset = QtCore.pyqtSignal()

    ITEM_ROLE_TOOLBAR_DATA = 0x0100

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint, False)

        self.cb_stays_on_top = QtWidgets.QCheckBox("Показывать окно поверх всех окон")
        self.cb_stays_on_top.setChecked(config.interface()["stays_on_top"])

        self.sb_icon_size = QtWidgets.QSpinBox(self)
        self.sb_icon_size.setRange(0, 10*9)
        self.sb_icon_size.setValue(config.get_icon_size())

        self.toolbar_selector = gui_widgets.StringListSelector(self._create_new_toolbar_item)
        self.toolbar_selector.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Expanding)

        self.toolbar_edit_widget = ToolBarEditWidget()

        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(self.cb_stays_on_top, 0, 0, 1, 3)
        self._layout.addWidget(QtWidgets.QLabel("Размер иконок:"), 1, 0, 1, 2)
        self._layout.addWidget(self.sb_icon_size, 1, 2, 1, 1)
        self._layout.addWidget(QtWidgets.QLabel("Панели инструментов:"), 2, 0, 1, 1)
        self._layout.addWidget(QtWidgets.QLabel("Команды панели инструментов:"), 2, 1, 1, 2)
        self._layout.addWidget(self.toolbar_selector, 3, 0, 1, 1)
        self._layout.addWidget(self.toolbar_edit_widget, 3, 1, 1, 2)
        self._layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self._layout)

        self.cb_stays_on_top.stateChanged.connect(self.set_stays_on_top)
        self.sb_icon_size.valueChanged.connect(self.set_icon_size)
        self.toolbar_selector.selection_changed.connect(self._toolbar_choosed)
        # self.toolbar_selector.list_changed.connect(self._toolbar_choosed)
        self.toolbar_selector.list_changed.connect(self._toolbars_changed)
        self.toolbar_edit_widget.data_edited.connect(self._toolbar_edited)

        config.set_after_config_reset_handler(self.reset_toolbars)

        self.init_toolbar_selector()
        self.toolbar_selector.clear_selection()

    def set_stays_on_top(self) -> None:
        config.interface()["stays_on_top"] = self.cb_stays_on_top.isChecked()
        self.stays_on_top_changed.emit()
        config.save()

    def set_icon_size(self, size: int) -> None:
        config.set_icon_size(size)
        self.icon_size_changed.emit()
        config.save()

    def init_toolbar_selector(self) -> None:
        self.toolbar_selector.clear_items(True)
        for tb_spec in config.toolbars():
            item = self._create_new_toolbar_item()
            item.setData(tb_spec["name"], QtCore.Qt.ItemDataRole.DisplayRole)
            item.setData(tb_spec, self.ITEM_ROLE_TOOLBAR_DATA)
            self.toolbar_selector.add_new_item(item, True, False)
        self.toolbar_selector.clear_selection()

    def reset_toolbars(self) -> None:
        config.toolbars().clear()
        for macros in macroses:
            tb_data = {
                "name": f"Панель «{macros.full_name}»",
                "has_break_before": False,
                "is_hidden": False,
                "contents": [[macros.code_name, w_name] for w_name in macros.toolbar_widgets().keys()],
            }
            config.toolbars().append(tb_data)
        self.init_toolbar_selector()
        self.widgets_changed.emit()
        self.toolbars_reset.emit()

    def _create_new_toolbar_item(self) -> QtGui.QStandardItem:
        toolbar_data = {
            "name": "Панель инструментов",
            "has_break_before": False,
            "is_hidden": False,
            "contents": [],
        }
        item = QtGui.QStandardItem(toolbar_data["name"])
        item.setData(toolbar_data, self.ITEM_ROLE_TOOLBAR_DATA)
        return item

    def _toolbars_changed(self) -> None:
        config.toolbars().clear()
        for item in self.toolbar_selector.iterate_items():
            tb_data = item.data(self.ITEM_ROLE_TOOLBAR_DATA)
            tb_data["name"] = item.data(QtCore.Qt.ItemDataRole.DisplayRole)
            config.toolbars().append(tb_data)
        config.save_delayed()
        self.widgets_changed.emit()

    def _toolbar_choosed(self) -> None:
        item = self.toolbar_selector.get_one_selected_item()
        if not item is None:
            tb_data = item.data(self.ITEM_ROLE_TOOLBAR_DATA)
            self.toolbar_edit_widget.set_data(tb_data)
            self.toolbar_edit_widget.setEnabled(True)
        else:
            self.toolbar_edit_widget.clear()
            self.toolbar_edit_widget.setEnabled(False)

    def _toolbar_edited(self) -> None:
        tb_data = self.toolbar_edit_widget.get_data()
        item = self.toolbar_selector.get_one_selected_item()
        item.setData(tb_data, self.ITEM_ROLE_TOOLBAR_DATA)
        self._toolbars_changed()



