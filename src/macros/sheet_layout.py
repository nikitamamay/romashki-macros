"""
Макрос для работы с оформлением листа чертежа.

Макрос предоставляет функционал:
* выбор формата листа от A0 до A5 и смена ориентации листа (портретная/альбомная).

    Этот функционал актуален для старых версий Компаса со старым интерфейсом,
    в котором нет возможности сменить формат листа за один клик мыши, а нужно
    заходить в отдельный менеджер документа и менять там.

* применение оформления основной надписи из lyt-библиотеки.

    Этот функционал полезен, если основная надпись чертежа как-то изменена
    под требования на предприятии. Например, в правой нижней чейке не просто
    прописано название предприятия, а вставлено какое-то изображение.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path



def set_sheets_layout_library(lib_filepath: str) -> None:
    """
        Изменяет стили оформления всех листов, на имеющиеся в библиотеке по пути `lib_filepath`.
        Номера стилей сохраняются теми же. Следовательно, номера стилей должны быть такими же,
        как и в стандартной библиотеке `graphic.lyt`.

        При `lib_filepath = ""` устанавливается стандартное обозначение из библиотеки `graphic.lyt`.
    """

    iKompasObject5, iKompasObject7 = get_kompas_objects()

    doc2d: KAPI7.IKompasDocument2D = open_doc2d()
    lss: KAPI7.ILayoutSheets = doc2d.LayoutSheets


    for i in range(lss.Count):
        ls: KAPI7.ILayoutSheet = lss.Item(i)
        ls.LayoutLibraryFileName = lib_filepath
        ls.Update()


def get_sheet_format(sheet_index: int = 0) -> tuple[int, bool]:
    """
        Возвращает формат и ориентацию листа
        с индексом (не номером) `sheet_index` у текущего документа.

        Формат может принимать значения `0...5` для A0...A5 соответственно
        и `6` для пользовательского (нестандартного) формата.
    """
    doc2d: KAPI7.IKompasDocument2D = open_doc2d()
    lss: KAPI7.ILayoutSheets = doc2d.LayoutSheets

    if sheet_index > lss.Count - 1:
        raise Exception("индекс листа задан больше, чем листов документе")
    if sheet_index < 0:
        raise Exception("задан отрицательный индекс")

    ls: KAPI7.ILayoutSheet = lss.Item(sheet_index)
    f: KAPI7.ISheetFormat = ls.Format

    return (f.Format, f.VerticalOrientation)


def set_sheet_format(format_number: int, is_vertical: bool, sheet_index: int = 0):
    """
        Изменяет у текущего документа формат и ориентацию листа
        с индексом (не номером) `sheet_index`.

        `format_number` может принимать значения `0...5` для A0...A5 соответственно.
    """
    doc2d: KAPI7.IKompasDocument2D = open_doc2d()
    lss: KAPI7.ILayoutSheets = doc2d.LayoutSheets

    if sheet_index > lss.Count - 1:
        raise Exception("индекс листа задан больше, чем листов документе")
    if sheet_index < 0:
        raise Exception("задан отрицательный индекс")

    ls: KAPI7.ILayoutSheet = lss.Item(sheet_index)
    f: KAPI7.ISheetFormat = ls.Format

    f.Format = format_number
    f.VerticalOrientation = is_vertical

    ls.Update()




class MacrosSheetLayout(Macros):
    def __init__(self) -> None:
        super().__init__("sheet_layout", "Оформление чертежа")

    def check_config(self) -> None:
        try:
            assert isinstance(self._config["lib_path"], str)
        except:
            self._config["lib_path"] = ""
            config.save_delayed()

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        def _get_apply_format_function(i: int):
            return lambda: self.execute(lambda: self.apply_sheet_format(i))

        btn_format = QtWidgets.QToolButton()
        btn_format.setIcon(QtGui.QIcon(get_resource_path("img/macros/sheet_format.svg")))
        btn_format.setToolTip("Выбор формата листа 2D-документа")
        btn_format.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        menu_format = QtWidgets.QMenu("Выбор формата листа 2D-документа")
        for i in range(6):
            fmt = f"A{i}"
            action = QtWidgets.QAction(fmt, btn_format)
            action.triggered.connect(_get_apply_format_function(i))
            menu_format.addAction(action)
        btn_format.setMenu(menu_format)

        btn_orientation = QtWidgets.QToolButton()
        btn_orientation.setIcon(QtGui.QIcon(get_resource_path("img/macros/sheet_orientation.svg")))
        btn_orientation.clicked.connect(lambda: self.execute(self.switch_sheet_orientation))
        btn_orientation.setToolTip("Сменить ориентацию формата листа")

        btn_layout = QtWidgets.QToolButton()
        btn_layout.setIcon(QtGui.QIcon(get_resource_path("img/macros/sheet_layout.svg")))
        btn_layout.clicked.connect(lambda: self.execute(self.apply_lib_layout))
        btn_layout.setToolTip("Применить оформление из библиотеки")

        return {
            "селектор формата листа": btn_format,
            "кнопка: сменить ориентацию формата листа": btn_orientation,
            "кнопка: применить оформление из библиотеки": btn_layout,
        }

    def settings_widget(self) -> QtWidgets.QWidget:
        def get_new() -> None:
            ext_filter = "Библиотека оформлений (*.lyt)"
            lib_path, filter_ = QtWidgets.QFileDialog.getOpenFileName(
                self._parent_widget,
                "Выбрать библиотеку оформления чертежей",
                "",
                f"{ext_filter};;Все файлы (*)",
                ext_filter,
            )
            if lib_path != "":
                self._config["lib_path"] = lib_path
                le_lib_path.setText(self._config["lib_path"])

        def reset() -> None:
            self._config["lib_path"] = ""
            le_lib_path.setText(self._config["lib_path"])

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        le_lib_path = QtWidgets.QLineEdit(self._config["lib_path"])
        le_lib_path.setReadOnly(True)

        btn_choose = QtWidgets.QPushButton("Выбрать...")
        btn_choose.clicked.connect(get_new)

        btn_clear = QtWidgets.QPushButton("Вернуть стандартное")
        btn_clear.clicked.connect(reset)

        l.addWidget(QtWidgets.QLabel("Путь к библиотеке оформления:"), 0, 0, 1, 2)
        l.addWidget(le_lib_path, 1, 0, 1, 2)
        l.addWidget(btn_choose, 2, 0, 1, 1)
        l.addWidget(btn_clear, 2, 1, 1, 1)

        return w

    def apply_lib_layout(self) -> None:
        set_sheets_layout_library(self._config["lib_path"])

    def apply_sheet_format(self, fmt: int) -> None:
        sheet_index = 0
        old_fmt, is_vertical = get_sheet_format(sheet_index)
        set_sheet_format(fmt, is_vertical, sheet_index)

    def switch_sheet_orientation(self) -> None:
        sheet_index = 0
        old_fmt, is_vertical = get_sheet_format(sheet_index)
        is_vertical = not is_vertical
        set_sheet_format(old_fmt, is_vertical, sheet_index)




if __name__ == "__main__":
    # set_sheets_layout_library("")

    set_sheet_format(1, False)
