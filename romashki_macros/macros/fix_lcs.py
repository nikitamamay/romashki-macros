"""
Макрос служит для исправления настроек создания локальных систем координат.

Дело в том, что при выполнении команд некоторых штатных библиотек Компаса,
например, "Валы и механические передачи", создаются локальные системы координат
и в настройках Компаса устанавливается опция "делать ЛСК текущей при её создании".
При активном использовании собственных ЛСК возникает необходимость убрать этот
флаг в настройках и вернуть статус текущей для абсолютной СК текущей модели ---
это и выполняется этим макросом.

"""

from .lib_macros.core import *


def fix_LCS():
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app = get_app7(iKompasObject7)

    ss: KAPI7.ISystemSettings = app.SystemSettings
    ss.ModelLocalCSCreateInAbsoluteCS = True
    ss.ModelLocalCSSetActive = False

    if get_document_type(app.ActiveDocument) == DocumentTypeEnum.type_3D:
        active_doc: KAPI7.IKompasDocument3D = KAPI7.IKompasDocument3D(app.ActiveDocument)
        part: KAPI7.IPart7 = active_doc.TopPart
        agc: KAPI7.IAuxiliaryGeomContainer = KAPI7.IAuxiliaryGeomContainer(part)
        lcss: KAPI7.ILocalCoordinateSystems = agc.LocalCoordinateSystems
        lcss.SetCurrent(None)


if __name__ == "__main__":
    fix_LCS()
