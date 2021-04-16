def print_number(num: int):
    if num > 100:
        print('yes, this is greater than 100')
    elif num > 10:
        print('yes, this is greater than 10')
    else:
        print('Me: ', num)


def check_triangle(a: int, b: int, c: int):
    if a == b:
        if a == c:
            if b == c:
                print_number(100)
                return "Equilateral"
            else:
                return "Isosceles"
        else:
            return "Isosceles"
    else:
        if b != c:
            if a == c:
                print_number(100)
                return "Isosceles"
            else:
                return "Scalene"
        else:
            return "Isosceles"
