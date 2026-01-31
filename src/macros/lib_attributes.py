"""
Макрос-библиотека для работы с атрибутами объектов в 3D-модели.


Принцип работы
В Компас-документе или в lat-библиотеке объявлены типы атрибутов (KAPI7.IAttributeType).
Тип атрибута определяет тип хранимых данных (число-double, строка, таблица одна, таблица другая),
имя атрибута (название атрибута, которое видно при вызове окна "Атрибуты...") и другое.

Объекты (KAPI7.IModelObject) и документ (KAPI7.IKompasDocument) могут содержать
атрибуты (KAPI7.IAttribute), типы которых (KAPI7.IAttributeType) объявлены в Компас-документе
или в lat-библиотеке, с какими-то значениями (непосредственно данными).


~~~~~~

Внимание! В справке SDK Компас API допущена очередная неточность. Оказывается, это враньё:
```
    Интерфейс IAttribute
    ...
    Примечания:
    1. Интерфейс позволяет осуществлять работу с атрибутом.
    2. Интерфейс можно получить с помощью метода IKompasDocument1::CreateAttr.
```
ведь есть еще один --- и основной! --- способ. Должно быть дописано:
`3. Интерфейс можно получить с помощью метода IKompasDocument1::Attributes(long Key1, long Key2, long Key3, long Key4, double Numb, VARIANT Objects)`.
где в `Objects` можно передать массив (`list`) объектов, для которых следует получить атрибуты.

Здесь надо иметь в виду, что когда написано "Массив атрибутов документа", имеется в виду "Массив атрибутов любого объекта".
(API интерфейсов. Версия 7 > Документ > Базовые интерфейсы > Интерфейс IKompasDocument1 > IKompasDocument1 - свойства > Attributes)

Также в справке зачем-то метод `Attributes()` записан в свойства.

2026.01.31

"""

from src.macros.HEAD import *

from src import math_utils

import typing
import traceback
import os


class ksAttributeTypeEnum:
    """ Тип данных для типа атрибута """

    ksATUnknown = -1
    """ Неизвестный """

    ksATString = 0
    """ Строка """

    ksATDouble = 1
    """ Число """

    ksATFixedTable = 2
    """ Таблица с фиксированным числом строк """

    ksATVariableTable = 3
    """ Таблица с переменным числом строк """



def get_all_attribute_types(
        attribute_library_path: str = "",
        ) -> list[KAPI7.IAttributeType]:
    """
    Возвращает массив всех типов атрибутов, которые объявлены в lat-файле
    библиотеки типов атрибутов по пути `attribute_library_path`.

    Если `attribute_library_path == ""`, то возвращает типы атрибутов, объявленные
    в текущем документе.
    """
    app: KAPI7.IApplication = get_app7()
    atm: KAPI7.IAttrTypeMng = KAPI7.IAttrTypeMng(app)

    attr_types: list[KAPI7.IAttributeType] = ensure_list(atm.GetAttrTypes(attribute_library_path))
    return attr_types


def get_attribute_number(
        attr_name: str,
        attr_data_type: int,
        do_recreate_if_exists_but_wrong_type: bool = False
        ) -> float:
    """
    Возвращает уникальный идентификатор типа атрибута с именем `attr_name`.
    Если в документе такого типа атрибута нет, то создаёт его.

    `attr_data_type` - см. `ksAttributeTypeEnum`.
    """
    attr_types: list[KAPI7.IAttributeType] = get_all_attribute_types("")

    for at in attr_types:
        if at.TypeName == attr_name:
            print(f"Найден существующий тип атрибута '{attr_name}': {at.UniqueNumb}")

            if at.AttrType != attr_data_type:
                if do_recreate_if_exists_but_wrong_type:
                    at.AttrType = attr_data_type
                    print(f"\tДля типа атрибута '{attr_name}' изменен тип на {attr_data_type}.")
                    at.Update(None)
                else:
                    raise Exception(f"Некорректный тип атрибута '{at.AttrType}'")

            break
    else:
        at: KAPI7.IAttributeType = atm.CreateAttrType("")
        at.TypeName = attr_name
        at.AttrType = attr_data_type
        at.Update(None)
        print(f"Создается тип атрибута '{attr_name}': {at.UniqueNumb}")

    return at.UniqueNumb


def get_attribute(
        doc1: KAPI7.IKompasDocument1,
        obj: typing.Any,
        attr_number: float,
        do_create_if_not_found: bool = True,
        default_value: typing.Any = None,
        ) -> KAPI7.IAttribute:
    """
    Возвращает атрибут с идентификатором `attr_number` для объекта `obj`.

    Если атрибута нет и `do_create_if_not_found == True`, создает его со значением `default_value`.
    В противном случае выдает ошибку.

    Если для объекта `obj` уже заданы несколько атрибутов с идентификатором `attr_number`, то выдает ошибку.
    (Несколько атрибутов с одинаковыми `attr_number` были созданы во время тестов. В реальном применении такое не_случается?)
    """
    attrs: list[KAPI7.IAttribute] = ensure_list(doc1.Attributes(0, 0, 0, 0, attr_number, [obj]))
    if len(attrs) < 1:
        if do_create_if_not_found:
            attr: KAPI7.IAttribute = doc1.CreateAttr(attr_number, "", [obj])
            if attr is None:
                raise Exception(f"Не удалось создать атрибут с идентификатором {attr_number} у объекта {obj}")
            attr.SetValue(None, 0, 0, default_value)
        else:
            raise Exception(f"Не найден атрибут с уникальным идентификатором {attr_number} у объекта {obj}")
    elif len(attrs) > 1:
        raise Exception(f"Количество атрибутов с идентификатором {attr_number} у объекта {obj} больше одного! ({len(attrs)})")
    else:
        attr = attrs[0]
    return attr


def get_attr_value(
        doc1: KAPI7.IKompasDocument1,
        obj: typing.Any,
        attr_number: float,
        do_create_if_not_found: bool = True,
        default_value: typing.Any = None,
        ) -> typing.Any:
    """
    Возвращает значение атрибута с идентификатором `attr_number` для объекта `obj`.

    Если атрибута нет и `do_create_if_not_found == True`, создает его со значением `default_value`.
    В противном случае выдает ошибку.

    См. также `get_attribute()`.
    """
    attr: KAPI7.IAttribute = get_attribute(doc1, obj, attr_number, do_create_if_not_found, default_value)
    return attr.Value(0, 0)


def set_attr_value(
        doc1: KAPI7.IKompasDocument1,
        obj: typing.Any,
        attr_number: float,
        value: typing.Any,
        do_create_if_not_found: bool = True,
        ) -> bool:
    """
    Устанавливает значение атрибута с идентификатором `attr_number` для объекта `obj`.

    Если атрибут уже есть, перезаписывает его значение.

    Если атрибута нет и `do_create_if_not_found == True`, создает его.
    В противном случае выдает ошибку.
    """
    attr: KAPI7.IAttribute = get_attribute(doc1, obj, attr_number, do_create_if_not_found)
    return attr.SetValue(None, 0, 0, value)



def find_entities_with_attr(
        doc1: KAPI7.IKompasDocument1,
        attr_number: int,
        attr_value_callback: typing.Callable[[KAPI7.IModelObject, typing.Any], bool],
        is_single_entity: bool = False,
        ) -> list[KAPI7.IModelObject]:
    """
    Находит объекты модели, которые имеют атрибут с идентификатором `attr_number` с каким-то значением
    и вызывает последовательно для каждого `attr_value_callback(obj, attr_value)`.

    Пример использования: фильтрация объектов по значению атрибута:
    ```python
    entities42: list[KAPI7.IModelObject] = find_entities_with_attr(
        doc1,
        attr_id_number,
        lambda obj, x: do_floats_equal(x, 42.0),
        False,
    )
    ```

    Пример использования: редактирование объектов, которые имеют атрибут:
    ```python
    def foo(obj, attr_value):
        data = json.loads(attr_value)
        ...
        obj.Update()

    find_entities_with_attr(
        doc1,
        attr_id_number,
        foo,
        False,
    )
    ```
    """
    entities: list[KAPI7.IModelObject] = []
    objs: list[KAPI7.IModelObject] = ensure_list(doc1.ObjectsByAttr(0, 0, 0, 0, attr_number, None))
    for o in objs:
        attrs: list[KAPI7.IAttribute] = ensure_list(doc1.Attributes(0, 0, 0, 0, 0, [o]))
        for a in attrs:
            if attr_value_callback(o, a.Value(0, 0)):
                entities.append(o)
                if is_single_entity:
                    return entities
    if is_single_entity and len(entities) == 0:
        raise Exception(f"Не найдены объекты с идентификатором атрибута {attr_number}")
    return entities





if __name__ == "__main__":
    """
    Пример работы с атрибутами, который:
    1. Выводит (для справки) все существующие типы атрибутов в текущем документе;
    2. Создает или получает типы атрибутов, нужные далее;
    3. Создает точки по координатам и присваивает им атрибут (идентификатор в рамках нашей библиотеки);
    4. Создает линию и присваивает им атрибут (строку с идентификаторами двух точек, разделенными ';');
    5. Перестраивает все линии в модели по координатам точек. Здесь специально сделано неассоциативное перестроение,
       чтобы показать преимущество работы с атрибутами.
    6. Перезаписывает атрибут самой первой созданной точки (перезаписывает идентификатор).
       Поэтому при следующем запуске скрипта 'Отрезок:1' не_удастся перестроить, так как для него сохранён
       старый (неизмененный) идентификатор первой точки.

    Скрипт можно запустить несколько раз и редактировать координаты точек.

    Иногда (?) при первом запуске скрипта на новом документе (3D-модели) скрипт выдает, что в документе
    уже существует тип атрибута "RM_LINE". Это ошибка. В таком случае стоит перезапустить Компас.
    """

    import random

    ### Вывод всех типов атрибутов в текущем документе
    print(f"\n### Вывод всех типов атрибутов в текущем документе")

    def get_str_of_attr_type(x):
        if x == ksAttributeTypeEnum.ksATString:
            return "Строка"
        if x == ksAttributeTypeEnum.ksATDouble:
            return "Число"
        if x == ksAttributeTypeEnum.ksATFixedTable:
            return "Таблица с фиксированным числом строк"
        if x == ksAttributeTypeEnum.ksATVariableTable:
            return "Таблица с переменным числом строк"
        return "Неизвестный"

    attr_types: list[KAPI7.IAttributeType] = get_all_attribute_types()

    print(f"Всего типов атрибутов в документе: {len(attr_types)}")
    for at in attr_types:
        print(f"TypeName='{at.TypeName}', AttrType={at.AttrType} ({get_str_of_attr_type(at.AttrType)}), UniqueNumb={at.UniqueNumb}, FileName='{at.FileName}'")

    ### Создание или получение идентификаторов атрибутов по их названиям
    print(f"\n### Создание или получение идентификаторов атрибутов по их названиям")

    LINE_ATTR = "RM_LINE"
    RM_ID_ATTR = "RM_ID"

    line_attr_number = get_attribute_number(LINE_ATTR, ksAttributeTypeEnum.ksATString)
    rm_id_attr_number = get_attribute_number(RM_ID_ATTR, ksAttributeTypeEnum.ksATDouble)

    doc, part = open_part()
    doc1 = KAPI7.IKompasDocument1(doc)

    ### Создание точек
    print(f"\n### Создание точек")

    def get_unique_id() -> int:
        return random.randint(0, 10**7)

    def create_point():
        points: KAPI7.IPoints3D = KAPI7.IModelContainer(part).Points3D
        point: KAPI7.IPoint3D = points.Add()
        point.X = float(random.randint(-200, 200))
        point.Y = float(random.randint(-200, 200))
        point.Z = float(random.randint(-200, 200))
        point.Update()
        print(f"Создана точка '{point.Name}'")
        point_id = get_unique_id()
        set_attr_value(doc1, point, rm_id_attr_number, point_id)
        return point_id

    pid1 = create_point()
    pid2 = create_point()

    ### Создание линии
    print(f"\n### Создание линии")

    line_segments: KAPI7.ILineSegments3D = KAPI7.IAuxiliaryGeomContainer(part).LineSegments3D
    ls: KAPI7.ILineSegment3D = line_segments.Add()
    ls.SetPoint(True, 0, 0, 0)
    ls.SetPoint(False, 1, 1, 1)
    ls.Update()
    print(f"Создана линия '{ls.Name}'")
    set_attr_value(doc1, ls, line_attr_number, f"{pid1};{pid2}")

    ### Перестроение всех линий
    print(f"\n### Перестроение всех линий")

    def rebuild_lines(line: KAPI7.ILineSegment3D, attr_value):
        try:
            object_id1, object_id2 = [float(x) for x in attr_value.split(";")]

            point1: KAPI7.IPoint3D = find_entities_with_attr(doc1, rm_id_attr_number, lambda o, x: math_utils.do_floats_equal(x, object_id1), True)[0]
            x, y, z = point1.X, point1.Y, point1.Z
            line.SetPoint(True, x, y, z)

            point2: KAPI7.IPoint3D = find_entities_with_attr(doc1, rm_id_attr_number, lambda o, x: math_utils.do_floats_equal(x, object_id2), True)[0]
            x, y, z = point2.X, point2.Y, point2.Z
            line.SetPoint(False, x, y, z)

            line.Update()

            print(f"Перестроена линия '{line.Name}' по точкам '{point1.Name}' и '{point2.Name}'")
        except Exception as e:
            print(f"Ошибка: {e.__class__.__name__}: {str(e)}")
        return True

    find_entities_with_attr(doc1, line_attr_number, rebuild_lines)

    ### Перезапись значения атрибута
    print(f"\n### Перезапись значения атрибута")

    points: KAPI7.IPoints3D = KAPI7.IModelContainer(part).Points3D
    point: KAPI7.IPoint3D = points.Point3D(0)  # для самой первой точки
    set_attr_value(doc1, point, rm_id_attr_number, get_unique_id())
