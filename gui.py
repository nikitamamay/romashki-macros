from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import macros


PARENT = None

def ask_filepath_save(filter="All files (*)", caption: str = "Save file", directory: str = None) -> str:
    state = not QtWidgets.QWidget().isHidden()
    PARENT.show()
    filepath = QtWidgets.QFileDialog.getSaveFileName(
        PARENT,
        caption,
        directory,
        filter,
    )[0]
    if state == False:
        PARENT.hide()
    return filepath



class Macros:
    def change_bg() -> None:
        macros.change_bg()

    def fast_mate() -> None:
        macros.fast_mate()

    def drawing_stamp() -> None:
        raise Exception("Not realized yet")

    def export_png() -> None:
        path = ask_filepath_save("PNG images (*.png);;All files (*)",
            "Specify the path to PNG image")
        if path == "":
            return print("Empty path. Abort.")
        macros.export_png_auto(path)

    def export_pdf_2d() -> None:
        path = ask_filepath_save("PDF documents (*.pdf);;All files (*)",
            "Specify the path to PDF document")
        if path == "":
            return print("Empty path. Abort.")
        macros.export_pdf_2d(path)

    def export_step() -> None:
        path = ask_filepath_save("STEP models (*.step *.stp);;All files (*)",
            "Specify the path to STEP model")
        if path == "":
            return print("Empty path. Abort.")
        macros.export_step(path)

    def fix_LCS() -> None:
        macros.fix_LCS()

    def handler(cmd: str) -> None:
        COMMANDS = {
            "change_bg": Macros.change_bg,
            "fast_mate": Macros.fast_mate,
            "drawing_stamp": Macros.drawing_stamp,
            "export_png": Macros.export_png,
            "export_pdf_2d": Macros.export_pdf_2d,
            "export_step": Macros.export_step,
            "fix_LCS": Macros.fix_LCS,
        }
        try:
            if cmd in COMMANDS:
                COMMANDS[cmd]()
            else:
                raise Exception(f"Unknown command: {repr(cmd)}")
        except Exception as e:
            print(e.__class__.__name__, ": ", str(e), sep="")
            # print(traceback.format_exc())


class icon:
    def app():
        return QtGui.QIcon("img/gear_in.png")
    def cancel():
        return QtGui.QIcon("img/cancel.png")


class Action(QtWidgets.QAction):
    def __init__(
            self,
            icon: QtGui.QIcon = None,
            text: str = None,
            slot = None,
            parent = None
    ) -> None:
        super().__init__(parent)

        if not icon is None:
            self.setIcon(icon)
        if not text is None:
            self.setText(text)
        if not slot is None:
            self.triggered.connect(slot)


class TrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, parent = None) -> None:
        super().__init__(icon.app(), parent)

        self._menu = QtWidgets.QMenu()
        self.setContextMenu(self._menu)

        self._a_exit = self._menu.addAction(icon.cancel(), "Exit")

        self.add_action(Action(None, "change_bg", lambda: Macros.handler("change_bg")))
        self.add_action(Action(None, "fast_mate", lambda: Macros.handler("fast_mate")))
        self.add_action(Action(None, "drawing_stamp", lambda: Macros.handler("drawing_stamp")))
        self.add_action(Action(None, "export_png", lambda: Macros.handler("export_png")))
        self.add_action(Action(None, "export_pdf_2d", lambda: Macros.handler("export_pdf_2d")))
        self.add_action(Action(None, "export_step", lambda: Macros.handler("export_step")))
        self.add_action(Action(None, "fix_LCS", lambda: Macros.handler("fix_LCS")))
        a = QtWidgets.QAction()
        a.setSeparator(True)
        self.add_action(a)

    def add_action(self, a: QtWidgets.QAction) -> None:
        a.setParent(self._menu)
        self._menu.insertAction(self._a_exit, a)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent = None) -> None:
        super().__init__(parent)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        event.ignore()
        self.hide()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    ti = TrayIcon()
    ti.show()

    sys.exit(app.exec())