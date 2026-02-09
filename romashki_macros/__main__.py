"""
Головной файл программы.

Здесь имеется проверка на то, запущен ли Компас в данный момент или нет, с предложением его запустить.
Дело в том, что при выполнении макросов, если Компас закрыт, то он открывается в скрытом режиме
и остается открытым до перезагрузки компьютера, а закрыть его можно только через диспетчер задач.

Соответственно, при открытии Компаса в явном виде для работы с чертежами и моделями, макросы
могут перестать работать, потому что они будут ссылаться на тот экземпляр Компаса, который запущен
в скрытом режиме.
"""
from . import config

config.init_config()


from PyQt5 import QtGui, QtWidgets
import sys

from . import PROGRAM_NAME
from .utils.resources import get_resource_path

from .gui.main_window import MainWindow
from .macros.lib_macros.core import is_kompas_running, start_kompas



app = QtWidgets.QApplication([])

app.setWindowIcon(QtGui.QIcon(get_resource_path("img/macros-icon.ico")))
app.setApplicationName(PROGRAM_NAME)


if not is_kompas_running():
    btn = QtWidgets.QMessageBox.critical(
        None,
        f"Компас-3D не запущен - {PROGRAM_NAME}",
        f"Не найдено запущенное приложение Компас-3D.\nЗапустить Компас-3D или закрыть {PROGRAM_NAME}?",
        QtWidgets.QMessageBox.StandardButton.Open | QtWidgets.QMessageBox.StandardButton.Close,
    )
    if btn == QtWidgets.QMessageBox.StandardButton.Open:
        if not start_kompas():
            QtWidgets.QMessageBox.critical(
                None,
                f"Не удалось запустить Компас-3D - {PROGRAM_NAME}",
                f"Не удалось запустить Компас-3D.\nПрограмма {PROGRAM_NAME} будет закрыта.",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            sys.exit(1)
    else:
        sys.exit(1)


w = MainWindow()
w.show()

config.execute_after_config_reset()

app.exec()

