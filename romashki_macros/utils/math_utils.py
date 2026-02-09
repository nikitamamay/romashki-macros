"""
Модуль предоставляет вспомогательные функции для округления чисел, в том числе
и для преобразования округленных чисел в строки.

"""

import math

PRECISION_DIGIT_COUNT = 7


def do_floats_equal(a: float, b: float) -> bool:
    """ Checks whether `a` and `b` are equals numbers within `(10 ** -PRECISION_DIGIT_COUNT)` """
    return abs(a - b) < 10 ** (-PRECISION_DIGIT_COUNT)


def round_N(x: float, n: int) -> float:
    """ Round to `n` digits after comma """
    return round_tail(round(x * 10 ** n) / (10 ** n))


def round_tail(x: float) -> float:
    """ Round a number to `PRECISION_DIGIT_COUNT` digits after comma """
    # return round_N(x, PRECISION_DIGIT_COUNT)  # recusion
    n = PRECISION_DIGIT_COUNT
    return round(x * 10 ** n) / (10 ** n)


def round_to_number(x: float, number: float, middle_coefficient: float = 0.5) -> float:
    """
        Round `x` to a number, so `x` becomes multiple of `number`.

        The `middle_coefficient` controls the middle point of rounding.
        `0` leads to rounding down, `1` leads to rounding up, and any different
        value sets the rounding middle point in fraction of `number`.

        For example, `middle_coefficient = 0.25` makes `x = 3.27` be rounded
        to `4`.
    """
    if do_floats_equal(x, 0):
        return 0.0
    sign = -1 if x < 0 else +1
    x = abs(x)
    return round_tail(
        sign * int(
            (x + middle_coefficient * number) // number
        ) * number
    )


def round_digits(x: float, digits_count: int) -> float:
    """ Round to given digits count """
    c10 = count_10(x)
    return round_tail(round_N(x, -c10 + digits_count - 1))


def count_digits(x: float) -> int:
    """ Count the digits in float's string representation """
    return len(str(round_tail(x)).replace("-", "").replace(".", "").strip("0"))


def count_10(x: float) -> int:
    """ Count the order of magnitude of a given `x` """
    if (do_floats_equal(x, 0)):
        return 0
    return math.floor(math.log10(abs(x)))


def round_N_str(x: float, n: int) -> str:
    """ Round to `n` digits after comma """
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
    """ Round to given digits count """
    c10 = count_10(x)
    return round_N_str(x, -c10 + digits_count - 1)


def round_tail_str(x: float) -> str:
    """ Round a number to `PRECISION_DIGIT_COUNT` digits after comma """
    x = round_tail(x)
    s = str(x)
    if s.endswith(".0"):
        return s[:-2]
    return s


def round_to_number_str(x: float, number: float, middle_coefficient: float = 0.5) -> str:
    """
        Round `x` to a number, so `x` becomes multiple of `number`.

        The `middle_coefficient` controls the middle point of rounding.
        `0` leads to rounding down, `1` leads to rounding up, and any different
        value sets the rounding middle point in fraction of `number`.

        For example, `middle_coefficient = 0.25` makes `x = 3.27` be rounded
        to `4`.
    """
    return round_tail_str(round_to_number(x, number, middle_coefficient))


if __name__ == '__main__':

    x = -193.26364298374

    print(x, round_to_number(x, 0.5))

