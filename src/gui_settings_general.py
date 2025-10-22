"""
Модуль графического интерфейса приложения.

Здесь описаны классы виджетов общих настроек приложения.

"""

from src.resources import get_resource_path

from PyQt5 import QtCore, QtGui, QtWidgets

from src import config
from src.macros import macroses, Macros, get_macros
from src import gui_widgets

import typing


class GeneralSettingsWidget(QtWidgets.QWidget):
    config_reset_requested = QtCore.pyqtSignal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self._le_config_path = QtWidgets.QLineEdit(config.cr.get_filepath())
        self._le_config_path.setReadOnly(True)

        self._btn_reset_config = QtWidgets.QPushButton("Сбросить настройки")
        self._btn_reset_config.clicked.connect(self.reset_config)

        self._layout = QtWidgets.QGridLayout()
        self._layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self._layout)

        self._layout.addWidget(QtWidgets.QLabel(f"Путь к конфигурационному файлу:"), 0, 0, 1, 1)
        self._layout.addWidget(self._le_config_path, 0, 1, 1, 1)
        self._layout.addWidget(self._btn_reset_config, 1, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignLeft)

    def reset_config(self) -> None:
        btn = QtWidgets.QMessageBox.question(
            self,
            "Внимание",
            "Вы уверены, что хотите сбросить все настройки программы?\n\nПрограмма будет закрыта.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel,
            QtWidgets.QMessageBox.StandardButton.Cancel,
        )
        if btn == QtWidgets.QMessageBox.StandardButton.Yes:
            self.config_reset_requested.emit()

