from HEAD import *


def save_as_png_2d(iKompasObject5, path: str) -> None:
    doc: KAPI5.ksDocument2D = iKompasObject5.ActiveDocument2D()
    if doc == None:
        raise Exception("Current Document is not a 2D document")

    rpar: KAPI5.ksRasterFormatParam = doc.RasterFormatParam()

    rpar.format = LDefin2D.FORMAT_PNG
    rpar.colorBPP = LDefin2D.BPP_COLOR_04
    rpar.greyScale = 0
    rpar.extResolution = 600  # dpi
    rpar.extScale = 1
    rpar.colorType = LDefin2D.BLACKWHITE
    rpar.onlyThinLine = 0
    # rpar.pages =
    # rpar.rangeIndex =
    # rpar.multiPageOutput =   # only for TIFF

    if not doc.SaveAsToRasterFormat(path, rpar):
        raise Exception("SaveAsToRasterFormat was not succeed")

    print(f"png 2D: Exported to \"{path}\"")


def save_as_png_3d(iKompasObject5, path: str) -> None:
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



def save_as_pdf_2d(iKompasObject5, path: str) -> None:
    doc: KAPI5.ksDocument2D = iKompasObject5.ActiveDocument2D()
    if doc == None:
        raise Exception("Current Document is not a 2D document")

    if not doc.ksSaveDocument(path):
        raise Exception("ksSaveDocument was not succeed")

    print(f"pdg 2D: Exported to \"{path}\"")



# not working
def save_as_pdf_2d_test(path: str) -> None:
    raise Exception(f'save_as_pdf_2d_test() does not work!')
    c: KAPI7.IConverter = app.Converter(KOMPAS_INSTALL_DIRECTORY + "\\Bin\\Pdf2d.dll")
    pPdf2dParam = c.ConverterParameters(0)
    pPdf2dParam.OnlyThinLine = 0

    # EmbedFontsWW
    # GrayScaleWWW
    # ResolutionWW
    # ScaleWWW
    # ColorTypeWWW
    # OnlyThinLine
    # MultiPageOutputW
    # PageRangeWWW
    # PageRangeStr
    # PageOddEvenW
    # UserFormatWW
    # HorizontOrientationW
    # ISOidWWW
    # MultipleFormatWW
    # WidthUserSheetWW
    # HeightUserSheetW
    # DrawQualityW
    # FilterDisableWWW
    # FilterFlagsW
    # FilterStyles
    # CutByFormatW

    c.Convert('', path, 0, False)


# not working
def save_as_pdf_as_png_2d(path: str):
    # doc: KAPI5.ksDocument2D = iKompasObject5.ActiveDocument2D()
    # if doc == None:
    #     print("Current Document is not a 2D document")
    #     return

    # rpar: KAPI5.ksRasterFormatParam = doc.RasterFormatParam()

    # rpar.format = LDefin2D.FORMAT_PNG
    # rpar.colorBPP = LDefin2D.BPP_COLOR_04
    # rpar.greyScale = 0
    # rpar.extResolution = 600  # dpi
    # rpar.extScale = 1
    # rpar.colorType = LDefin2D.BLACKWHITE
    # rpar.onlyThinLine = 0
    # # rpar.pages =
    # # rpar.rangeIndex =
    # # rpar.multiPageOutput =   # only for TIFF

    # doc.SaveAsToRasterFormat(path, rpar)

    # path_tmp = path + "_tmp.png"
    # save_as_png_2d(path_tmp)
    # fpdf.FPDF()
    # img = PIL.Image.open(path_tmp)
    # img.show()
    pass


def save_as_step(iKompasObject5, path: str) -> None:
    doc: KAPI5.ksDocument3D = iKompasObject5.ActiveDocument3D()
    if doc == None:
        raise Exception("Current Document is not a 3D document")

    apar: KAPI5.ksAdditionFormatParam = doc.AdditionFormatParam()

    apar.author = doc.author
    apar.comment = doc.comment

    # apar.saveResultDocument = ### ???

    # apar.configuration =
    apar.createLocalComponents = True
    apar.format = LDefin3D.format_STEP
    # apar.formatBinary =
    # apar.length =
    # apar.lengthUnits =
    # apar.maxTeselationCellCount =
    apar.needCreateComponentsFiles = False
    # apar.organization =
    # apar.password =
    # apar.step =
    # apar.stepType =
    # apar.stitchPrecision =
    # apar.stitchSurfaces =
    # apar.textExportForm =
    # apar.topolgyIncluded =


    for i in range(0, 28 + 1, 2):
        apar.SetObjectsOptions(i, False)

    ### Внимание! В файлах LDefin2D.py и LDefin3D.py констант ksD3ConverterOptionsEnum нет!
    apar.SetObjectsOptions(12, True)  # ksD3CODocumentProperties
    apar.SetObjectsOptions(0, True)  # ksD3COBodyes
    apar.SetObjectsOptions(28, True)  # ksD3COStyle

    # еще что-то включить? Или просить пользователя скрыть все ненужное и экспортировать всё, но только видимое?
    # размеры, ТТ, ассоциативные штуки (резьбы) и т.д.?

    if not doc.SaveAsToAdditionFormat(path, apar):
        raise Exception("SaveAsToAdditionFormat was not succeed")

    print(f"step: Exported to \"{path}\"")

