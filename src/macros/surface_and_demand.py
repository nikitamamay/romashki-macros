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

from PyQt5 import QtCore, QtGui, QtWidgets

from src.macros.HEAD import *
from src import config

from src import gui_widgets
from src.gui_macros import MacrosSingleCommand

from src.resources import get_resource_path


def set_surface_finish(sf_text: str) -> None:
    doc2d: KAPI7.IKompasDocument2D = open_doc2d()
    dc: KAPI7.IDrawingDocument = KAPI7.IDrawingDocument(doc2d)

    sr: KAPI7.ISpecRough = dc.SpecRough
    sr.Text = sf_text
    sr.AddSign = True
    sr.Distance = 2
    sr.Update()


def set_technical_demand(td_text: str) -> None:
    doc2d: KAPI7.IKompasDocument2D = open_doc2d()
    dc: KAPI7.IDrawingDocument = KAPI7.IDrawingDocument(doc2d)

    td: KAPI7.ITechnicalDemand = dc.TechnicalDemand
    text: KAPI7.IText = td.Text
    text.Str = td_text
    td.Update()



class MacrosSurfaceRoughnessAndTechDemand(MacrosSingleCommand):
    def __init__(self) -> None:
        super().__init__(
            "surface_and_demand",
            "Шероховатость и ТТ",
            get_resource_path("img/macros/surface_and_demand.svg"),
            "Вставить на чертеж неуказанную шероховатость\nи технические требования",
        )

    def check_config(self) -> None:
        try:
            assert isinstance(self._config["surface_finish_text"], str)
        except:
            self._config["surface_finish_text"] = "Ra 25"

        try:
            assert isinstance(self._config["technical_demand"], str)
        except:
            self._config["technical_demand"] = "* Размеры для справок.\nОбщие допуски по ГОСТ 30893.2 - mK."


    def execute_macros(self) -> None:
        set_surface_finish(self._config["surface_finish_text"])
        set_technical_demand(self._config["technical_demand"])

    def settings_widget(self) -> QtWidgets.QWidget:
        def _apply_changes() -> None:
            self._config["surface_finish_text"] = le_sf.text()
            self._config["technical_demand"] = te_td.toPlainText()
            print(repr(te_td.toPlainText()))
            config.save_delayed()

        w = QtWidgets.QWidget()
        l = QtWidgets.QGridLayout()
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        w.setLayout(l)

        le_sf = QtWidgets.QLineEdit(self._config["surface_finish_text"])
        le_sf.textChanged.connect(_apply_changes)

        te_td = QtWidgets.QTextEdit()
        te_td.setPlainText(self._config["technical_demand"])
        te_td.textChanged.connect(_apply_changes)

        l.addWidget(QtWidgets.QLabel("Текст неуказанной шероховатости:"), 0, 0, 1, 1)
        l.addWidget(le_sf, 0, 1, 1, 1)
        l.addWidget(QtWidgets.QLabel("Текст технических требований:"), 1, 0, 1, 2)
        l.addWidget(te_td, 2, 0, 1, 2)

        return w



if __name__ == "__main__":
    set_surface_finish("25")  # без "Ra", потому что мы использовали старое обозначение (просто число над галочкой)
    set_technical_demand("lalala")  # удобнее, чтобы ТТ просто появились в чертеже. Их все равно редактировать. Удобнее --- копированием текста из заранее заготовленного файла `шаблоны_ТТ.txt`
