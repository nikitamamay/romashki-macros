"""
Главный модуль графического интерфейса приложения.

Здесь описаны классы главного окна, окна и виджета настроек.

"""


from src.resources import get_resource_path

from PyQt5 import QtCore, QtGui, QtWidgets

import typing

from src.delayed_handler import DelayedHandler
from src import config

from src.macros import macroses, Macros, get_macros

from src import gui_widgets



class InterfaceCustomizationWidget(QtWidgets.QWidget):
    icon_size_changed = QtCore.pyqtSignal()
    widgets_changed = QtCore.pyqtSignal()
    stays_on_top_changed = QtCore.pyqtSignal()

    ITEM_ROLE_MACROS_CODENAME = 0x0100
    ITEM_ROLE_TOOLBAR_WIDGET_CODENAME = 0x0101

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint, False)

        self.cb_show_all_toolbar_widgets = QtWidgets.QCheckBox("Всегда выводить виджеты всех макросов на панель")
        self.cb_show_all_toolbar_widgets.setChecked(config.interface()["show_all_toolbar_widgets"])
        self.cb_show_all_toolbar_widgets.stateChanged.connect(lambda: self.set_cb_show_all_toolbar_widgets())

        self.cb_stays_on_top = QtWidgets.QCheckBox("Показывать окно поверх всех окон")
        self.cb_stays_on_top.setChecked(config.interface()["stays_on_top"])

        self.sb_icon_size = QtWidgets.QSpinBox(self)
        self.sb_icon_size.setRange(0, 10*9)
        self.sb_icon_size.setValue(config.get_icon_size())
        self.sb_icon_size.valueChanged.connect(self.set_icon_size)

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
        self._layout_2.addWidget(self.view_available, 0, 0, 1, 1)
        self._layout_2.addWidget(self.btn_add, 1, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
        self._layout_2.addWidget(self.view_displayed, 0, 1, 2, 1)

        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(self.cb_stays_on_top, 0, 0, 1, 2)
        self._layout.addWidget(QtWidgets.QLabel("Размер иконок:"), 1, 0)
        self._layout.addWidget(self.sb_icon_size, 1, 1)
        self._layout.addWidget(self.cb_show_all_toolbar_widgets, 2, 0, 1, 2)
        self._layout.addLayout(self._layout_2, 3, 0, 1, 2)
        self._layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self._layout)

        self.model_available = QtGui.QStandardItemModel()
        self.view_available.setModel(self.model_available)

        self.init_displayed_widgets()
        self.init_available_widgets()

        self.set_cb_show_all_toolbar_widgets(True)
        self.cb_stays_on_top.stateChanged.connect(self.set_stays_on_top)

        self.view_displayed.list_changed.connect(self.displayed_widgets_list_changed)

    def _set_displayed_widget_item_data(self, item, m_name, w_name) -> None:
        macros = get_macros(m_name)
        text = f'{macros.full_name} / {w_name}'
        widget = macros.toolbar_widgets()[w_name]

        if isinstance(widget, QtWidgets.QAbstractButton):
            item.setIcon(widget.icon())
        item.setData(text, QtCore.Qt.ItemDataRole.DisplayRole)
        item.setData(text, QtCore.Qt.ItemDataRole.ToolTipRole)
        item.setData(m_name, self.ITEM_ROLE_MACROS_CODENAME)
        item.setData(w_name, self.ITEM_ROLE_TOOLBAR_WIDGET_CODENAME)

    def init_displayed_widgets(self) -> None:
        self.view_displayed.clear_items()
        for m_name, w_name in config.toolbar_widgets():
            item = QtGui.QStandardItem()
            self._set_displayed_widget_item_data(item, m_name, w_name)
            self.view_displayed.add_new_item(item, True, True)

    def init_available_widgets(self) -> None:
        self.model_available.clear()
        for macros in macroses:
            item_directory = QtGui.QStandardItem(macros.full_name)
            self.model_available.appendRow(item_directory)
            for w_name, widget in macros.toolbar_widgets().items():
                item = QtGui.QStandardItem()
                if isinstance(widget, QtWidgets.QAbstractButton):
                    item.setIcon(widget.icon())
                item.setData(w_name, QtCore.Qt.ItemDataRole.DisplayRole)
                item.setData(w_name, QtCore.Qt.ItemDataRole.ToolTipRole)
                item.setData(macros.code_name, self.ITEM_ROLE_MACROS_CODENAME)
                item.setData(w_name, self.ITEM_ROLE_TOOLBAR_WIDGET_CODENAME)
                item_directory.appendRow(item)

    def displayed_widgets_list_changed(self) -> None:
        tw = config.toolbar_widgets()
        tw.clear()
        for item in self.view_displayed.iterate_items():
            m_name = item.data(self.ITEM_ROLE_MACROS_CODENAME)
            w_name = item.data(self.ITEM_ROLE_TOOLBAR_WIDGET_CODENAME)
            tw.append([m_name, w_name])

        self.widgets_changed.emit()
        config.save_delayed()

    def add_widget(self) -> None:
        selected: list[QtCore.QModelIndex] = self.view_available.selectedIndexes()
        if len(selected) == 0:
            return

        index = selected[0]

        if not index.parent().isValid():  # if selected is top-level
            # или добавлять все виджеты данного макроса?
            return

        m_name = index.data(self.ITEM_ROLE_MACROS_CODENAME)
        w_name = index.data(self.ITEM_ROLE_TOOLBAR_WIDGET_CODENAME)

        item = QtGui.QStandardItem()
        self._set_displayed_widget_item_data(item, m_name, w_name)
        self.view_displayed.add_new_item(item)

        # self.widgets_changed.emit()  # вызывается из-за self.view_displayed.list_changed.emit()

    def set_icon_size(self, size: int) -> None:
        config.set_icon_size(size)
        self.icon_size_changed.emit()
        config.save()

    def set_stays_on_top(self) -> None:
        config.interface()["stays_on_top"] = self.cb_stays_on_top.isChecked()
        self.stays_on_top_changed.emit()
        config.save()

    def set_cb_show_all_toolbar_widgets(self, is_silent: bool = False) -> None:
        to_show = self.cb_show_all_toolbar_widgets.isChecked()
        config.interface()["show_all_toolbar_widgets"] = to_show

        self.btn_add.setEnabled(not to_show)
        self.view_displayed.setEnabled(not to_show)
        self.view_available.setEnabled(not to_show)

        if not is_silent:
            self.widgets_changed.emit()
            config.save()



class SettingsWindow(QtWidgets.QWidget):
    ITEM_ROLE_SECTION_INDEX = 0x0100
    ITEM_ROLE_MACROS_CODENAME = 0x0101
    SECTION_INDEX_OFFSET = 100
    SECTION_INTERFACE = 1

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

        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(self.view_sections, 0, 0, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setLayout(self._layout)

        self.init_sections()

    def init_sections(self) -> None:
        self.model_sections.clear()
        item = QtGui.QStandardItem("Интерфейс")
        item.setData(self.SECTION_INTERFACE, self.ITEM_ROLE_SECTION_INDEX)
        item.setData("", self.ITEM_ROLE_MACROS_CODENAME)
        self.model_sections.appendRow(item)

        i = 0
        for macros in macroses:
            item = QtGui.QStandardItem(f'Макрос «{macros.full_name}»')
            item.setData(self.SECTION_INDEX_OFFSET + i, self.ITEM_ROLE_SECTION_INDEX)
            item.setData(macros.code_name, self.ITEM_ROLE_MACROS_CODENAME)
            self.model_sections.appendRow(item)
            i += 1

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

        elif i >= self.SECTION_INDEX_OFFSET:
            i -= self.SECTION_INDEX_OFFSET
            macros: Macros = macroses[i]
            w = macros.settings_widget()

        else:
            raise Exception(f"Bad section index: {i}")

        w.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self._layout.addWidget(w, 0, 1)

    def hideEvent(self, a0: QtGui.QHideEvent) -> None:
        super().hideEvent(a0)
        self.event_hided.emit()

    def open_macros_page(self, macros_codename: str = "") -> None:
        for i in range(self.model_sections.rowCount()):
            index = self.model_sections.index(i, 0)
            if index.data(self.ITEM_ROLE_MACROS_CODENAME) == macros_codename:
                self.view_sections.selectionModel().clearSelection()
                self.view_sections.selectionModel().select(
                    index,
                    QtCore.QItemSelectionModel.SelectionFlag.Select
                )
                self.changed_section()
                return



class MainWindow(QtWidgets.QMainWindow):
    _init_toolbar_signal = QtCore.pyqtSignal()  # сделан для корректной обработки многопоточности с DelayedHandler

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self._toolbar_widgets = []

        self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint, False)

        self.btn_settings = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/settings.svg")), "")
        self.btn_settings.setToolTip("Настройки")
        self.btn_settings.clicked.connect(self.show_settings)

        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)

        self._toolbar_layout = QtWidgets.QHBoxLayout()
        self._toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self._toolbar_layout.setSpacing(1)
        self._toolbar_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)

        self.init_toolbar()

        self._layout = QtWidgets.QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(1)
        self._layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        self._layout.addLayout(self._toolbar_layout)
        self._layout.addStretch(1)
        self._layout.addWidget(self.btn_settings, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self.main_widget.setLayout(self._layout)

        self.settings_window = SettingsWindow(self)
        self.settings_window.setWindowFlag(QtCore.Qt.WindowType.Window, True)
        self.settings_window.icw.widgets_changed.connect(self.init_toolbar)
        self.settings_window.icw.icon_size_changed.connect(self.init_toolbar)
        self.settings_window.icw.stays_on_top_changed.connect(self.apply_stays_on_top)
        self.settings_window.event_hided.connect(self.init_toolbar)

        self.apply_stays_on_top()

        for m in macroses:
            m.set_parent_widget(self)
            m.settings_requested.connect(self.show_settings)
            m.toolbar_update_requested.connect(self._toolbar_init_requested)


        self._dh = DelayedHandler()
        self._init_toolbar_task_id = self._dh.create_task(
            self._init_toolbar_signal.emit,
            5.0
        )
        self._init_toolbar_signal.connect(self.init_toolbar)

        self.resize(1, 1)  # сделать окно минимального размера
        self.move_to_screen_center()

    def show_settings(self, macros_code_name: str = "") -> None:
        s = QtWidgets.qApp.primaryScreen().size()
        w = self.settings_window.width()
        h = self.settings_window.height()
        self.settings_window.move((s.width() - w) // 2, (s.height() - h) // 2)
        self.settings_window.show()
        self.settings_window.open_macros_page(macros_code_name)

    def init_toolbar(self) -> None:
        policy_default = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        size = QtCore.QSize(config.get_icon_size(), config.get_icon_size())

        def _add_widget(widget, policy=policy_default) -> None:
            self._toolbar_layout.addWidget(widget)
            if isinstance(widget, (QtWidgets.QAbstractButton)):
                widget.setIconSize(size)
            widget.setSizePolicy(policy)

        self.clear_toolbar()

        if config.interface()["show_all_toolbar_widgets"]:
            widgets = self.get_all_toolbar_widgets()
        else:
            widgets = config.toolbar_widgets()

        i = 0
        while i < len(widgets):
            m, w = widgets[i]
            try:
                macros: Macros = next(filter(lambda el: el.code_name == m, macroses))
                widget = macros.toolbar_widgets()[w]
                self._toolbar_widgets.append(widget)
                _add_widget(widget)
                i += 1
            except Exception as e:
                widgets.pop(i)
                QtWidgets.QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"{str(e)}<br>Виджет <code>{m}/{w}</code> не будет отображен.",
                )
                config.save_delayed()

        s = config.get_icon_size()
        size = QtCore.QSize(s, s)
        for i in range(0, self._toolbar_layout.count()):
            widget = self._toolbar_layout.itemAt(i).widget()
            if isinstance(widget, QtWidgets.QAbstractButton):
                widget.setIconSize(size)
            if isinstance(widget, QtWidgets.QComboBox):
                widget.setIconSize(size)

        self.resize(10, 10)

    def clear_toolbar(self) -> None:
        for i in range(self._toolbar_layout.count()):
            li = self._toolbar_layout.takeAt(0)
            w = li.widget()
            w.deleteLater()

    def apply_stays_on_top(self) -> None:
        self.setWindowFlag(
            QtCore.Qt.WindowType.WindowStaysOnTopHint,
            config.interface()["stays_on_top"]
        )
        self.show()

    def get_all_toolbar_widgets(self) -> list[list[str, str]]:
        l = []
        for m in macroses:
            l.extend([[m.code_name, w] for w in m.toolbar_widgets().keys()])
        return l

    def move_to_screen_center(self) -> None:
        s_size = QtWidgets.qApp.primaryScreen().size()
        self.move(
            int(s_size.width() / 2 - self.width() / 2),
            int(s_size.height() / 2 - self.height() / 2)
        )

    def _toolbar_init_requested(self, is_immediate: bool = True):
        if is_immediate:
            self.init_toolbar()
        else:
            self._dh.do_task(self._init_toolbar_task_id)



if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    w = MainWindow()
    w.show()

    app.exec()
