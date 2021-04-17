def check_triangle(a: int, b: int, c: int):
    if not is_divisible_by_3_5(a):
        return "Failed"
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


def is_divisible_by_3_5(num: int):
    
    if num % 3 == 0:
        if num % 5 == 0:
            return True
        else:
            return False
    return False