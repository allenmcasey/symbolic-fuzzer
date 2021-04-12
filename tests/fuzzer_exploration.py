from fuzzingbook.SymbolicFuzzer import AdvancedSymbolicFuzzer, used_vars

# example function
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


# create fuzzer
asymfz_ct = AdvancedSymbolicFuzzer(check_triangle, max_iter=10, max_tries=10, max_depth=10)

# print parameters and their types
print("\n", used_vars(check_triangle), "\n")

# collect and print all paths in function
ct_paths = asymfz_ct.get_all_paths(asymfz_ct.fnenter)
for path in ct_paths:
    print(asymfz_ct.extract_constraints(path.get_path_to_root()))
print("\n")

# generate inputs for paths
for i in range(1, 20):
    r = asymfz_ct.fuzz()
    v = check_triangle(r['a'].as_long(), r['b'].as_long(), r['c'].as_long())
    print(r, "result:", v)
    
