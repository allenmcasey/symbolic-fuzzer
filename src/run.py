#!/usr/bin/env python3
import argparse
import os
import tempfile
import ast
import astor
from fuzzingbook.ControlFlow import gen_cfg

# ============================ Arguments ============================
parser = argparse.ArgumentParser(description='Argument parser')
# ============== required arguments ==============
parser.add_argument("-i", "--input", help="input program path", type=str, required=True)
# ============== optional arguments ==============
# parser.add_argument("-i", "--input", help="input program path", type=str, required=True)
args = parser.parse_args()


# ============================ read input program as code_string ============================
input_program = args.input
function_names = []
function_CFGs = {}

# create AST from source file; get string
astree = astor.parse_file(input_program)
code_string = astor.to_source(astree)

# get CFG of each defined fn
for node in ast.walk(astree):
	if isinstance(node, ast.FunctionDef):
		function_names.append(node.name)
		function_CFGs[node.name] = gen_cfg(astor.to_source(node))

# print(code_string)
# print(function_names)
# print(function_CFGs)

# ============================ Generation ============================
# Construct CFG and collect the paths
# from fuzzingbook.SymbolicFuzzer_original import SymbolicFuzzer
# Generate and print the path constraints in the program
# Each constraint should be traceable to the part of code that created the constraint

from fuzzingbook.SymbolicFuzzer_original import SimpleSymbolicFuzzer
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