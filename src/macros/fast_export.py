"""
Изначально макрос задумывался для возможности экспортировать текущий документ
в различные форматы: PNG, PDF, STEP.

Однако в работе наиболее часто этот макрос использовался для сохранения в PDF
при работе с чертежами.

По умолчанию макрос сохраняет PDF с тем же названием, что и текущий документ,
просто меняя расширение файла. Перезаписывает файл, если такой файл уже
существует на диске.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path


def split_path(path: str) -> tuple[str, str, str]:
    d, t = os.path.split(path)
    name, ext = os.path.splitext(t)
    return (d, name, ext)


def change_ext(path: str, new_ext: str) -> str:
    d, n, e = split_path(path)
    while new_ext.startswith("."):
        new_ext = new_ext[1:]
    return os.path.join(d, n + "." + new_ext)


def get_current_doc_path() -> str:
    try:
        iKompasObject5, iKompasObject7 = get_kompas_objects()
        app: KAPI7.IApplication = get_app7(iKompasObject7)
        doc: KAPI7.IKompasDocument = app.ActiveDocument

        assert not doc is None
        assert doc.Name != ""

        return doc.PathName
    except Exception as e:
        return ""


def save_as_png_2d(path: str) -> None:
    iKompasObject5, iKompasObject7 = get_kompas_objects()

    doc: KAPI5.ksDocument2D = iKompasObject5.ActiveDocument2D()
    if doc == None:
        raise Exception("Current Document is not a 2D document")

    rpar: KAPI5.ksRasterFormatParam = doc.RasterFormatParam()

    rpar.format = LDefin2D.FORMAT_PNG
    rpar.colorBPP = LDefin2D.BPP_COLOR_04
    rpar.greyScale = 0
    rpar.extResolution = 300  # dpi
    rpar.extScale = 1
    rpar.colorType = LDefin2D.BLACKWHITE
    rpar.onlyThinLine = 0
    # rpar.pages =
    # rpar.rangeIndex =
    # rpar.multiPageOutput =   # only for TIFF

    if not doc.SaveAsToRasterFormat(path, rpar):
        raise Exception("SaveAsToRasterFormat was not succeed")

    print(f"png 2D: Exported to \"{path}\"")


def save_as_png_3d(path: str) -> None:
    iKompasObject5, iKompasObject7 = get_kompas_objects()

    doc: KAPI5.ksDocument3D = iKompasObject5.ActiveDocument3D()
    if doc == None:
        raise Exception("Current Document is not a 3D document")

    part: KAPI5.ksPart = doc.GetPart(LDefin3D.pTop_Part)
    b, x1, y1, z1, x2, y2, z2 = part.GetGabarit(True, True)
    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1
    g_max = max(dx, dy, dz)

    DPI = 96
    scale = 3 * DPI / g_max

    # print(scale)

    rpar: KAPI5.ksRasterFormatParam = doc.RasterFormatParam()

    rpar.format = LDefin2D.FORMAT_PNG
    rpar.colorBPP = LDefin2D.BPP_COLOR_16
    rpar.greyScale = 0
    rpar.extResolution = DPI  # dpi
    rpar.extScale = scale
    rpar.colorType = LDefin2D.COLOROBJECT
    rpar.onlyThinLine = 0
    # rpar.pages =
    # rpar.rangeIndex =
    # rpar.multiPageOutput =   # only for TIFF

    if not doc.SaveAsToRasterFormat(path, rpar):
        raise Exception("SaveAsToRasterFormat was not succeed")

    print(f"png 3D: Exported to \"{path}\"")


def export_png_auto(path_png: str) -> None:
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app: KAPI7.IApplication = get_app7(iKompasObject7)
    active_doc: KAPI7.IKompasDocument = KAPI7.IKompasDocument2D(app.ActiveDocument)

    if active_doc:
        doc_type = get_document_type(active_doc)

        if doc_type == DocumentTypeEnum.type_2D:
            print("Current document type is 2D")
            save_as_png_2d(path_png)

        elif doc_type == DocumentTypeEnum.type_3D:
            print("Current document type is 3D")
            save_as_png_3d(path_png)

        else:
            raise Exception("Unsupported document type for PNG exporting")


def save_as(path: str) -> None:
    """
        По большей мере используется для сохранения в PDF
    """
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app: KAPI7.IApplication = get_app7(iKompasObject7)
    doc: KAPI7.IKompasDocument = app.ActiveDocument

    if doc == None:
        raise Exception("No current document")

    doc.SaveAs(path)

    print(f"save_as: Exported to \"{path}\"")




def export_step(path: str) -> None:
    """ Не работает в Компас v16. """
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    doc: KAPI5.ksDocument3D = iKompasObject5.ActiveDocument3D()
    if doc == None:
        raise Exception("Current Document is not a 3D document")

    apar: KAPI5.ksAdditionFormatParam = doc.AdditionFormatParam()

    apar.format = LDefin3D.format_STEP
    # apar.formatBinary =
    # apar.topolgyIncluded =


    for i in range(0, 28 + 1, 2):
        apar.SetObjectsOptions(i, False)

    ### Внимание! В файлах LDefin2D.py и LDefin3D.py констант ksD3ConverterOptionsEnum нет!
    apar.SetObjectsOptions(12, True)  # ksD3CODocumentProperties
    apar.SetObjectsOptions(0, True)  # ksD3COBodyes
    apar.SetObjectsOptions(28, True)  # ksD3COStyle

    if not doc.SaveAsToAdditionFormat(path, apar):
        raise Exception("SaveAsToAdditionFormat was not succeed")

    print(f"step: Exported to \"{path}\"")


class MacrosFastExport(Macros):
    def __init__(self) -> None:
        super().__init__("fast_export", "Быстрый экспорт")

    def check_config(self) -> None:
        try:
            assert "ask_if_rewrite" in self._config
            assert isinstance(self._config["ask_if_rewrite"], bool)
        except:
            self._config["ask_if_rewrite"] = False

        try:
            assert "always_ask_filepath" in self._config
            assert isinstance(self._config["always_ask_filepath"], bool)
        except:
            self._config["always_ask_filepath"] = False

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        btn_pdf = QtWidgets.QToolButton()
        btn_pdf.setIcon(QtGui.QIcon(get_resource_path("img/macros/doc_pdf.svg")))
        btn_pdf.setToolTip("Экспортировать в PDF\n(любой документ)")
        btn_pdf.clicked.connect(lambda: self.execute(self.export_pdf))

        btn_png = QtWidgets.QToolButton()
        btn_png.setIcon(QtGui.QIcon(get_resource_path("img/macros/doc_png.svg")))
        btn_png.setToolTip("Экспортировать в PNG\n(3D-модели и чертежи)")
        btn_png.clicked.connect(lambda: self.execute(self.export_png))

        btn_step = QtWidgets.QToolButton()
        btn_step.setIcon(QtGui.QIcon(get_resource_path("img/macros/doc_stp.svg")))
        btn_step.setToolTip("Экспортировать в STEP\n(только 3D-модели)")
        btn_step.clicked.connect(lambda: self.execute(self.export_step))

        return {
            "экспорт в PDF": btn_pdf,
            "экспорт в PNG": btn_png,
            "экспорт в STEP": btn_step,
        }

    def settings_widget(self) -> QtWidgets.QWidget:
        def _update_config():
            self._config["ask_if_rewrite"] = cb_ask_if_rewrite.isChecked()
            self._config["always_ask_filepath"] = cb_always_ask.isChecked()
            config.save_delayed()

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        cb_ask_if_rewrite = QtWidgets.QCheckBox("Спрашивать о перезаписи, если файл уже существует")
        cb_ask_if_rewrite.setChecked(self._config["ask_if_rewrite"])
        cb_ask_if_rewrite.stateChanged.connect(_update_config)

        cb_always_ask = QtWidgets.QCheckBox("Всегда спрашивать путь файла при экспорте")
        cb_always_ask.setChecked(self._config["always_ask_filepath"])
        cb_always_ask.stateChanged.connect(_update_config)

        l.addWidget(cb_ask_if_rewrite, 0, 0)
        l.addWidget(cb_always_ask, 1, 0)
        return w

    def export_pdf(self) -> None:
        path = self.get_save_path(["pdf"])
        if not path:
            print("Путь не выбран, отмена сохранения.")
            return
        save_as(path)

    def export_png(self) -> None:
        path = self.get_save_path(["png"])
        if not path:
            print("Путь не выбран, отмена сохранения.")
            return
        export_png_auto(path)

    def export_step(self) -> None:
        path = self.get_save_path(["stp", "step"])
        if not path:
            print("Путь не выбран, отмена сохранения.")
            return
        export_step(path)

    def get_save_path(self, exts: list[str], force_ask_path: bool = False) -> str:
        ext = exts[0]
        current_doc_path = get_current_doc_path()
        auto_path = change_ext(current_doc_path, ext)
        ext_filter = f"{ext.upper()} ({'; '.join([f'*.{e}' for e in exts])})"

        if current_doc_path == "":
            force_ask_path = True

        if force_ask_path or self._config["always_ask_filepath"]:
            path, f = QtWidgets.QFileDialog.getSaveFileName(
                self._parent_widget,
                "Выбрать путь для сохранения",
                auto_path,
                f"{ext_filter};;Все файлы (*)",
                ext_filter,
            )
            return path  # может быть "", если пользователь отменил выбор пути файла в диалоге
        else:
            path = auto_path
            if self._config["ask_if_rewrite"] and os.path.exists(path) and os.path.isfile(path):
                dialog = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Icon.Question,
                    "Перезапись файла",
                    f"Файл <code>{path}</code> уже существует.<br>Перезаписать?",
                    QtWidgets.QMessageBox.StandardButton.NoButton,
                    self._parent_widget,
                )
                btn_rewrite = dialog.addButton("Перезаписать", QtWidgets.QMessageBox.ButtonRole.YesRole)
                btn_select_path = dialog.addButton("Выбрать путь", QtWidgets.QMessageBox.ButtonRole.ActionRole)
                dialog.addButton("Отмена", QtWidgets.QMessageBox.ButtonRole.RejectRole)

                dialog.exec()

                if dialog.clickedButton() == btn_rewrite:
                    pass
                elif dialog.clickedButton() == btn_select_path:
                    return self.get_save_path(exts, force_ask_path=True)
                else:
                    return ""
            return path




if __name__ == "__main__":
    # Сохранение в PDF
    save_as(change_ext(get_current_doc_path(), "pdf"))
