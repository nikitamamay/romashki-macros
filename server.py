from logging import exception
from PyQt5 import QtCore, QtGui, QtWidgets

import gui

import const
import socket
import threading
import traceback



def echo(addr: tuple[str, int], msg: str) -> None:
    def f():
        try:
            s = socket.socket()
            s.connect(addr)
            s.sendall(bytes(msg, encoding="utf-8"))
        except Exception as e:
            print("echo to ", addr, ": ", e.__class__.__name__, ": ", str(e), sep="")
    th = threading.Thread(
        target=f,
    )
    th.start()
    return th


class ServerThread(QtCore.QThread):
    handling_requested = QtCore.pyqtSignal(str)

    def run(self) -> None:
        server = socket.create_server(const.ADDRESS)
        server.listen(1)
        print("Server started at", const.ADDRESS)

        print("Listening at", const.ADDRESS, "...")
        while True:
            try:
                conn, addr = server.accept()
                self.handle_connection(conn, addr)
            except (TimeoutError, socket.timeout) as e:
                print("Connection timed out.")
            except Exception as e:
                print(traceback.format_exc())

    def handle_connection(self, conn, addr) -> threading.Thread:
        def f():
            with conn:
                data = b''
                while True:
                    d = conn.recv(1024)
                    if not d: break
                    data += d
                cmd = str(bytes(data), encoding="utf-8")
                print('Connected by ', addr, ": ", repr(cmd), sep="")
                self.handling_requested.emit(cmd)

        th = threading.Thread(
            target=f
        )
        th.start()
        return th


app = QtWidgets.QApplication([])

mw = gui.MainWindow()
gui.PARENT = mw
# mw.show()
mw.setVisible(False)

tray_icon = gui.TrayIcon(gui.PARENT)
tray_icon.show()
tray_icon._a_exit.triggered.connect(app.exit)
tray_icon.add_action(gui.Action(gui.icon.app(), "Raise", mw.show))

thread_server = ServerThread()
thread_server.handling_requested.connect(gui.Macros.handler)
thread_server.start()

app.exec()

print("App is executed.")
