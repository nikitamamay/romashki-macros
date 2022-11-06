from HEAD import *

import os

import selection_filter
import visible_elements
import fast_export
import fix_lcs

fast_mate_used = False
last_visible_elements = 0
last_selection_filter = 0


def _ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path)


def _construct_path_temp(basename: str) -> str:
    dirpath = os.path.join(os.environ.get("TEMP"), "Kompas-fast-export")
    _ensure_dir(dirpath)
    return os.path.join(dirpath, basename)


def _get_target_filepath_without_ext(path_current_doc: str) -> str:
    if path_current_doc != "":
        path_dir, basename = os.path.split(path_current_doc)
        filename = basename[ : (basename.rfind("."))]
        path_target = os.path.join(path_dir, filename)
    else:
        path_target = _construct_path_temp("fast-export")
    return path_target


def change_bg() -> None:
    iKompasObject5, iKompasObject7 = get_kompas_objects()

    view_params = iKompasObject5.GetParamStruct(LDefin2D.ko_ViewColorParam)

    iKompasObject5.ksGetSysOptions(LDefin2D.MODEL_VIEWCOLOR_OPTIONS, view_params)

    if view_params.color == 0xffffff:
        print("Current background is white, setting to gray gradient.")
        view_params.color = 0x000000
        view_params.useGradient = True
        view_params.topColor = 0x333333
        view_params.bottomColor = 0x484848
    else:
        print("Current background is not white, setting to white.")
        view_params.color = 0xffffff
        view_params.useGradient = False

    if not iKompasObject5.ksSetSysOptions(LDefin2D.MODEL_VIEWCOLOR_OPTIONS, view_params):
        raise Exception("ksSetSysOptions was not succeed")


def fast_mate() -> None:
    global fast_mate_used, last_selection_filter, last_visible_elements

    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app = get_app7(iKompasObject7)
    active_doc: KAPI7.IKompasDocument3D = KAPI7.IKompasDocument3D(app.ActiveDocument)

    # Первый вызов
    if not fast_mate_used:
        print("fast_mate: first call")
        # Сохранение настроек, которые были до вызова
        fast_mate_used = not fast_mate_used
        last_selection_filter = selection_filter.get_objects_filter(app)
        last_visible_elements = visible_elements.get_visible_elements(active_doc)

        # Установить фильтр выбора объектов на "Системы координат" и "Контрольные точки"
        selection_filter.set_objects_filter(
            app,
            selection_filter.binaryObjectsFilter.CS | selection_filter.binaryObjectsFilter.ControlPoints
        )

        # Скрыть всё, кроме систем координат и контрольных точек
        # и на уровне головной сборки, и в компонентах
        visible_elements.set_visible_elements(
            active_doc,
            visible_elements.VisibleElements.Axis \
            | visible_elements.VisibleElements.ControlPoints \
            | visible_elements.VisibleElements.Places \
            | visible_elements.VisibleElements.Axis_InComponents \
            | visible_elements.VisibleElements.ControlPoints_InComponents \
            | visible_elements.VisibleElements.Places_InComponents \
            | visible_elements.VisibleElements.LayoutGeometry \
            | visible_elements.VisibleElements.LayoutGeometry_InComponents \
        )

        CMD_MATE_COINCIDENT = 20060  # Номер команды "Сопряжение Совпадение"

        # Выполнить сопряжение "Совпадение"
        if app.IsKompasCommandEnable(CMD_MATE_COINCIDENT):
            app.ExecuteKompasCommand(CMD_MATE_COINCIDENT)

    # Повторный вызов, чтобы вернуть состояние фильтра объектов и режим скрытия объектов обратно
    else:
        print("fast_mate: second call")
        fast_mate_used = not fast_mate_used
        selection_filter.set_objects_filter(app, last_selection_filter)
        last_selection_filter = 0
        visible_elements.set_visible_elements(active_doc, last_visible_elements)
        last_visible_elements = 0


def export_png_auto(path_png: str) -> None:
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app: KAPI7.IApplication = get_app7(iKompasObject7)
    active_doc: KAPI7.IKompasDocument = KAPI7.IKompasDocument2D(app.ActiveDocument)
    if active_doc:
        doc_type = get_document_type(active_doc)
        if doc_type == DocumentTypeEnum.type_2D:
            print("Current document type is 2D")
            fast_export.save_as_png_2d(iKompasObject5, path_png)
        elif doc_type == DocumentTypeEnum.type_3D:
            print("Current document type is 3D")
            fast_export.save_as_png_3d(iKompasObject5, path_png)
        else:
            raise Exception("Unknown document type")


def export_pdf_2d(path: str) -> None:
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    fast_export.save_as_pdf_2d(iKompasObject5, path)


def export_step(path: str) -> None:
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    fast_export.save_as_step(iKompasObject5, path)


def fix_LCS() -> None:
    iKompasObject5, iKompasObject7 = get_kompas_objects()
    app = get_app7(iKompasObject7)
    fix_lcs.fix_LCS(app)



if __name__ == "__main__":
    change_bg()
