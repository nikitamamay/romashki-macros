
from PyQt5 import QtCore, QtGui, QtWidgets

from ..macros.lib_macros.core import *
from .. import config

from ..gui import widgets as gui_widgets
from ..gui.macros import Macros

from ..utils.resources import get_resource_path

# from ..macros.do_not_disturb import set_silent_mode, get_silent_mode
from ..macros.fast_parts import *


class MacrosFastParts(Macros):
    def __init__(self) -> None:
        super().__init__(
            "fast_parts",
            "Работа с компонентами",
        )

        self._last_selected_target_asm_path: str = ""

    def check_config(self):
        try:
            assert isinstance(self._config["do_close_child_docs"], bool)
        except:
            self._config["do_close_child_docs"] = False

    def settings_widget(self):
        def _set_do_close_child_docs(state: bool) -> None:
            self._config["do_close_child_docs"] = state
            config.save_delayed()

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        cb = QtWidgets.QCheckBox("Закрывать файлы деталей при их создании из выбранных тел")
        cb.setChecked(self._config["do_close_child_docs"])
        cb.stateChanged.connect(_set_do_close_child_docs)

        l.addWidget(cb, 0, 0, 1, 1)
        return w

    def toolbar_widgets(self):
        btn_fast_parts = QtWidgets.QToolButton()
        btn_fast_parts.setIcon(QtGui.QIcon(get_resource_path("img/macros/fast_parts_work_to_out.svg")))
        btn_fast_parts.setToolTip("Создать out-детали из выбранных тел")
        btn_fast_parts.clicked.connect(self._create_out_parts)


        btn_create_fast_part = QtWidgets.QToolButton()
        btn_create_fast_part.setIcon(QtGui.QIcon(get_resource_path("img/macros/fast_part_single.svg")))
        btn_create_fast_part.setToolTip("Создать out-модель с компоновочной геометрией и вставить её в сборку")
        btn_create_fast_part.clicked.connect(self._create_single_out_part)


        btn_orient = QtWidgets.QToolButton()
        btn_orient.setIcon(QtGui.QIcon(get_resource_path("img/macros/orient.svg")))
        btn_orient.setToolTip(
            "Ориентировать выбранные компоненты\n"
            "параллельно осям АСК сборки"
        )
        btn_orient.clicked.connect(lambda: self.execute(orient_part_K5))


        btn_insert_parts_from_lg = QtWidgets.QToolButton()
        btn_insert_parts_from_lg.setIcon(QtGui.QIcon(get_resource_path("img/macros/insert_parts_from_lg.svg")))
        btn_insert_parts_from_lg.setToolTip(
            "Вставить выбранные компоненты\n"
            "компоновочной геометрии в текущую сборку")
        btn_insert_parts_from_lg.clicked.connect(
            lambda: self.execute(self._create_parts_and_bodies_from_lg)
        )

        return {
            "кнопка ориентирования компонентов": btn_orient,
            "кнопка создания out-деталей": btn_fast_parts,
            "кнопка создания одной out-модели": btn_create_fast_part,
            "кнопка вставки компонентов": btn_insert_parts_from_lg,
        }


    def _create_out_parts(self) -> None:
        # FIXME не_обёрнуто в try-except ?
        doc, part = open_part()
        path_dir: str = doc.Path

        if self._last_selected_target_asm_path == "":
            self._last_selected_target_asm_path = path_dir

        # get_selected(doc)  # для вызова print() этих выбранных объектов

        target_asm_path, filter_ = QtWidgets.QFileDialog.getOpenFileName(
            self._parent_widget,
            "Выбрать путь к файлу out-сборки",
            self._last_selected_target_asm_path,
            f"{gui_widgets.EXT_ASSEMBLY};;{gui_widgets.EXT_PART};;{gui_widgets.EXT_ALL}",
            gui_widgets.EXT_ASSEMBLY,
        )

        if target_asm_path == "":
            print("Команда отменена")
            return

        self._last_selected_target_asm_path = target_asm_path

        parts_dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self._parent_widget,
            "Выбрать путь к папке создаваемых деталей",
            path_dir,
        )

        if parts_dir_path == "":
            print("Команда отменена")
            return

        self.execute(
            lambda: create_parts_from_selected_bodies(target_asm_path, parts_dir_path, self._config["do_close_child_docs"])
        )

    def _create_single_out_part(self) -> None:
        try:
            path_dir = os.path.dirname(remember_opened_document())
        except:
            path_dir = ""

        if self._last_selected_target_asm_path == "":
            self._last_selected_target_asm_path = path_dir

        target_asm_path, filter_ = QtWidgets.QFileDialog.getOpenFileName(
            self._parent_widget,
            "Выбрать путь к файлу out-сборки",
            self._last_selected_target_asm_path,
            f"{gui_widgets.EXT_ASSEMBLY};;{gui_widgets.EXT_PART};;{gui_widgets.EXT_ALL}",
            gui_widgets.EXT_ASSEMBLY,
        )

        if target_asm_path == "":
            print("Команда отменена")
            return

        self._last_selected_target_asm_path = target_asm_path

        fast_part_path, filter_ = QtWidgets.QFileDialog.getSaveFileName(
            self._parent_widget,
            "Выбрать путь к файлу out-модели",
            path_dir,
            f"{gui_widgets.EXT_ASSEMBLY};;{gui_widgets.EXT_PART};;{gui_widgets.EXT_ALL}",
            gui_widgets.EXT_ASSEMBLY,
        )

        if fast_part_path == "":
            print("Команда отменена")
            return

        self.execute(
            lambda: create_fast_part(target_asm_path, fast_part_path)
        )

    def _create_parts_and_bodies_from_lg(self) -> None:
        insert_parts_from_lg()
        copy_bodies_from_lg()


if __name__ == "__main__":
    orient_part_K5()
