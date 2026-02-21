"""
Макрос для вставки в чертеж обозначения неуказанной шероховатости и технических
требований.

Ключевым результатом работы макроса является именно отображение на поле чертежа
обозначения неуказанной шероховатости и какого-либо текста технических требований.
Подразумевается, что и шероховатость, и техтребования затем будут редактироваться
пользователем вручную, как правило, копированием шаблонных фраз из некоторого
заранее подготовленного txt-файла.

Макрос особенно актуален для старых версий Компаса или для настроек Компаса,
в которых не подразумевается использование шаблонов чертежей с уже отображенными
этими обозначениями.

"""

from .lib_macros.core import *


def set_surface_finish(sf_text: str) -> None:
    """
    Задает общую шероховатость ("неуказанную", в правом верхнем углу)
    с текстом `sf_text` в текущем чертеже.
    """
    doc2d: KAPI7.IKompasDocument2D = open_doc2d()
    dc: KAPI7.IDrawingDocument = KAPI7.IDrawingDocument(doc2d)

    sr: KAPI7.ISpecRough = dc.SpecRough
    sr.Text = sf_text
    sr.AddSign = True
    sr.Distance = 2
    sr.Update()


def set_technical_demand(td_text: str) -> None:
    """
    Задает технические требования с текстом `td_text` в текущем чертеже.
    """
    doc2d: KAPI7.IKompasDocument2D = open_doc2d()
    dc: KAPI7.IDrawingDocument = KAPI7.IDrawingDocument(doc2d)

    td: KAPI7.ITechnicalDemand = dc.TechnicalDemand
    text: KAPI7.IText = td.Text
    text.Str = td_text
    td.Update()



if __name__ == "__main__":
    set_surface_finish("25")  # без "Ra", потому что мы использовали старое обозначение (просто число над галочкой)
    set_technical_demand("lalala")  # удобнее, чтобы ТТ просто появились в чертеже. Их все равно редактировать. Удобнее --- копированием текста из заранее заготовленного файла `шаблоны_ТТ.txt`
