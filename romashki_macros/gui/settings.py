"""
Модуль окна настроек приложения и макросов.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from .. import PROGRAM_NAME
from ..utils.resources import get_resource_path
from .widgets import StringListSelector
from .settings_general import GeneralSettingsWidget
from .settings_interface import InterfaceCustomizationWidget


from ..macros_gui.MACROS_GUI import macroses, Macros, get_macros


class SettingsWindow(QtWidgets.QWidget):
    ITEM_ROLE_SECTION_INDEX = 0x0100
    ITEM_ROLE_PAGE_CODENAME = 0x0101

    SECTION_INDEX_OFFSET = 100
    SECTION_INTERFACE = 1
    SECTION_GENERAL = 2

    SECTION_INTERFACE_S = "$$$interface$$$"
    SECTION_GENERAL_S = "$$$general$$$"

    PAGE_WIDGET_POS_ROW = 1
    PAGE_WIDGET_POS_COLUMN = 1

    event_hided = QtCore.pyqtSignal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.resize(900, 500)

        self.setWindowTitle(f"Настройки - {PROGRAM_NAME}")

        self.model_sections = QtGui.QStandardItemModel()

        self.view_sections = StringListSelector()
        self.view_sections.set_read_only()
        self.view_sections.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.view_sections.set_single_selecting_only(True)
        self.view_sections.selection_changed.connect(self.section_changed)

        self.label_title = QtWidgets.QLabel()
        f = self.label_title.font()
        f.setPointSize(round(f.pointSize() * 1.5))
        f.setBold(True)
        self.label_title.setFont(f)

        self.icw = InterfaceCustomizationWidget()

        self.gsw = GeneralSettingsWidget()

        self._layout = QtWidgets.QGridLayout()
        self._layout.addWidget(self.view_sections, 0, 0, 2, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self._layout.addWidget(self.label_title, 0, 1, 1, 1, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self._layout)

        self._init_sections()

        self.view_sections.select_single_row(0)

    def _init_sections(self) -> None:
        sections = [
            ["Общие настройки", self.SECTION_GENERAL, self.SECTION_GENERAL_S],
            ["Интерфейс", self.SECTION_INTERFACE, self.SECTION_INTERFACE_S],
        ]

        for i, macros in enumerate(macroses):
            sections.append([f'Макрос «{macros.full_name}»', self.SECTION_INDEX_OFFSET + i, macros.code_name])

        for name, index, codename in sections:
            item = QtGui.QStandardItem()
            item.setData(name, QtCore.Qt.ItemDataRole.DisplayRole)
            item.setData(name, QtCore.Qt.ItemDataRole.ToolTipRole)
            item.setData(index, self.ITEM_ROLE_SECTION_INDEX)
            item.setData(codename, self.ITEM_ROLE_PAGE_CODENAME)
            self.view_sections.add_new_item(item, True, True)

    def section_changed(self) -> None:
        item_page = self.view_sections.get_one_selected_item()

        if item_page is None:
            return

        i = item_page.data(self.ITEM_ROLE_SECTION_INDEX)

        layout_item = self._layout.itemAtPosition(self.PAGE_WIDGET_POS_ROW, self.PAGE_WIDGET_POS_COLUMN)
        if not layout_item is None:
            w = layout_item.widget()
            assert w is not None
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
        self._layout.addWidget(w, self.PAGE_WIDGET_POS_ROW, self.PAGE_WIDGET_POS_COLUMN, 1, 1)

        self.label_title.setText(item_page.data(QtCore.Qt.ItemDataRole.DisplayRole))

    def hideEvent(self, a0: QtGui.QHideEvent) -> None:
        super().hideEvent(a0)
        self.event_hided.emit()

    def open_page(self, page_codename: str = "") -> None:
        if page_codename != "":
            for item in self.view_sections.iterate_items():
                if item.data(self.ITEM_ROLE_PAGE_CODENAME) == page_codename:
                    self.view_sections.select_single_item(item)