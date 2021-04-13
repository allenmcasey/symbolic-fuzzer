#!/usr/bin/env python3
import argparse
import os
import tempfile


# ============================ Arguments ============================
parser = argparse.ArgumentParser(description='Argument parser')
# ============== required arguments ==============
parser.add_argument("-i", "--input", help="input program path", type=str, required=True)
# ============== optional arguments ==============
# parser.add_argument("-i", "--input", help="input program path", type=str, required=True)
args = parser.parse_args()



# ============================ read input program as code_string ============================
input_program = args.input
code_string = ""
function_names = []
with open(input_program, 'r') as f:
	for line in f:
		if "def " in line:
			name = line.split('(')[0].split(" ")[-1]
			function_names.append(name)
		code_string += line
# print(code_string)
# print(function_names)


# ============================ Generation ============================
# Construct CFG and collect the paths
# from fuzzingbook.SymbolicFuzzer_original import SymbolicFuzzer
# Generate and print the path constraints in the program
# Each constraint should be traceable to the part of code that created the constraint


from fuzzingbook.SymbolicFuzzer_modified import SimpleSymbolicFuzzer
symfz_ct = SimpleSymbolicFuzzer(code_string, function_names[0])

# from fuzzingbook.SymbolicFuzzer_original import SimpleSymbolicFuzzer
# symfz_ct = SimpleSymbolicFuzzer(check_triangle)

paths = symfz_ct.get_all_paths(symfz_ct.fnenter)
print(len(paths))
print(paths[0])
for item in paths[0]:
    print(item)


# ============================ Analysis ============================
# If a path is unsatisfiable, the fuzzer should generate the corresponding unsat core and the statements that it belongs to.