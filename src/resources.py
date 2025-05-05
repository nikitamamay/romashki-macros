"""
Модуль предоставляет "обертки" для путей к файлам.

Эти "обертки" нужны для корректной компиляции проекта (с помощью pyinstaller)
со вставкой дополнительных файлов, как правило, картинок или иконок, в один
исполнительный файл.

"""


import os


BUNDLE_DIR = os.path.abspath(os.path.dirname(__file__))


def set_bundle_dir_by_main_file(main_file: str) -> None:
    """
    Usage in `main.py`:

        set_bundle_dir_by_main_file(__file__)
    """
    global BUNDLE_DIR
    BUNDLE_DIR = os.path.abspath(os.path.dirname(main_file))


def get_resource_path(path: str) -> str:
    return os.path.join(BUNDLE_DIR, path)


if __name__ == "__main__":
    print(__file__)
    print(BUNDLE_DIR)
    print(get_resource_path("icon/icon.ico"))
