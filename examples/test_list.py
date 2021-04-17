def list_func() -> int:
    test_list: list[int] = [1, 2, 3]
    other_list: list[str] = ["this", "tests", "str", "lists"]
    other_list[1] = "tests our"
    test_list[0] = 6
    if test_list[0] == 0:
        test_list[1] = test_list[2] + 1
        other_list[1] = "confirms"
        return test_list[1]
    else:
        test_list[2] = test_list[1] - 1
        other_list[1] = "confirms"
        return test_list[2]

