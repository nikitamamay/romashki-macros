"""
Макрос предоставляет функционал по пакетному изменению свойств (наименования,
обозначения, комментария) для выбранных компонентов в сборке. Однако макрос
не доработан; работоспособность не гарантируется.

Также имеется функционал по замене путей с автоматическим поиском файлов в папке
проекта, что полезно при реорганизации структуры хранения файлов в Проводнике.
Однако здесь реализована очень ограниченный функционал: только замена файлов
в 3D-моделях, при том даже без поддержки исполнений деталей.
Не заменяются пути в файлах чертежей, не меняются ссылки на переменные.

"""

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import Macros

from src.resources import get_resource_path

import traceback
import subprocess
import os

from src import ods_utils


BULK_RENAME_SHEET_NAME = "PROPERTIES"

# Номера свойств обязательно должны быть float!
# Здесь номера свойств прописаны для Компас16. В новых версиях
# это может отличаться, да и вообще, там другой принцип.
PROPERTY_MARKING = 4.0
PROPERTY_NAME = 5.0
PROPERTY_COMMENT = 13.0
PROPERTY_SPECIFICATION_SECTION = 20.0



class PDM_Part():
    def __init__(self) -> None:
        self._id: int = 0
        self._name: str = ""
        self._marking: str = ""
        self._filepath: str = ""
        self._children: list[int] = []

    def name(self) -> str:
        return self._name

    def marking(self) -> str:
        return self._marking

    def filepath(self) -> str:
        return self._filepath

    def add_child(self, _id: int) -> None:
        self._children.append(_id)

    def iterate_children(self):
        return self._children.__iter__()

    def identity(self) -> str:
        return f"{self._name}|{self._marking}"

    @staticmethod
    def fromKAPI7(part: KAPI7.IPart7) -> 'PDM_Part':
        p = PDM_Part()
        p._name = part.Name
        p._marking = part.Marking
        p._filepath = part.FileName
        return p


class PDM_PartsContainer():
    def __init__(self) -> None:
        self._parts: dict[int, PDM_Part] = {}

    def register(self, part: PDM_Part) -> tuple[int, bool]:
        """
            Возвращает `(id, True)`, если зарегистрирован новый объект,
            и `(id, False)`, если объект уже есть в контейнере.
        """
        _id = self.get_part_id(part)
        if _id != 0:
            return (_id, False)

        _id = self.get_next_id()
        self._parts[_id] = part
        part._id = _id
        return (_id, True)

    def get_next_id(self) -> int:
        s = set(self._parts.keys())
        s.add(0)
        return max(s) + 1

    def get_part_id(self, part: PDM_Part) -> int:
        for _id, p in self._parts.items():
            if p.identity() == part.identity():
                return _id
        return 0

    def get_part_by_id(self, _id: int) -> PDM_Part:
        if _id in self._parts:
            return self._parts[_id]
        return PDM_Part()


def load_part_structure(part: KAPI7.IPart7, container: PDM_PartsContainer) -> int:
    if part.IsLayoutGeometry:
        return 0

    p = PDM_Part.fromKAPI7(part)
    top_id, is_new_obj = container.register(p)
    if not is_new_obj:
        return top_id

    for child in iterate_child_parts(part):
        c = PDM_Part.fromKAPI7(child)
        c_id = load_part_structure(child, container)
        if c_id != 0:
            p.add_child(c_id)

    return top_id


def get_structure_table_by_levels(container: PDM_PartsContainer, _id: int, level = 0) -> list[list]:
    toppart = container.get_part_by_id(_id)
    lines = [
        [level, toppart.marking(), toppart.name(), toppart.filepath()]
    ]
    for c_id in toppart.iterate_children():
        new_lines = get_structure_table_by_levels(container, c_id, level + 1)
        lines.extend(new_lines)
    return lines


def get_structure_table(container: PDM_PartsContainer, _id: int) -> list[list]:
    toppart = container.get_part_by_id(_id)

    # { id: count }
    top_dict: dict[int, int] = {}

    def _count_children(children: typing.Iterable[int]) -> None:
        for c_id in children:
            if not c_id in top_dict:
                top_dict[c_id] = 0
            top_dict[c_id] += 1
            _count_children(container.get_part_by_id(c_id).iterate_children())

    _count_children(toppart.iterate_children())

    def _get_line(part, count):
        return [part.marking(), part.name(), count, part.filepath()]

    lines = []
    for p_id, count in top_dict.items():
        p = container.get_part_by_id(p_id)
        lines.append(_get_line(p, count))

    lines = sorted(
        sorted(lines, key=lambda line: line[1]),
        key=lambda line: line[0],
    )

    lines.insert(
        0,
        _get_line(toppart, 1)
    )
    return lines




def _print_properties(filename: str = "") -> bool:
    """
        Функция для отладки. Нужна для определения `p_id` у всех свойств в документе.
    """
    app = get_app7()
    doc, part = open_part(filename)

    pmng = KAPI7.IPropertyMng(app)
    ps = pmng.GetProperties(doc)
    pk = KAPI7.IPropertyKeeper(part)

    for p in ps:
        p_id = p.Id
        p_name = p.Name
        _, p_value, is_from_source = pk.GetPropertyValue(p, None, True, None)
        print(p_id, p_name, repr(p_value))


def get_property_value(doc: KAPI7.IKompasDocument, part: KAPI7.IPart7, p_id: float) -> typing.Any:
    # FIXME doc можно получить через open_document(part.FileName) - ?

    if not isinstance(p_id, float):
        raise Exception("p_id должно быть типа float")

    app = get_app7()
    pmng = KAPI7.IPropertyMng(app)
    pk = KAPI7.IPropertyKeeper(part)

    p: KAPI7.IProperty = pmng.GetProperty(doc, p_id)

    _, p_value, is_from_source = pk.GetPropertyValue(p, None, True, None)
    return p_value


def set_property_value(doc: KAPI7.IKompasDocument, part: KAPI7.IPart7, p_id: float, p_value: typing.Any) -> bool:
    # FIXME doc можно получить через open_document(part.FileName) - ?

    if not isinstance(p_id, float):
        raise Exception("p_id должно быть типа float")

    app = get_app7()
    pmng = KAPI7.IPropertyMng(app)
    pk = KAPI7.IPropertyKeeper(part)

    p: KAPI7.IProperty = pmng.GetProperty(doc, p_id)

    return pk.SetPropertyValue(p, p_value, True)


def rename_parts(data: list[tuple[str, str, str]]) -> None:
    for line in data:
        # поле comment может быть пустым, тогда выдается line из 3 значений => not enough values to unpack
        line = (line + ["", "", "", ""])[:4]

        marking, name, filepath, comment = line

        try:
            doc, part = open_part(filepath, is_hidden=True)  # FIXME может быть ошибка, если файла по пути не существует
        except:
            print("Не удалось открыть документ", filepath)
            continue

        try:
            # FIXME свойства почему-то не_меняются в Компас22; но, кажется, менялись в Компас16, когда я в нем работал
            set_property_value(doc, part, PROPERTY_MARKING, marking)
            set_property_value(doc, part, PROPERTY_NAME, name)
            set_property_value(doc, part, PROPERTY_COMMENT, comment)
            part.Update()
        except:
            print("Не удалось изменить свойства в документе", filepath)
            continue

        try:
            doc.Save()
        except:
            print("Не удалось сохранить документ", filepath)

    print("Изменение свойств завершено.")


def get_selected_parts_properties() -> list[list]:
    def ensure_not_None(value):
        if value is None:
            return ""
        return value

    doc, toppart = open_part()
    parts: list[KAPI7.IPart7] = get_selected(doc, KAPI7.IPart7)

    if len(parts) == 0:
        parts = iterate_child_parts(toppart)

    lines = []
    for part in parts:
        line = [
            ensure_not_None(part.Marking),
            ensure_not_None(part.Name),
            ensure_not_None(part.FileName),
            ensure_not_None(get_property_value(doc, part, PROPERTY_COMMENT)),
        ]
        lines.append(line)

    return lines



def import_files_tree(path: str) -> list[str]:
    files: list[str] = [path]

    if os.path.isfile(path):
        pass
    elif os.path.isdir(path):
        for entry in os.listdir(path):
            entry = os.path.join(path, entry)
            files.append(path)
            files.extend(import_files_tree(entry))
    else:
        raise Exception(f"Entry is not a file or a directory:", path)
    return files


def find_missing_paths(project_dir: str) -> tuple[set[str], dict[str, str]]:
    filepaths: list[str] = import_files_tree(project_dir)
    filebasenames: list[str] = [os.path.basename(file) for file in filepaths]

    iterated_parts: set[str] = set()
    replacements: dict[str, str] = {}  # missing_basename: replacement_path
    parents: set[str] = set()

    def _apply_to_child(part: KAPI7.IPart7, parentpart: KAPI7.IPart7) -> bool:
        if part.FileName == "":
            missing_file_basename = part.Name
            parentpart_path = parentpart.FileName

            if not missing_file_basename in replacements:
                replacements[missing_file_basename] = ""
                try:
                    i = filebasenames.index(missing_file_basename)
                    replacements[missing_file_basename] = filepaths[i]
                except ValueError:
                    print(f"Пропуск замены, так как путь пустой: {repr(missing_file_basename)} в {repr(parentpart_path)}")

            parents.add(parentpart_path)
        else:
            if part.FileName in iterated_parts:
                return False
            iterated_parts.add(part.FileName)
        return True

    doc, toppart = open_part()
    apply_to_children_with_parent_r(toppart, _apply_to_child)

    return parents, replacements


def replace_paths(parent_paths: typing.Iterable[str], replacements: dict[str, str]) -> None:
    app = get_app7()
    prev_hidemessage = app.HideMessage
    app.HideMessage = 2

    for parent_path in parent_paths:
        print(repr(parent_path))
        doc, parentpart = open_part(parent_path, True)
        parts: KAPI7.IParts7 = parentpart.Parts
        for i in range(parts.Count):
            part = parts.Part(i)
            if part.Name in replacements:
                new_path = replacements[part.Name]
                if new_path != "":
                    print(f"\t{repr(part.Name)} -> {repr(new_path)}")
                    part.FileName = new_path
                    part.Update()
        doc.RebuildDocument()
        doc.Save()

    app.HideMessage = prev_hidemessage



class BulkRenameMacros(Macros):
    def __init__(self) -> None:
        super().__init__(
            "bulk_rename",
            "Массовое переименование"
        )
        self._replacements = {}
        self._parents = set()

    def toolbar_widgets(self) -> dict[str, QtWidgets.QWidget]:
        btn_rename = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/macros/bulk_rename.svg")), "")
        btn_rename.clicked.connect(self._rename)
        btn_rename.setToolTip("Переименовать и переобозначить компоненты")

        btn_replace_paths = QtWidgets.QPushButton(QtGui.QIcon(get_resource_path("img/macros/bulk_replace_paths.svg")), "")
        btn_replace_paths.clicked.connect(self._replace_paths)
        btn_replace_paths.setToolTip("Заменить пути к файлам в папке проекта")

        return {
            "кнопка переименования": btn_rename,
            "кнопка замены путей к файлам": btn_replace_paths,
        }

    def _rename(self) -> None:
        initial_docpath = remember_opened_document()

        sheet = get_selected_parts_properties()

        ods_filepath = ods_utils.create_temp_ods_filepath()
        ods_utils.save_ods_sheet(ods_filepath, sheet, BULK_RENAME_SHEET_NAME)

        ods_utils.open_for_edit(ods_filepath)

        btn = QtWidgets.QMessageBox.question(
            self._parent_widget,
            "Редактирование свойств компонентов",
            f"<p>Отредактируйте файл:<br><code>{ods_filepath}</code></p>\
                <p>По окончании редактирования для внесения свойств нажмите ОК.</p>",
            QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel
        )

        # <пользователь работает с ODS файлом>

        if btn == QtWidgets.QMessageBox.StandardButton.Ok:
            sheet = ods_utils.read_ods_sheet(ods_filepath, BULK_RENAME_SHEET_NAME)
            print("Введенные данные:", repr(sheet))
            self.execute(
                lambda: rename_parts(sheet)
            )
            restore_opened_document(initial_docpath)
        else:
            print("Переименование отменено.")

    def _replace_paths(self) -> None:
        try:
            opened_document_path = remember_opened_document()
        except:
            opened_document_path = ""

        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self._parent_widget,
            "Выбрать путь к папке проекта",
            os.path.dirname(opened_document_path),
        )
        if dir_path == "":
            print("Команда отменена")
            return

        print(f"Выбрана папка проекта: {repr(dir_path)}")

        self._replacements.clear()
        self._parents.clear()
        def f():
            self._parents, self._replacements = find_missing_paths(dir_path)

        if not self.execute(f):
            print("Ошибка. Команда отменена.")
            return

        if len(self._replacements) == 0:
            QtWidgets.QMessageBox.information(
                self._parent_widget,
                "Замена путей к файлам",
                "Компоненты с неактуальными путями к файлам не найдены.",
            )
            return

        basenames = list(self._replacements.keys())

        msg = f"Найдено {len(self._replacements)} компонентов с неактуальными путями к файлам в {len(self._parents)} родительских моделях"
        print(msg)
        msg += ". Продолжить замену ссылок?"
        details = \
            "Родительские модели:\n" + \
            "".join([f"{repr(parent_path)}\n" for parent_path in self._parents]) + \
            "\nЗамещаемые модели:\n" + \
            "".join([f"{repr(basename)} -> {repr(new_path)}\n" for basename, new_path in self._replacements.items()])
        print(details)

        msg_box = QtWidgets.QMessageBox(self._parent_widget)
        msg_box.setIcon(QtWidgets.QMessageBox.Question)
        msg_box.setWindowTitle("Замена путей к файлам")
        msg_box.setText(msg)
        msg_box.setInformativeText(
            "<p><b>Внимание!</b> Если в модели сборки свойство компонента \"Наименование\" установлено не по источнику, "
            "то программа не может определить путь к файлу для замены.</p>"
            "<p>Зайдите в Редактор свойств и поставьте свойство \"Наименование\" у этих компонентов <b>по источнику</b> (ПКМ - Источник).</p>"
        )
        msg_box.setDetailedText(details)

        btn_ok_and_rebuild = msg_box.addButton("Заменить и перестроить", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        btn_ok_without_rebuild = msg_box.addButton("Заменить без перестроения", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        btn_cancel = msg_box.addButton("Отмена", QtWidgets.QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(btn_ok_without_rebuild)

        msg_box.exec()
        if msg_box.clickedButton() == btn_ok_and_rebuild or msg_box.clickedButton() == btn_ok_without_rebuild:
            self.execute(lambda: replace_paths(self._parents, self._replacements))
            self.execute(lambda: restore_opened_document(opened_document_path))
            if msg_box.clickedButton() == btn_ok_and_rebuild:
                self.execute(rebuild_current_document)
        else:
            print("Смена путей к файлам отменена.")


if __name__ == "__main__":

    def _f():
        while True:
            filepath = input("filepath> ")
            doc, part = open_part(filepath, True)
            set_property_value(doc, part, PROPERTY_COMMENT, "#заимствованное")




    doc, toppart = open_part()
    parts = get_selected(doc, KAPI7.IPart7)
    if len(parts) == 0:
        print("Не выбраны компоненты. Используется головная сборка.")
        parts.append(toppart)

    c = PDM_PartsContainer()

    lines = []

    for part in parts:
        top_id = load_part_structure(part, c)

        # arr = get_structure_table_by_levels(c, top_id)
        arr = get_structure_table(c, top_id)
        lines.extend(arr)
        lines.append([])

    ods_path = ods_utils.create_temp_ods_filepath()
    ods_utils.save_ods_sheet(ods_path, lines)
    ods_utils.open_for_edit(ods_path)




