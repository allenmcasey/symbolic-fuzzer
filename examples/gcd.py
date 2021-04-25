def good_gcd(a: int, b: int) -> int:
    if a < b:
        c: int = a
        a = b
        b = c
    while b != 0:
        c: int = a
        a = b
        b = c % b
    return a


def bad_gcd(a: int, b: int) -> int:
    if a < b:
        c: int = a
        a = b
        b = c
        if b > c:
        	return b
    while b != 0:
        c: int = a
        a = b
        b = c % b
    return a
