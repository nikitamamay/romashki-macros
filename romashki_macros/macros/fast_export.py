"""
Изначально макрос задумывался для возможности экспортировать текущий документ
в различные форматы: PNG, PDF, STEP.

Однако в работе наиболее часто этот макрос использовался для сохранения в PDF
при работе с чертежами.

По умолчанию макрос сохраняет PDF с тем же названием, что и текущий документ,
просто меняя расширение файла. Перезаписывает файл, если такой файл уже
существует на диске.

"""

from .lib_macros.core import *


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



if __name__ == "__main__":

    # Сохранение в PDF
    save_as(get_current_doc_path() + ".pdf")
