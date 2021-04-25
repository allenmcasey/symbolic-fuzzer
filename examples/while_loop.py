

def while_loop(a: int, b: int):
    b *= b
    while(a > b):
        a += 1
        b -= 1
        if a == a + 1:
            return False
    return True 





