"""
Макрос для автоматизированного заполнения основной надписи по шаблону.

В графическом интерфейсе поддерживается список настраиваемых шаблонов основных
надписей. Поддерживается возможность вставить текущую дату.

Один из самых первых разработанных автором макросов, один из наиболее часто применяемых.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path

import datetime


class StampCellNumbers:
    Naimenovanie = 1
    Oboznachenie = 2
    Material = 3
    Litera0 = 40
    Litera1 = 41
    Litera2 = 42
    Massa = 5
    Masschtab = 6
    Predpriyatie = 9

    NachOtd_dolzhnost = 10

    Razrabotal = 110
    Proveril = 111
    TehControl = 112
    NachOtd = 113
    NormContr = 114
    Utverdil = 115

    Razrabotal_podp = 110 + 10
    Proveril_podp = 111 + 10
    TehControl_podp = 112 + 10
    NachOtd_podp = 113 + 10
    NormContr_podp = 114 + 10
    Utverdil_podp = 115 + 10

    Razrabotal_data = 110 + 20
    Proveril_data = 111 + 20
    TehControl_data = 112 + 20
    NachOtd_data = 113 + 20
    NormContr_data = 114 + 20
    Utverdil_data = 115 + 20

    SpravNomer = 24
    PervPrimen = 25



def format_date(date: datetime.date|None = None, fmt: str = "%d.%m.%y") -> str:
    """
        Для `31.12.90` используйте `%d.%m.%y`.

        Для `31.12.1990` используйте `%d.%m.%Y`.
    """
    if date is None:
        date = datetime.datetime.now()

    return date.strftime(fmt)


def stamp_numbers(max_number: int = 10000) -> None:
    """
    Заполняет все ячейки основных надписей всех листов в текущем графическом
    документе номерами этих ячеек.

    Позволяет выяснить, какой номер у определенной ячейки.
    """
    doc = open_doc2d()

    lss: KAPI7.ILayoutSheets = doc.LayoutSheets

    for i in range(lss.Count):
        ls: KAPI7.ILayoutSheet = lss.Item(i)

        stamp: KAPI7.IStamp = ls.Stamp

        for col_id in range(0, max_number):
            txt: KAPI7.IText = stamp.Text(col_id)
            txt.Str = f"{col_id}"

        stamp.Update()


def stamp(data: dict[int, str], sheet_number: int = 1) -> None:
    assert isinstance(data, dict)

    app: KAPI7.IApplication = get_app7()
    doc: KAPI7.IKompasDocument = app.ActiveDocument

    lss: KAPI7.ILayoutSheets = doc.LayoutSheets

    ls: KAPI7.ILayoutSheet = lss.ItemByNumber(sheet_number)

    stamp: KAPI7.IStamp = ls.Stamp

    for col_id, value in data.items():
        col_id = int(col_id)
        txt: KAPI7.IText = stamp.Text(col_id)
        txt.Str = str(value)

    stamp.Update()


def get_stamp_data(cell_number: int, doc: KAPI7.IKompasDocument2D|None = None) -> str:
    if doc is None:
        doc = KAPI7.IKompasDocument2D(app.ActiveDocument)

    lss: KAPI7.ILayoutSheets = doc.LayoutSheets
    ls: KAPI7.ILayoutSheet = lss.ItemByNumber(1)  # Самый первый лист
    stamp: KAPI7.IStamp = ls.Stamp

    txt: KAPI7.IText = stamp.Text(cell_number)
    return txt.Str


class TemplateKeywords:
    CurrentDate = "$$$current_date$$$"


class SpinBoxDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(
            self,
            parent: QtWidgets.QWidget,
            option: QtWidgets.QStyleOptionViewItem,
            index: QtCore.QModelIndex
            ) -> QtWidgets.QWidget:
        editor = QtWidgets.QSpinBox(parent)
        editor.setFrame(False)
        editor.setRange(-(10**9), 10**9)
        return editor

    def setEditorData(self, editor: QtWidgets.QSpinBox, index: QtCore.QModelIndex) -> None:
        value = int(index.model().data(index, QtCore.Qt.ItemDataRole.EditRole))
        editor.setValue(value)

    def setModelData(self, editor: QtWidgets.QSpinBox, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex) -> None:
        editor.interpretText()
        value = str(editor.value())
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        editor.setGeometry(option.rect)


class ValueEditDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(
            self,
            parent: QtWidgets.QWidget,
            option: QtWidgets.QStyleOptionViewItem,
            index: QtCore.QModelIndex
            ) -> QtWidgets.QWidget:
        editor = QtWidgets.QTextEdit(parent)
        # editor.setFrame(False)
        editor.setToolTip("Нажмите правой кнопкой мыши для дополнительных опций")
        editor.contextMenuEvent = lambda event: ValueEditDelegate._context_menu_event(editor, event)
        return editor

    def setEditorData(self, editor: QtWidgets.QTextEdit, index: QtCore.QModelIndex) -> None:
        value = index.model().data(index, QtCore.Qt.ItemDataRole.EditRole)
        editor.setPlainText(value)

    def setModelData(self, editor: QtWidgets.QTextEdit, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex) -> None:
        value = editor.toPlainText()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        editor.setGeometry(option.rect)

    @staticmethod
    def _context_menu_event(le: QtWidgets.QTextEdit, event: QtGui.QContextMenuEvent) -> None:
        menu = le.createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(QtGui.QIcon(get_resource_path("img/macros/calendar.svg")), "Вставить шаблон: текущая дата", lambda: le.setText(TemplateKeywords.CurrentDate))
        menu.exec(event.globalPos())


class StampTemplateWidget(QtWidgets.QWidget):
    data_changed = QtCore.pyqtSignal()
    fill_stamp_cell_numbers_requested = QtCore.pyqtSignal()

    def __init__(self, data: dict[str, str] = {}, parent = None) -> None:
        super().__init__(parent)

        self._lbl_info_img = gui_widgets.LabelImage(get_resource_path("img/macros/dwg_cell_numbers.png"), self)
        self._lbl_info_img.setWindowFlags(QtCore.Qt.WindowType.Window)
        self._lbl_info_img.setWindowTitle(f"Номера ячеек основной надписи - {config.PROGRAM_NAME}")

        self._view = QtWidgets.QTableView()

        self._model = QtGui.QStandardItemModel()
        self._model.dataChanged.connect(lambda: self.data_changed.emit())
        self._view.setModel(self._model)

        self._view.verticalHeader().setHidden(True)

        self._view.horizontalHeader().setStretchLastSection(True)
        self._model.setHorizontalHeaderLabels([
            "№ ячейки",
            "значение",
        ])

        self._delegate0 = SpinBoxDelegate()
        self._delegate1 = ValueEditDelegate()

        self._view.setItemDelegateForColumn(0, self._delegate0)
        self._view.setItemDelegateForColumn(1, self._delegate1)


        self._btn_add = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/add.svg")), "")
        self._btn_add.setToolTip("Добавить")
        self._btn_add.clicked.connect(self.add_item)

        self._btn_delete = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/delete.svg")), "")
        self._btn_delete.setToolTip("Удалить")
        self._btn_delete.clicked.connect(self.delete_selected)

        self._btn_info = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/information.svg")), "Номера ячеек")
        self._btn_info.setToolTip(
            "Показать номера ячеек в основной надписи\n"
            "первого листа конструкторских чертежей"
        )
        self._btn_info.clicked.connect(self.show_info)

        self._btn_fill_stamp_numbers = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/macros/stamp_go.svg")), "Узнать номера ячеек")
        self._btn_fill_stamp_numbers.setToolTip(
            "Заполнить в текущем документе все ячейки\n"
            "основных надписей всех листов текущего документа"
        )
        self._btn_fill_stamp_numbers.clicked.connect(self.request_fill_stamp_cell_numbers)

        self._layout_btn = QtWidgets.QHBoxLayout()
        self._layout_btn.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self._layout_btn.setContentsMargins(0, 0, 0, 0)
        self._layout_btn.addWidget(self._btn_add)
        self._layout_btn.addWidget(self._btn_delete)
        self._layout_btn.addWidget(self._btn_info)
        self._layout_btn.addWidget(self._btn_fill_stamp_numbers)

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._view)
        self._layout.addLayout(self._layout_btn)
        self.setLayout(self._layout)

        self.set_data(data)

    def set_data(self, data: dict[str, str]) -> None:
        self._model.removeRows(0, self._model.rowCount())
        i = 0
        for number, value in data.items():
            self._model.appendRow([
                QtGui.QStandardItem(str(number)),
                QtGui.QStandardItem(value),
            ])
            i += 1

    def get_data(self) -> dict[int, str]:
        data: dict[int, str] = {}
        for i in range(self._model.rowCount()):
            number = int(self._model.index(i, 0).data())
            value = self._model.index(i, 1).data()
            data[number] = value
        return data

    def add_item(self) -> None:
        self._model.appendRow([
            QtGui.QStandardItem("0"),
            QtGui.QStandardItem("текст"),
        ])
        self.data_changed.emit()

    def delete_selected(self) -> None:
        selected: list[QtCore.QModelIndex] = self._view.selectedIndexes()
        if len(selected) == 0:
            return

        root = QtCore.QModelIndex()
        selected_row_indexes = sorted([i.row() for i in selected])

        deleted_count = 0
        for r in selected_row_indexes:
            self._model.removeRow(r - deleted_count, root)
            deleted_count += 1

        self.data_changed.emit()

    def show_info(self) -> None:
        self._lbl_info_img.show()
        gui_widgets.move_to_screen_center(self._lbl_info_img)

    def request_fill_stamp_cell_numbers(self) -> None:
        btn = QtWidgets.QMessageBox.warning(
            self,
            "Внимание!",
            "Команда заполнит все возможные ячейки основной надписи в текущем графическом документе их номерами.\n\nВы уверены, что хотите продолжить?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel,
            QtWidgets.QMessageBox.StandardButton.Cancel,
        )
        if btn == QtWidgets.QMessageBox.StandardButton.Yes:
            self.fill_stamp_cell_numbers_requested.emit()



class MacrosStamp(Macros):
    DATA_ROLE_TEMPLATE_DATA = 0x100

    def __init__(self) -> None:
        super().__init__("stamp", "Основная надпись")

    def check_config(self) -> None:
        try:
            assert isinstance(self._config["date_format"], str)
        except Exception as e:
            self._config["date_format"] = "%d.%m.%y"

        try:
            assert isinstance(self._config["templates"], list)
            assert len(self._config["templates"]) > 0
            for name, template in self._config["templates"]:
                assert isinstance(name, str)
                assert isinstance(template, dict)
                for key, value in template.items():
                    assert isinstance(key, str)
                    assert isinstance(value, str)
        except Exception as e:
            self._config["templates"] = [
                ["Иванов", {
                    StampCellNumbers.Razrabotal: "Иванов",
                    StampCellNumbers.Proveril: "Петров",
                    StampCellNumbers.Utverdil: "Сидоров",
                }],
            ]

        try:
            assert isinstance(self._config["current_template"], int)
        except:
            self._config["current_template"] = 0

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        def _select_current_template() -> None:
            i = cmbx_stamp_template.currentIndex()
            if i >= len(self._config["templates"]):
                self.request_settings()
                if i > 0:
                    cmbx_stamp_template.setCurrentIndex(0)
            else:
                self._config["current_template"] = i
                config.save_delayed()

        btn_stamp_current_date = QtWidgets.QToolButton()
        btn_stamp_current_date.setIcon(QtGui.QIcon(get_resource_path("img/macros/stamp_date.svg")))
        btn_stamp_current_date.clicked.connect(self.fill_razrabotal_current_date)
        btn_stamp_current_date.setToolTip("Заполнить текущую дату в строке \"Разработал\"")

        cmbx_stamp_template = QtWidgets.QComboBox()

        for t in self._config["templates"]:
            t_name, t_data = t
            cmbx_stamp_template.addItem(t_name)
        cmbx_stamp_template.addItem(QtGui.QIcon(get_resource_path("img/settings.svg")), "Настроить...")

        if self._config["current_template"] < cmbx_stamp_template.count():
            cmbx_stamp_template.setCurrentIndex(self._config["current_template"])
        cmbx_stamp_template.setToolTip("Выбор шаблона заполнения основной надписи")
        cmbx_stamp_template.currentIndexChanged.connect(_select_current_template)

        btn_stamp = QtWidgets.QToolButton()
        btn_stamp.setIcon(QtGui.QIcon(get_resource_path("img/macros/stamp_go.svg")))
        btn_stamp.clicked.connect(self.fill_stamp_template)
        btn_stamp.setToolTip("Заполнить основную надпись по шаблону")

        return {
            "селектор шаблона": cmbx_stamp_template,
            "кнопка: заполнить по шаблону": btn_stamp,
            "кнопка: заполнить дату подписи разработчика": btn_stamp_current_date,
        }

    def settings_widget(self) -> QtWidgets.QWidget:
        def _apply_datetime_format(to_save = True):
            self._config["date_format"] = le_format.text()
            try:
                txt = today.strftime(self._config["date_format"])
            except:
                txt = "Ошибка"
            lbl_result.setText(txt)
            if to_save:
                config.save_delayed()

        def _save_list():
            self._config["templates"].clear()
            for item in template_selector.iterate_items():
                t_name = item.data(QtCore.Qt.ItemDataRole.DisplayRole)
                t_data = item.data(self.DATA_ROLE_TEMPLATE_DATA)
                t = [t_name, t_data]
                self._config["templates"].append(t)
            config.save_delayed()

        def _selection_changed() -> None:
            item = template_selector.get_one_selected_item()
            if not item is None:
                t_data = item.data(self.DATA_ROLE_TEMPLATE_DATA)
                stamp_template_widget.set_data(t_data)
            else:
                stamp_template_widget.set_data({})

        def _data_changed() -> None:
            item = template_selector.get_one_selected_item()
            if not item is None:
                item.setData(stamp_template_widget.get_data(), self.DATA_ROLE_TEMPLATE_DATA)
                _save_list()

        def _create_new_template() -> QtGui.QStandardItem:
            item = QtGui.QStandardItem()
            _set_item_data(item, ["Шаблон", {}])
            return item

        def _set_item_data(item: QtGui.QStandardItem, template) -> None:
            t_name, t_data = template
            item.setData(t_name, QtCore.Qt.ItemDataRole.DisplayRole)
            item.setData(t_data, self.DATA_ROLE_TEMPLATE_DATA)


        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        today = datetime.datetime.now()

        lbl_desc = QtWidgets.QLabel(
            "Формат даты:" \
            "<br><code>%d</code> - двузначный номер дня месяца (01...31)" \
            "<br><code>%m</code> - двузначный номер месяца (01...12)" \
            "<br><code>%y</code> - двузначный номер года (70)" \
            "<br><code>%Y</code> - четырехзначный номер года (1970)" \
        )
        lbl_desc.setWordWrap(True)

        lbl_result = QtWidgets.QLabel()
        lbl_result.setFont(gui_widgets.get_monospace_font())

        le_format = QtWidgets.QLineEdit(self._config["date_format"])
        le_format.setFont(gui_widgets.get_monospace_font())
        le_format.textChanged.connect(lambda: _apply_datetime_format())

        _apply_datetime_format(to_save=False)

        stamp_template_widget = StampTemplateWidget()
        stamp_template_widget.fill_stamp_cell_numbers_requested.connect(lambda: self.execute(stamp_numbers))

        template_selector = gui_widgets.StringListSelector(_create_new_template)
        for t in self._config["templates"]:
            item = _create_new_template()
            _set_item_data(item, t)
            template_selector.add_new_item(item)

        l.addWidget(lbl_desc, 0, 0, 1, 3)
        l.addWidget(le_format, 1, 0, 1, 2)
        l.addWidget(lbl_result, 1, 2, 1, 1)

        l.addWidget(template_selector, 2, 0, 1, 1)
        l.addWidget(stamp_template_widget, 2, 1, 1, 2)

        template_selector.clear_selection()

        stamp_template_widget.data_changed.connect(_data_changed)
        template_selector.selection_changed.connect(_selection_changed)
        template_selector.list_changed.connect(lambda: self.toolbar_update_requested.emit(False))
        template_selector.list_changed.connect(_save_list)

        return w

    def fill_razrabotal_current_date(self):
        self.execute(
            lambda: stamp({
                StampCellNumbers.Razrabotal_data: format_date(fmt=self._config["date_format"]),
            })
        )

    def fill_stamp_template(self) -> None:
        def _fill_stamp_template():
            t_name, t_data = self._get_current_template()

            stamp_data = {}
            for key in t_data:
                stamp_data[key] = t_data[key].replace(TemplateKeywords.CurrentDate, format_date(fmt = self._config["date_format"]))

            stamp(stamp_data)
        self.execute(_fill_stamp_template)

    def _get_current_template(self):
        if len(self._config["templates"]) == 0:
            raise Exception("Нет ни одного шаблона основной надписи")
        if not (0 <= self._config["current_template"] < len(self._config["templates"])):
            raise Exception(f"Некорректный индекс выбранного шаблона: {self._config["current_template"]}")
        return self._config["templates"][self._config["current_template"]]


if __name__ == "__main__":

    app = QtWidgets.QApplication([])

    m = MacrosStamp()
    m.check_config()

    w = m.settings_widget()

    w.show()

    app.exec()

    exit()

    stamp({
        StampCellNumbers.Razrabotal: "Иванов",
        StampCellNumbers.Predpriyatie: "Университет\nКафедра\nГруппа",
        StampCellNumbers.Razrabotal_data: format_date(fmt="%d.%m.%Y"),
    })

