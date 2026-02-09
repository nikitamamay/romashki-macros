"""
Вспомогательный модуль, предоставляет класс для задания на выполнение какого-то
действия в другом потоке с некоторой задержкой по времени после последней
вызванной команды на выполнение этого действия.

Задержка по времени актуальна для каких-то быстро выполняющихся событий,
например, для сохранения размеров и местоположения окна при их изменении.

"""

from time import time_ns, sleep
import threading


class DelayedHandler:
    def __init__(self) -> None:
        self._tasks = {}
        self._id_counter = 0

    def create_task(self, f, wait_time_seconds: float) -> int:
        tid = self.new_id()
        self._tasks[tid] = [
            time_ns(),
            int(wait_time_seconds * 10 ** 9),
            f,
            None
        ]
        self.create_thread(self._tasks[tid])
        return tid

    def do_task(self, task_id: int):
        task = self._tasks[task_id]
        f = task[2]
        th: threading.Thread = task[3]
        task[0] = time_ns()

        try:  # has not been started
            task[3].start()
        except:
            if task[3].is_alive():  # running
                pass
            else:  # dead
                self.create_thread(task)
                task[3].start()

    def new_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    def get_thread_function(self, task: list):
        def th_f() -> None:
            while task[0] + task[1] > time_ns():
                sleep(0.010)
            task[2]()
        return th_f

    def create_thread(self, task) -> None:
        task[3] = threading.Thread(
            target=self.get_thread_function(task),
            daemon=True,
        )


if __name__ == "__main__":
    from time import sleep

    start = time_ns()

    dh = DelayedHandler()
    tid = dh.create_task(lambda: print("hey", (time_ns() - start)/10**9), 1)
    dh.do_task(tid)

    for i in range(5):
        sleep(0.2)
        print("slept 0.2")
        dh.do_task(tid)

    # print('slept')

    print((time_ns() - start)/10**9)

    sleep(2)
    dh.do_task(tid)

    sleep(2)
    print((time_ns() - start)/10**9)
    sleep(2)
