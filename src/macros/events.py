"""
"Проба пера" в работе с событиями Компас.

Этот код не несет в себе никакого полезного функционала. Это незаконченная разработка.

"""
#
# Код класса BaseEvent заимствован у Slaviation:
# https://forum.ascon.ru/index.php?msg=284230
#
# Комментарии написал и типы аргументов добавил nikitamamay.
#
# 25.03.2025
#

import pythoncom, win32com.client.connect, win32com.server.util
from win32com.client import Dispatch, gencache

import typing
import traceback


class BaseEvent(object):
    _public_methods_ = ["__on_event"]

    def __init__(self, event, event_handler: typing.Callable[[int, tuple], bool], event_source):
        """
            `event` - это интерфейс группы событий, например, ksKompasObjectNotify, ksDocumentFileNotify и т.д. См. разделы "Интерфейсы событий" в справке Компас APIv5 и APIv7.

            `event_handler` - это функция-обработчик группы событий. Первым параметром передается номер события (См. "Константы - Перечисления события" в справке Компас API); вторым параметром - кортеж (tuple) параметров функции-обработчика для события этого номера. Возвращаемое значение функции-обработчика, как правило, разрешает или запрещает дальнейшую обработку события штатным обработчиком Компаса, но может отличаться для функции-обработчика каждого конкретного номера события, см. справку Компас API.

            `event_source` - это объект-источик группы событий. См. справку Компас API: "...источником событий для подписки являются: ...".
        """
        self.__event = event
        self.__event_handler = event_handler
        self.__connection = None
        self.event_source = event_source

    def __del__(self):
        if not (self.__connection is None):
            self.__connection.Disconnect()
            del self.__connection

    def _invokeex_(self, command_id, locale_id, flags, params, result, exept_info):
        return self.__on_event(command_id, params)

    def _query_interface_(self, iid):
        if iid == self.__event.CLSID:
            return win32com.server.util.wrap(self)

    def advise(self):
        """
            Подписаться на события, то есть активировать "прослушку" событий и передавать обработку вызовами `event_handler(...)`.
        """
        if self.__connection is None and not (self.event_source is None):
            self.__connection = win32com.client.connect.SimpleConnection(self.event_source, self, self.__event.CLSID)

    def unadvise(self):
        """
            Отписаться от событий.
        """
        if self.__connection is not None and self.event_source is not None:
            self.__connection.Disconnect()
            self.__connection = None

    def __on_event(self, command_id, params):
        return self.__event_handler(command_id, params)


def register_handler(event_group, event_source, event_number: int, handler: typing.Callable[[typing.Any], bool]) -> BaseEvent:
    def _top_handler(en: int, params: tuple[typing.Any]) -> None:
        if en == event_number:
            handler(*[_try_do_dispatch(p) for p in params])

    be = BaseEvent(event_group, _top_handler, event_source)
    be.advise()
    return be


def _try_do_dispatch(o: object) -> object:
    try:
        return Dispatch(o)
    except:
        return o


if __name__ == "__main__":

    def f1(doc, doctype):
        print(doc, doctype)
        if doctype == DocumentTypeEnum.ksDocumentDrawing:
            d = Dispatch(doc)
            print(d.ksGetZoomScale())

    from src.macros.HEAD import *

    app = get_app7()
    doc, part = open_part("")

    register_handler(KAPI5.ksKompasObjectNotify, app, 4, f1)
    register_handler(KAPI7.ksDocument3DNotify7, doc, 1, lambda: print("begin rebuild") or True)

    from PyQt5 import QtWidgets

    a = QtWidgets.QApplication([])
    w = QtWidgets.QWidget()
    w.show()
    a.exec()
