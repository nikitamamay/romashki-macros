"""
Макрос предоставляет функционал для включения и отключения режима "Не беспокоить".

Режим "Не беспокоить" (назван условно) - это отключение всплывающих окон,
(например, с просьбами перестроить 3D-модель или чертеж)
с автоматическим ответом "Нет" в этих окнах.

Следует иметь в виду, что некоторые операции в режиме "Не беспокоить" могут
работать некорректно. Даже те, которые не предполагают таких всплывающих окон.

"""

from .lib_macros.core import *


def set_silent_mode(is_silent: bool) -> None:
    """
    Устанавливает режим "Не беспокоить".
    """
    app = get_app7()
    app.HideMessage = 2 if is_silent else 0
    print(f"стало app.HideMessage={app.HideMessage} (is_silent={is_silent})")


def get_silent_mode() -> bool:
    """
    Проверяет, включен ли сейчас режим "Не беспокоить".
    """
    app = get_app7()
    return app.HideMessage != 0


if __name__ == "__main__":
    # set_silent_mode(True)
    set_silent_mode(False)
