#!/usr/bin/env python3
import argparse
import os
import tempfile
import ast
import astor
from fuzzingbook.ControlFlow import gen_cfg, PyCFG
import z3
from contextlib import contextmanager

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
index = 0
from SymbolicFuzzer import SimpleSymbolicFuzzer
symfz_ct = SimpleSymbolicFuzzer(code_string, function_names, index, py_cfg)
paths = symfz_ct.get_all_paths(symfz_ct.fnenter)

#TODO need a graph to link functions once there is an external function call
# then re-construct paths to explore deeper
print('---------------------------- ' + str(function_names[index])+ ' ----------------------------')
print("Number of paths: ", len(paths))

@contextmanager
def checkpoint(z3solver):
    z3solver.push()
    yield z3solver
    z3solver.pop()

for i in range(len(paths)):
    print(' ----------- path: ' + str(i)+ '----------- ')
    print('Path contraints: ', symfz_ct.extract_constraints(paths[i]))
    # TODO solve_path_constraint will fail when condition is an external function call
    print('Contraints values: ',symfz_ct.solve_path_constraint(paths[i]))
    for item in paths[i]:
        print(item[0], ' --- ', item[1])

    constraints = symfz_ct.extract_constraints(paths[i])

    with checkpoint(symfz_ct.z3):
        st = 'symfz_ct.z3.add(%s)' % ', '.join(constraints)
        print(st)
        # eval(st)
        if symfz_ct.z3.check() != z3.sat:
            print('unsatisfiable path')
            print(paths[i])


# ============================ Analysis ============================
# If a path is unsatisfiable, the fuzzer should generate the corresponding unsat core and the statements that it belongs to.
