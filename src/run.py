#!/usr/bin/env python3
import argparse
import os
import tempfile
import ast
import astor
import sys
from fuzzingbook.ControlFlow import gen_cfg, PyCFG

# ============================ Arguments ============================
parser = argparse.ArgumentParser(description='Argument parser')
# ============== required arguments ==============
parser.add_argument("-i", "--input", help="input program path", type=str, required=True)
# ============== optional arguments ==============
parser.add_argument("-d", "--depth", help="max depth", type=int, default=10)
args = parser.parse_args()


# ============================ read input program as code_string ============================
input_program = args.input
depth = args.depth
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

#TODO need a graph to link functions once there is an external function call
# then re-construct paths to explore deeper
# print('---------------------------- ' + str(function_names[index])+ ' ----------------------------')
# print("Number of paths: ", len(paths))
# for i in range(len(paths)):
#     print(' ----------- path: ' + str(i)+ '----------- ')
#     print('Path contraints: ', symfz_ct.extract_constraints(paths[i]))
#     # TODO solve_path_constraint will fail when condition is an external function call
#     print('Contraints values: ',symfz_ct.solve_path_constraint(paths[i]))
#     for item in paths[i]:
#         print(item[0], ' --- ', item[1])


# sys.exit(0)
index = 0
from SymbolicFuzzer import AdvancedSymbolicFuzzer

asymfz_ct = AdvancedSymbolicFuzzer(code_string, function_names, index, py_cfg, max_depth=depth)

print(asymfz_ct.used_variables)

paths = asymfz_ct.get_all_paths(asymfz_ct.fnenter)

print('---------------------------- ' + str(function_names[index])+ ' ----------------------------')

num_of_paths = 0
used_constraint = []

for i in range(len(paths)):
    constraint = asymfz_ct.extract_constraints(paths[i].get_path_to_root())
    constraint_key = '__'.join(constraint)
    if constraint_key in used_constraint or len(constraint) < 2:
        continue
    num_of_paths += 1
    print(' ----------- path: ' + str(num_of_paths)+ '----------- ')
    used_constraint.append(constraint_key)
    print('Path contraints: ', constraint)
    # sys.exit(0)
    # TODO solve_path_constraint will fail when condition is an external function call
    # print(paths[i].get_path_to_root(), type(paths[i].get_path_to_root()) )


    # print('Contraints values: ',asymfz_ct.solve_path_constraint(paths[i].get_path_to_root()))
    # for item in paths[i].get_path_to_root():

print("Total number of paths: ", num_of_paths)
# for path in paths:
#     print(asymfz_ct.extract_constraints(path.get_path_to_root()))

# ============================ Analysis ============================
# If a path is unsatisfiable, the fuzzer should generate the corresponding unsat core and the statements that it belongs to.