"""
Модуль предоставляет интерфейсы, классы и функции для удобной работы с JSON,
в частности, для кодирования и декодирования произвольных объектов, чтения и
записи JSON-файлов.

"""

import typing
import json


CLASS_NAME_KEY = "CLASS_NAME"


def construct_class_dict(classes: list):
    class_names = {}
    for c in classes:
        class_names[c.__name__] = c
    return class_names


class JSONable:
    def to_json_base(self):
        return { CLASS_NAME_KEY: self.__class__.__name__ }

    def to_json(self) -> dict:
        d = self.to_json_base()
        v = vars(self).copy()
        for key in v:
            if not key.startswith("_"):
                d[key] = v[key]
        return d

    def from_json_base(self, d: dict):
        if CLASS_NAME_KEY in d:
            del d[CLASS_NAME_KEY]
        for key in d:
            vars(self)[key] = d[key]

    @staticmethod
    def from_json(d: dict):
        raise NotImplementedError("JSONable.from_json(dict) is not implemented")

    @staticmethod
    def encode(obj):
        if isinstance(obj, JSONable):
            return obj.to_json()
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

    @staticmethod
    def check_dict(obj):
        return isinstance(obj, dict) and CLASS_NAME_KEY in obj


### ----- DECODERS -----


def decoder_classes(general: list, special: list = []):
    class_names = construct_class_dict(general + special)

    def decode(obj):
        if JSONable.check_dict(obj) \
                and obj[CLASS_NAME_KEY] in class_names:
            class_name = class_names[obj[CLASS_NAME_KEY]]
            # Decoding nested objects
            for key in obj:
                if key == CLASS_NAME_KEY: continue
                obj[key] = decode(obj[key])
            # Special
            if class_name in special:
                return class_name.from_json(obj)
            # General
            else:
                result: JSONable = class_names[obj[CLASS_NAME_KEY]]()
                result.from_json_base(obj)
                return result
        return obj

    return decode


def mix_decoders(*decoders: typing.Callable[[object], typing.Any]):
    def decode(obj):
        old_type = type(obj)
        for f in decoders:
            obj = f(obj)
            if type(obj) != old_type:
                break
        return obj
    return decode


### ----- FILE INTERFACE -----


def save_json(path: str, target: object):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(target, f, default=JSONable.encode, ensure_ascii=False, indent=2)


def load_json(path: str, object_hook: typing.Callable[[object], typing.Any]):
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f, object_hook=object_hook)
    return obj


def load_json_with_classes(path: str, general: list = [], special: list = []):
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f, object_hook=decoder_classes(general, special))
    return obj



if __name__ == "__main__":
    class A(JSONable):
        def __init__(self, i = 0) -> None:
            super().__init__()
            self.i = i
            self.x = 20
            self.y = ["hey", "bye"]

    class B(JSONable):
        def __init__(self, a) -> None:
            super().__init__()
            self.z = [A(), 20, "qwerty"]
            self.a = a
            self._arr = []

        def foo(self):
            for i in range(self.a):
                self._arr.append(A(i))

        def to_json(self) -> dict:
            d = super().to_json()
            d["arr"] = self._arr
            return d

        def from_json(d: dict):
            b = B(d["a"])
            for el in d["arr"]:
                b._arr.append(el)
            return b

    a = A()
    b = B(3)

    b.foo()

    d = {
        "a": a,
        "b": b,
        "o": 10,
        "p": "word",
        "l": ["b", B(1)],
    }

    save_json("test.json", d)
    dd = load_json("test.json", [A], [B])
    bb = dd["b"]

    print(dd)
    print(vars(bb))
    for el in bb._arr:
        print(el.i)
