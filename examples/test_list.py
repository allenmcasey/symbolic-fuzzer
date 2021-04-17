def list_func():
    test_list: list[int] = [1, 2, 3, 4, 5]
    test_list[3] = 6
    for i in range(0, len(test_list)):
        if test_list[i] % 2 == 0:
            test_list[i] = test_list[i] + 1
        else:
            test_list[i] = test_list[i] - 1
    print(test_list)
