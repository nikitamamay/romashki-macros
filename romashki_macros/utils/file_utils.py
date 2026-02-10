"""
Модуль предоставляет функционал для работы с файлами и директориями.

"""

import sys
import os


def get_user_config_folder(program_name: str) -> str:
    """
    Формирует и возвращает абсолютный путь к папке с настройками приложения.
    * для windows: `C:\\Users\\<user>\\%AppData%\\Roaming\\<program_name>`;
    * для Linux: `/home/<user>/.config/<program_name>`.

    Не гарантирует существование папки на диске.
    """
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        folder_path = appdata if not appdata is None else ""
    elif sys.platform == "linux":
        folder_path = "~/.config"
    else:
        print(f'Your current platform is "{sys.platform}". Only "win32" and "linux" is supported for now. Sorry.')
        raise Exception(f"Unsupported platform '{sys.platform}'")
    return os.path.abspath(os.path.join(folder_path, program_name))


def is_folder_creatable(filepath: str) -> bool:
    """
    Проверяет, можно ли создать папку по пути `filepath`.

    При этом проверяет:
    * существует ли папка по этому пути уже;
    * существует ли диск (для windows);
    * существуют ли или возможно ли создать родительские папки;

    См. `is_file_creatable()`.
    """
    filepath = os.path.abspath(filepath)

    if os.path.exists(filepath):
        return os.path.isdir(filepath)

    if sys.platform == "win32":
        drive = os.path.splitdrive(filepath)[0]
        if not os.path.exists(drive):
            return False

    parent_dir = os.path.dirname(filepath)
    if is_folder_creatable(parent_dir):
        # TODO сделать здесь проверку на наличие прав для создания. Может, использовать touch с флагом проверки?
        return True

    return False


def is_file_creatable(filepath: str) -> bool:
    """
    Проверяет, можно ли создать файл по пути `filepath`.

    См. `is_folder_creatable()`.
    """
    return is_folder_creatable(os.path.dirname(os.path.abspath(filepath)))


def ensure_folder(filepath: str) -> None:
    """
    Рекурсивно создает папку `filepath` и её родительские папки, если их нет.
    """
    filepath = os.path.abspath(filepath)
    if not os.path.isdir(filepath):
        os.makedirs(filepath)


def ensure_file(filepath: str) -> None:
    """
    Обеспечивает наличие файла по пути `filepath` на диске.
    Если файла нет, создает его;
    перед этим рекурсивно создает родительские папки, если их тоже нет.
    """
    ensure_folder(os.path.dirname(os.path.abspath(filepath)))
    with open(filepath, "ab") as f:
        pass


def do_paths_intersect(path1: str, path2: str) -> bool:
    # TODO как эта функция должна называться, работать, и где её можно применить?
    sp1 = str(os.path.abspath(path1))
    sp2 = str(os.path.abspath(path2))
    if __debug__:
        print(sp1, sp2, sep="\n")
    return sp1.startswith(sp2) or sp2.startswith(sp1)


def split_path(path: str) -> tuple[str, str, str]:
    """
    Разбивает путь `path` на 3 (три) строки:
    * родительская папка;
    * имя файла без расширения (до точки);
    * расширение файла (с точкой включительно).
    """
    d, t = os.path.split(path)
    name, ext = os.path.splitext(t)
    return (d, name, ext)


def change_ext(path: str, new_ext: str) -> str:
    """
    Заменяет расширение у файла по пути `path` на расширение `new_ext`.

    Строка `new_ext` может начинаться с точки `"."` или с другого символа.
    При замене расширения файла двойных точек не образуется.
    """
    d, n, e = split_path(path)
    while new_ext.startswith("."):
        new_ext = new_ext[1:]
    return os.path.join(d, n + "." + new_ext)



if __name__ == "__main__":

    p1 = ""
    p2 = "../../hey/"

    print(do_paths_intersect(p1, p2))

