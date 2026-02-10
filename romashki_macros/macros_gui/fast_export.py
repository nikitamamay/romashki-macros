"""
Модуль графического интерфейса макроса `fast_export`.

Графический интерфейс позволяет:
* эскпортировать текущий документ в формат PDF или PNG;
* эскпортировать текущую 3D-модель в формат STEP;
* настраивать:
    * опцию перезаписи уже существующего файла;
    * опцию запроса имени файла при каждом экспорте.

"""
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config

from ..gui import widgets as gui_widgets
from ..gui.macros import Macros

from ..utils.resources import get_resource_path

from ..utils.file_utils import change_ext

from ..macros.fast_export import *



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

