"""
Модуль предоставляет вспомогательные функции для округления чисел, в том числе
и для преобразования округленных чисел в строки.

"""

import math

PRECISION_DIGIT_COUNT = 7


def do_floats_equal(a: float, b: float) -> bool:
    """
    Проверяет, что числа `a` и `b` равны в пределах `(10 ** -PRECISION_DIGIT_COUNT)`.
    """
    return abs(a - b) < 10 ** (-PRECISION_DIGIT_COUNT)


def round_N(x: float, n: int) -> float:
    """
    Округляет до `n` цифр после запятой.
    """
    return round_tail(round(x * 10 ** n) / (10 ** n))


def round_tail(x: float) -> float:
    """
    Округляет число до `PRECISION_DIGIT_COUNT` цифр после запятой.
    """
    # return round_N(x, PRECISION_DIGIT_COUNT)  # recusion
    n = PRECISION_DIGIT_COUNT
    return round(x * 10 ** n) / (10 ** n)


def round_to_number(x: float, number: float, middle_coefficient: float = 0.5) -> float:
    """
    Округляет `x` кратно числу `number` с коэффициентом границы округления `middle_coefficient`.

    Коэффициент границы округления `middle_coefficient` устанавливает относительную
    границу округления, выше которой число округляется вверх, ниже - вниз.
    Значение `middle_coefficient = 0.5` в итоге приводит к округлению по привычным
    правилам математики,
    значение `middle_coefficient = 0` приводит к округлению всегда вверх,
    значение `middle_coefficient = 1` - всегда вниз.

    Примеры:
    * при `number = 1; middle_coefficient = 0.5` число `x = 3.27` будет
    округлено до `3`;
    * при `number = 1; middle_coefficient = 0.25` число `x = 3.27` будет
    округлено до `4`;
    * при `number = 0.1; middle_coefficient = 0.5` число `x = 3.27` будет
    округлено до `3.3`;
    * при `number = 0.1; middle_coefficient = 0.75` число `x = 3.27` будет
    округлено до `3.2`.
    """
    if do_floats_equal(x, 0):
        return 0.0
    sign = -1 if x < 0 else +1
    # x = abs(x)
    return round_tail(
        sign * int(
            (abs(x) + (1 - middle_coefficient) * number) // number
        ) * number
    )


def round_digits(x: float, digits_count: int) -> float:
    """
    Округляет до `digits_count` значащих цифр.
    """
    c10 = count_10(x)
    return round_tail(round_N(x, -c10 + digits_count - 1))


def count_digits(x: float) -> int:
    """
    Возвращает количество значащих цифр.

    Предварительно применяет `round_tail()`.
    """
    return len(str(round_tail(x)).replace("-", "").replace(".", "").strip("0"))


def count_10(x: float) -> int:
    """
    Возвращает порядок числа `x`.

    То есть: `1 <= abs(x) / (10 ** count_10(x)) < 10`.
    """
    if (do_floats_equal(x, 0)):
        return 0
    return math.floor(math.log10(abs(x)))


def round_N_str(x: float, n: int) -> str:
    """
    Округляет до `n` цифр после запятой и возвращает строку.
    Включает незначащие нули справа.
    """
    less0 = "-" if x < 0 else ""
    x = round_N(abs(x), n)
    if do_floats_equal(x, 0):
        return "0"
    s = str(x) + "0" * 16
    dot_pos = s.find(".")
    if n <= 0:
        return less0 + s[:dot_pos]
    else:
        return less0 + s[:dot_pos + n + 1]


def round_digits_str(x: float, digits_count: int) -> str:
    """
    Округляет до `digits_count` значащих цифр и возвращает строку.
    Включает незначащие нули справа.
    """
    c10 = count_10(x)
    return round_N_str(x, -c10 + digits_count - 1)


def round_tail_str(x: float) -> str:
    """
    Округляет до `PRECISION_DIGIT_COUNT` цифр после запятой и возвращает строку.
    **Не включает** незначащие нули справа.
    """
    x = round_tail(x)
    s = str(x)
    if s.endswith(".0"):
        return s[:-2]
    return s


def round_to_number_str(x: float, number: float, middle_coefficient: float = 0.5) -> str:
    """
    Округляет `x` кратно `number` с коэффициентом границы округления `middle_coefficient`
    и возвращает строку. **Не включает** незначащие нули справа.

    См. также `round_to_number()`.
    """
    return round_tail_str(round_to_number(x, number, middle_coefficient))


if __name__ == '__main__':

    x = -193.26364298374
    y = 0.00123

    print(count_10(x), x, 10 ** count_10(x), x / (10**count_10(x)), sep="\t")
    print(count_10(y), y, 10 ** count_10(y), y / (10**count_10(y)), sep="\t")

    x = 3.27
    print(round_to_number(x, 1, 0.5), 1 * 0.5)
    print(round_to_number(x, 1, 0.25), 1 * 0.25)
    print(round_to_number(x, 0.1, 0.5), 0.5 * 0.5)
    print(round_to_number(x, 0.1, 0.75), 0.5 * 0.75)

