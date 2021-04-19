#!/usr/bin/env python3
import argparse
import os
import tempfile
import ast
import astor
from fuzzingbook.ControlFlow import gen_cfg, PyCFG

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
py_cfg = PyCFG()

# create AST from source file; get string
astree = astor.parse_file(input_program)
code_string = astor.to_source(astree)

# get CFG of each defined fn
for node in ast.walk(astree):
	if isinstance(node, ast.FunctionDef):
		function_names.append(node.name)
		function_CFGs[node.name] = py_cfg.gen_cfg(astor.to_source(node))

# print(code_string)
# print(function_names)
# print(function_CFGs)

# ============================ Generation ============================
# Construct CFG and collect the paths
# from fuzzingbook.SymbolicFuzzer_original import SymbolicFuzzer
# Generate and print the path constraints in the program
# Each constraint should be traceable to the part of code that created the constraint

# NOTE: Simple fuzzer will NOT work with test_list.py
# index = 1
# from SymbolicFuzzer import SimpleSymbolicFuzzer
# symfz_ct = SimpleSymbolicFuzzer(code_string, function_names, index, py_cfg)
# paths = symfz_ct.get_all_paths(symfz_ct.fnenter)
#
# #TODO need a graph to link functions once there is an external function call
# # then re-construct paths to explore deeper
# print('---------------------------- ' + str(function_names[index])+ ' ----------------------------')
# print("Number of paths: ", len(paths))
# for i in range(len(paths)):
#     print(' ----------- path: ' + str(i)+ '----------- ')
#     print('Path contraints: ', symfz_ct.extract_constraints(paths[i]))
#     # TODO solve_path_constraint will fail when condition is an external function call
#     print('Contraints values: ',symfz_ct.solve_path_constraint(paths[i]))
#     for item in paths[i]:
#         print(item[0], ' --- ', item[1])

index = 0
from SymbolicFuzzer import AdvancedSymbolicFuzzer, used_identifiers
asymfz_ct = AdvancedSymbolicFuzzer(code_string, function_names, index, py_cfg)
paths = asymfz_ct.get_all_paths(asymfz_ct.fnenter)
for path in paths:
	# 	constraints = asymfz_ct.extract_constraints(path.get_path_to_root())
	# 	print(constraints)
	# 	# for constraint in constraints:
	# 	# 	used_identifiers(constraint)
	print(asymfz_ct.solve_path_constraint(path.get_path_to_root()))

# ============================ Analysis ============================
# If a path is unsatisfiable, the fuzzer should generate the corresponding unsat core and the statements that it belongs to.
