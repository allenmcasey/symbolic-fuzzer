def is_divisible_by_3_5(num: int, num2: int):
    num = 15
    if num % 3 == 0:
        if num % 5 == 0:
            return True
        else:
            return False
    return False


def is_divisible_by_3_5_without_constant(num: int, num2: int):
    if num % 3 == 0:
        if num % 5 == 0:
            return True
        else:
            return False
    return False


def check_triangle(a: int, b: int, c: int):
    if a == b:
        if a == c:
            if b == c:
                return "Equilateral"
            else:
                return "Isosceles"
        else:
            return "Isosceles"
    else:
        if b != c:
            if a == c:
                return "Isosceles"
            else:
                return "Scalene"
        else:
            return "Isosceles"


def check_triangle2(a: int, b: int, c: int):
    a = 10
    if not is_divisible_by_3_5_without_constant(a, b):
        return 'Failed'

    if a == b:
        if a == c:
            if b == c:
                return "Equilateral"
            else:
                return "Isosceles"
        else:
            return "Isosceles"
    else:
        if b != c:
            if a == c:
                return "Isosceles"
            else:
                return "Scalene"
        else:
            return "Isosceles"


