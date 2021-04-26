

def func_a(a: int):
    if func_b(a):
        return func_c(a)
    elif a > 5:
        return False
    else:
        return True


def func_b(b: int):
    for i in range(5):
        b += 2
    b = 11
    if b > 10:
        return True
    else:
        return False


def func_c(c: int):
    if c > 13:
        return False
    else:
        return True
