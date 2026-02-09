import sys
import os


def get_user_config_folder(program_name: str) -> str:
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
    filepath = os.path.abspath(filepath)
    drive = os.path.splitdrive(filepath)[0]
    if not os.path.exists(drive):
        return False
    while not os.path.exists(filepath):
        filepath = os.path.dirname(filepath)
    return True


def is_file_creatable(filepath: str) -> bool:
    return is_folder_creatable(os.path.dirname(os.path.abspath(filepath)))


def ensure_folder(filepath: str) -> None:
    filepath = os.path.abspath(filepath)
    if not os.path.isdir(filepath):
        os.makedirs(filepath)


def ensure_file(filepath: str) -> None:
    ensure_folder(os.path.dirname(os.path.abspath(filepath)))
    with open(filepath, "ab") as f:
        pass


def do_paths_intersect(path1: str, path2: str) -> bool:
    sp1 = str(os.path.abspath(path1))
    sp2 = str(os.path.abspath(path2))
    if __debug__:
        print(sp1, sp2, sep="\n")
    return sp1.startswith(sp2) or sp2.startswith(sp1)


def split_path(path: str) -> tuple[str, str, str]:
    d, t = os.path.split(path)
    name, ext = os.path.splitext(t)
    return (d, name, ext)


def change_ext(path: str, new_ext: str) -> str:
    d, n, e = split_path(path)
    while new_ext.startswith("."):
        new_ext = new_ext[1:]
    return os.path.join(d, n + "." + new_ext)


if __name__ == "__main__":

    p1 = ""
    p2 = "../../hey/"

    print(do_paths_intersect(p1, p2))

