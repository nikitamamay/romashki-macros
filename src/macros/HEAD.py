"""
Базовый модуль для всех макросов.

Cодержит функции:
* для получения объектов Компас API, объекта приложения Компас,
* для преобразования интерфейсов API-5 в API-7 и наоборот,
* для работы с цветом в формате Компас (`0xBBGGRR`),
* для открытия документов и получения объектов компонента (`Part`),
* для работы с выбранными объектами в 3D-модели,
* для итерации по дочерним компонентам модели
* и другие вспомогательные функции.

"""

import Kompas6API5 as KAPI5
import KompasAPI7 as KAPI7
from win32com.client import Dispatch
import LDefin2D
import LDefin3D
import MiscellaneousHelpers as MH

import pythoncom

import typing
import os



def ensure_folder(filepath: str) -> None:
    filepath = os.path.abspath(filepath)
    if not os.path.isdir(filepath):
        print("Created directory: ", repr(filepath))
        os.makedirs(filepath)


def is_kompas_running() -> bool:
    try:
        pythoncom.connect('KOMPAS.Application.5')
        app = get_app7()
        if not app.Visible:
            app.Visible = True
        return True
    except Exception as e:
        return False

def start_kompas() -> bool:
    try:
        get_kompas_objects()
        app = get_app7()
        app.Visible = True
        return True
    except Exception as e:
        return False



def get_kompas_objects() -> tuple[KAPI5.KompasObject, KAPI7.IKompasAPIObject]:
    pythoncom.CoInitialize()

    iKompasObject5 = Dispatch('KOMPAS.Application.5')
    iKompasObject5 = KAPI5.KompasObject(iKompasObject5._oleobj_.QueryInterface(KAPI5.KompasObject.CLSID, pythoncom.IID_IDispatch))

    iKompasObject7 = Dispatch('KOMPAS.Application.7')
    iKompasObject7 = KAPI7.IKompasAPIObject(iKompasObject7._oleobj_.QueryInterface(KAPI7.IKompasAPIObject.CLSID, pythoncom.IID_IDispatch))

    return (iKompasObject5, iKompasObject7)


def get_app7(_ = None) -> KAPI7.IApplication:
    app: KAPI7.IApplication = get_kompas_objects()[1].Application
    return app


class DocumentTypeEnum(int):
    ksDocumentUnknown = 0  # Неизвестный тип
    ksDocumentDrawing = 1  # Чертеж
    ksDocumentFragment = 2  # Фрагмент
    ksDocumentSpecification = 3  # Спецификация
    ksDocumentPart = 4  # Деталь
    ksDocumentAssembly = 5  # Сборка
    ksDocumentTextual = 6  # Текстовый доку­мент
    ksDocumentTechnologyAssembly = 7  # Технологиче­ская сборка

    type_2D = 100
    type_2D_text = 101
    type_2D_spc = 102
    type_3D = 103


def get_document_type(doc: KAPI7.IKompasDocument) -> int:
    if doc.DocumentType == DocumentTypeEnum.ksDocumentPart \
            or doc.DocumentType == DocumentTypeEnum.ksDocumentAssembly \
            or doc.DocumentType == DocumentTypeEnum.ksDocumentTechnologyAssembly:
        return DocumentTypeEnum.type_3D
    elif doc.DocumentType == DocumentTypeEnum.ksDocumentDrawing \
            or doc.DocumentType == DocumentTypeEnum.ksDocumentFragment:
        return DocumentTypeEnum.type_2D
    elif doc.DocumentType == DocumentTypeEnum.ksDocumentTextual:
        return DocumentTypeEnum.type_2D_text
    elif doc.DocumentType == DocumentTypeEnum.ksDocumentSpecification:
        return DocumentTypeEnum.type_2D_spc
    else:
        return DocumentTypeEnum.ksDocumentUnknown


def color_traditional_to_kompas(color_traditional: int) -> int:
    """
    Преобразование цвета из традиционного формата `0xRRGGBB` в формат Компаса `0xBBGGRR`.
    """
    r = (color_traditional & 0xff0000) >> 16
    g = (color_traditional & 0x00ff00) >> 8
    b = color_traditional & 0x0000ff
    return (b << 16) | (g << 8) | r

def color_kompas_to_traditional(color_kompas: int) -> int:
    """
    Преобразование цвета из формата Компаса `0xBBGGRR` в традиционный формат `0xRRGGBB`.
    """
    r = color_kompas & 0x0000ff
    g = (color_kompas & 0x00ff00) >> 8
    b = (color_kompas & 0xff0000) >> 16
    return (r << 16) | (g << 8) | b

def pretty_print_color(color: int) -> str:
    return hex(color)[2:].rjust(6, "0")




def get_view_by_name(doc: KAPI7.IKompasDocument2D, view_name: str, do_raise_exception: bool = True) -> KAPI7.IView:
    assert get_document_type(doc) == DocumentTypeEnum.type_2D
    vlm: KAPI7.IViewsAndLayersManager = doc.ViewsAndLayersManager
    views: KAPI7.IViews = vlm.Views
    view: KAPI7.IView = views.View(view_name)
    if do_raise_exception and view is None:
        raise Exception(f"Не найден вид с названием \"{view_name}\"")
    return view


def get_system_view(doc: KAPI7.IKompasDocument2D) -> KAPI7.IView:
    assert doc.DocumentType == DocumentTypeEnum.ksDocumentFragment
    vlm: KAPI7.IViewsAndLayersManager = doc.ViewsAndLayersManager
    views: KAPI7.IViews = vlm.Views
    view: KAPI7.IView = views.View(0)
    return view


def create_document2d(
        app: KAPI7.IApplication,
        type_: DocumentTypeEnum,
        is_visible = True,
        path_to_save: str = "",
        ) -> KAPI7.IKompasDocument2D:
    docs: KAPI7.IDocuments = app.Documents
    doc: KAPI7.IKompasDocument2D = KAPI7.IKompasDocument2D(
        docs.Add(type_, is_visible)
    )
    if path_to_save != "":
        doc.SaveAs(path_to_save)
    return doc


def get_active_part() -> tuple[KAPI7.IKompasDocument3D, KAPI7.IPart7]:
    app = get_app7()
    active_doc: KAPI7.IKompasDocument3D = KAPI7.IKompasDocument3D(app.ActiveDocument)
    return (active_doc, active_doc.TopPart)


def open_document(filepath: str = "", is_hidden: bool = False) -> KAPI7.IKompasDocument:
    app = get_app7()
    if filepath == "":
        return app.ActiveDocument

    docs: KAPI7.IDocuments = app.Documents

    for i in range(docs.Count):
        doc: KAPI7.IKompasDocument = docs.Item(i)
        if doc.PathName == filepath:
            print("Найден среди открытых:", repr(filepath))
            # doc.Active = True  # FIXME точно нужно?
            # doc.Visible = not is_hidden  # FIXME не работает для просто IKompasDocument
            break
    else:
        doc: KAPI7.IKompasDocument = docs.Open(filepath, not is_hidden, False)

    if doc is None:
        raise Exception(f"Не удается открыть документ '{filepath}'")

    return doc


def open_part(filepath: str = "", is_hidden: bool = False) -> tuple[KAPI7.IKompasDocument3D, KAPI7.IPart7]:
    # FIXME добавить возможность указать исполнение здесь (по обозначению, например, или по его окончанию -01)
    """ Если `filepath == ""`, то возвращается текущий документ и его компонент верхнего уровня. """

    if filepath == "":
        return get_active_part()

    doc = open_document(filepath, is_hidden)

    doc3d: KAPI7.IKompasDocument3D = KAPI7.IKompasDocument3D(doc)
    return (doc3d, doc3d.TopPart)


def open_part_K5(filepath: str = "", is_hidden: bool = False) -> tuple[KAPI5.ksDocument3D, KAPI5.ksPart]:
    # FIXME добавить возможность указать исполнение здесь (по обозначению, например, или по его окончанию -01)

    iKompasObject5, iKompasObject7 = get_kompas_objects()

    if filepath != "":
        doc: KAPI5.ksDocument3D = iKompasObject5.Document3D()
        doc.Open(filepath, is_hidden)
    else:
        doc: KAPI5.ksDocument3D = iKompasObject5.ActiveDocument3D()

    if doc is None:
        raise Exception(f"Не удается открыть документ '{filepath}'")

    part: KAPI5.ksPart = doc.GetPart(LDefin3D.pTop_Part)

    return doc, part


def open_doc2d(filepath: str = "") -> KAPI7.IKompasDocument2D:
    """ Если `filepath == ""`, то возвращается `app.ActiveDocument`. """
    app: KAPI7.IApplication = get_app7()

    if filepath == "":
        active_doc: KAPI7.IKompasDocument2D = KAPI7.IKompasDocument2D(app.ActiveDocument)
        if get_document_type(active_doc) != DocumentTypeEnum.type_2D:
            raise Exception("Текущий документ не является 2D-документом")
        return active_doc

    docs: KAPI7.IDocuments = app.Documents
    doc: KAPI7.IKompasDocument = docs.Open(filepath, True, False)

    if doc is None:
        raise Exception(f"Не удается открыть документ '{filepath}'")

    doc2d: KAPI7.IKompasDocument2D = KAPI7.IKompasDocument2D(doc)
    return doc2d

def open_doc2d_K5(filepath: str = "") -> KAPI5.ksDocument2D:
    """ Если `filepath == ""`, то возвращается `app.ActiveDocument`. """
    iKompasObject5, iKompasObject7 = get_kompas_objects()

    if filepath != "":
        doc2d: KAPI5.ksDocument2D = iKompasObject5.Document2D()
        doc2d.Open(filepath, False)
    else:
        doc2d: KAPI5.ksDocument2D = iKompasObject5.ActiveDocument2D()

    if doc2d is None:
        raise Exception(f"Не удается открыть документ '{filepath}'")

    return doc2d


def remember_opened_document() -> str:
    app = get_app7()
    doc: KAPI7.IKompasDocument = app.ActiveDocument
    if not doc is None:
        path = doc.PathName
    else:
        path = ""
    print(f"Текущий документ: '{path}'")
    return path

def restore_opened_document(path: str) -> None:
    if path != "":
        print(f"Возврат к ранее открытому документу: '{path}'")
        app: KAPI7.IApplication = get_app7()
        docs: KAPI7.IDocuments = app.Documents
        app.ActiveDocument = docs.Open(path, True)


def rebuild_current_document() -> None:
    doc, part = open_part()
    doc.RebuildDocument()
    print(f"Перестроен документ: {doc.PathName}")


def create_part(
        type3d: DocumentTypeEnum,
        is_visible = True,
        path_to_save: str = "",
        ) -> tuple[KAPI7.IKompasDocument3D, KAPI7.IPart7]:
    app = get_app7()
    docs: KAPI7.IDocuments = app.Documents
    doc: KAPI7.IKompasDocument3D = KAPI7.IKompasDocument3D(
        docs.Add(type3d, is_visible)
    )
    if path_to_save != "":
        doc.SaveAs(path_to_save)
    return (doc, doc.TopPart)




def get_selected(active_doc: KAPI7.IKompasDocument3D|KAPI7.IKompasDocument2D1, classes: tuple=(object)) -> list:
    assert isinstance(active_doc, (KAPI7.IKompasDocument3D, KAPI7.IKompasDocument2D1))
    sm: KAPI7.ISelectionManager = active_doc.SelectionManager
    s_objs: typing.Iterable[KAPI7.IKompasAPIObject] = ([sm.SelectedObjects] \
        if not isinstance(sm.SelectedObjects, tuple) else sm.SelectedObjects) \
        if not sm.SelectedObjects is None else []

    print(f"Выбрано {len(s_objs)} объектов:", s_objs)

    objects: list[object] = []

    for obj in s_objs:
        if (not obj is None) and isinstance(obj, classes):
            objects.append(obj)
        else:
            pass

    return objects

def get_selected_K5(active_doc5: KAPI5.ksDocument3D, classes: tuple=(object)) -> list:
    smng: KAPI5.ksSelectionMng = active_doc5.GetSelectionMng()

    print(f"Выбрано {smng.GetCount()} объектов (K5): [", end="")

    objects: list[object] = []

    for i in range(smng.GetCount()):
        obj = smng.GetObjectByIndex(i)
        print(obj, end=", ")

        if (not obj is None) and isinstance(obj, classes):
            objects.append(obj)
        else:
            pass

    print("]")

    return objects


def transfer_to_K5(obj: object, o3d_type: int = 0) -> object:
    kompas5, kompas7 = get_kompas_objects()
    return kompas5.TransferInterface(obj, 1, o3d_type)

def transfer_to_7(obj: object, o3d_type: int = 0) -> object:
    kompas5, kompas7 = get_kompas_objects()
    return kompas5.TransferInterface(obj, 2, o3d_type)


def iterate_child_parts(part: KAPI7.IPart7):
    parts: KAPI7.IParts7 = part.Parts
    for i in range(parts.Count):
        p = parts.Part(i)
        yield p


def apply_to_children_r(part: KAPI7.IPart7, function: typing.Callable[[KAPI7.IPart7], bool]):
    """
        Внимание! Будут итерироваться все компоненты, включая компоновочную геометрию и все её компоненты!

        Определение callback-функции: `function(child_part) -> bool`.
        Если `function()` возвращает `False`, то дочерние компоненты `child_part`-а не будут итерироваться.

        Постфикс в названии этой функции `_r` --- это `recursive`.
    """
    parts: KAPI7.IParts7 = part.Parts
    for i in range(parts.Count):
        p = parts.Part(i)
        if function(p):
            apply_to_children_r(p, function)


def apply_to_children_with_parent_r(parent_part: KAPI7.IPart7, function: typing.Callable[[KAPI7.IPart7, KAPI7.IPart7], bool]) -> None:
    """
        Внимание! Будут итерироваться все компоненты, включая компоновочную геометрию и все её компоненты!

        Определение callback-функции: `function(child_part, parent_part) -> bool`.
        Если `function()` возвращает `False`, то дочерние компоненты `child_part`-а не будут итерироваться.

        Постфикс в названии этой функции `_r` --- это `recursive`.
    """
    parts: KAPI7.IParts7 = parent_part.Parts
    for i in range(parts.Count):
        child_part = parts.Part(i)
        if function(child_part, parent_part):
            apply_to_children_with_parent_r(child_part, function)


def ensure_list(obj) -> list:
    if obj is None:
        return []
    if isinstance(obj, (tuple, list)):
        return obj
    return [obj]




if __name__ == "__main__":
    # get_kompas_objects()
    print(is_kompas_running())
