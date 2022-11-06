
# "D:\NikitaFolder\engineering\290-CAD-Data\Kompas-3D\Macros and API\client.py"

import socket
import const


def send_cmd(cmd: str) -> None:
    """
    Sends the command.

    Raises `Exception` when something is wrong.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(10)
        s.connect(const.ADDRESS)
        s.sendall(bytes(cmd, encoding="utf-8"))


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Specify arguments!")
        input("Press any key...")
        sys.exit(1)

    cmd = sys.argv[1]
    print(f"Sending command: \"{cmd}\"")
    try:
        send_cmd(cmd)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        input("Press any key...")
    sys.exit(1)

