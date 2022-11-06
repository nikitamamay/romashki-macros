from HEAD import *


def fix_LCS(app: KAPI7.IApplication):
    ss: KAPI7.ISystemSettings = app.SystemSettings
    ss.ModelLocalCSCreateInAbsoluteCS = True
    ss.ModelLocalCSSetActive = False

    if get_document_type(app.ActiveDocument) == DocumentTypeEnum.type_3D:
        active_doc: KAPI7.IKompasDocument3D = KAPI7.IKompasDocument3D(app.ActiveDocument)
        part: KAPI7.IPart7 = active_doc.TopPart
        agc: KAPI7.IAuxiliaryGeomContainer = get_by_QueryInterface(part, KAPI7.IAuxiliaryGeomContainer)
        lcss: KAPI7.ILocalCoordinateSystems = agc.LocalCoordinateSystems
        lcss.SetCurrent(None)
