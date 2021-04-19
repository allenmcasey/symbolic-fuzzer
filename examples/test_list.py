def list_func(a: int, b: int, c: int) -> int:
    test: list[int] = [1, 2, 3]
    test[0] = a
    if test[0] > b:
        return test[1]
    elif test[0] < b:
        return test[2]
    else:
        return c


