"""
Головной файл программы.

Здесь имеется проверка на то, запущен ли Компас в данный момент или нет, с предложением его запустить.
Дело в том, что при выполнении макросов, если Компас закрыт, то он открывается в скрытом режиме
и остается открытым до перезагрузки компьютера, а закрыть его можно только через диспетчер задач.

Соответственно, при открытии Компаса в явном виде для работы с чертежами и моделями, макросы
могут перестать работать, потому что они будут ссылаться на тот экземпляр Компаса, который запущен
в скрытом режиме.
"""



from src.resources import *
set_bundle_dir_by_main_file(__file__)

from PyQt5 import QtGui, QtWidgets

from src import gui
from src import config
from src.macros.HEAD import is_kompas_running, start_kompas

import sys
exit = sys.exit


app = QtWidgets.QApplication([])

app.setWindowIcon(QtGui.QIcon(get_resource_path("icon/macros-icon.ico")))
app.setApplicationName(config.PROGRAM_NAME)


if not is_kompas_running():
    btn = QtWidgets.QMessageBox.critical(
        None,
        f"Компас-3D не запущен - {config.PROGRAM_NAME}",
        f"Не найдено запущенное приложение Компас-3D.\nЗапустить Компас-3D или закрыть {config.PROGRAM_NAME}?",
        QtWidgets.QMessageBox.StandardButton.Open | QtWidgets.QMessageBox.StandardButton.Close,
    )
    if btn == QtWidgets.QMessageBox.StandardButton.Open:
        if not start_kompas():
            QtWidgets.QMessageBox.critical(
                None,
                f"Не удалось запустить Компас-3D - {config.PROGRAM_NAME}",
                f"Не удалось запустить Компас-3D.\nПрограмма {config.PROGRAM_NAME} будет закрыта.",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            exit(1)
    else:
        exit(1)


w = gui.MainWindow()
w.show()

config.execute_after_config_reset()

app.exec()
