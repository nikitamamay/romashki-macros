import Kompas6API5 as KAPI5
import KompasAPI7 as KAPI7
from win32com.client import Dispatch
import LDefin2D
import LDefin3D
import MiscellaneousHelpers as MH

import pythoncom

from const import KOMPAS_INSTALL_DIRECTORY


def get_kompas_objects() -> tuple[KAPI5.KompasObject, KAPI7.IKompasAPIObject]:
    # pythoncom.CoInitialize()

    iKompasObject5 = Dispatch('KOMPAS.Application.5')
    iKompasObject5 = KAPI5.KompasObject(iKompasObject5._oleobj_.QueryInterface(KAPI5.KompasObject.CLSID, pythoncom.IID_IDispatch))

    iKompasObject7 = Dispatch('KOMPAS.Application.7')
    iKompasObject7 = KAPI7.IKompasAPIObject(iKompasObject7._oleobj_.QueryInterface(KAPI7.IKompasAPIObject.CLSID, pythoncom.IID_IDispatch))

    return (iKompasObject5, iKompasObject7)


def get_app7(iKompasObject7: KAPI7.IKompasAPIObject) -> KAPI7.IApplication:
    app: KAPI7.IApplication = iKompasObject7.Application
    return app


def get_by_QueryInterface(parent_object, class_):
    return class_(
        parent_object._oleobj_.QueryInterface(
            class_.CLSID,
            pythoncom.IID_IDispatch
        )
    )


class DocumentTypeEnum:
    ksDocumentUnknown = 0  # Неизвестный тип
    ksDocumentDrawing = 1  # Чертеж
    ksDocumentFragment = 2  # Фрагмент
    ksDocumentSpecification = 3  # Спецификация
    ksDocumentPart = 4  # Деталь
    ksDocumentAssembly = 5  # Сборка
    ksDocumentTextual = 6  # Текстовый доку­мент
    ksDocumentTechnologyAssembly = 7  # Технологиче­ская сборка

    type_2D = 100
    type_3D = 101


def get_document_type(doc: KAPI7.IKompasDocument) -> int:
    """
    Returns:
        * `DocumentTypeEnum.ksDocumentUnknown` - if unknown
        * `DocumentTypeEnum.type_2D` - if 2D
        * `DocumentTypeEnum.type_3D` - if 3D
    """
    if doc.DocumentType == DocumentTypeEnum.ksDocumentPart \
            or doc.DocumentType == DocumentTypeEnum.ksDocumentAssembly \
            or doc.DocumentType == DocumentTypeEnum.ksDocumentTechnologyAssembly:
        return DocumentTypeEnum.type_3D
    elif doc.DocumentType == DocumentTypeEnum.ksDocumentDrawing \
            or doc.DocumentType == DocumentTypeEnum.ksDocumentFragment \
            or doc.DocumentType == DocumentTypeEnum.ksDocumentSpecification \
            or doc.DocumentType == DocumentTypeEnum.ksDocumentTextual:
        return DocumentTypeEnum.type_2D
    else:
        return DocumentTypeEnum.ksDocumentUnknown
