#!/usr/bin/env python3
import argparse
import os
import tempfile
import ast
import astor
import sys
import inspect
import ConstantDetector
from fuzzingbook.ControlFlow import gen_cfg, PyCFG
from SymbolicFuzzer import AdvancedSymbolicFuzzer,SimpleSymbolicFuzzer


def main(args):
    # ============================ read input program as code_string ============================
    input_program = args.input
    selected_function_name = args.func
    check_constant = args.constant
    max_depth = args.depth
    max_iter = args.iter
    max_tries = args.tries

    # ============================ Initialization ============================
    function_names = []
    function_CFGs = {}
    py_cfg = PyCFG()
    # create AST from source file; get string
    astree = astor.parse_file(input_program)
    code_string = astor.to_source(astree)

    # ============================ CFG generation ============================
    # get CFG of each defined fn
    index = 0
    for node in ast.walk(astree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
            if selected_function_name == node.name:
                selected_index = index
            function_CFGs[node.name] = py_cfg.gen_cfg(astor.to_source(node))
            index += 1
    # ============================ Analysis ============================
    # only check selected function
    if selected_function_name:
        print_func(selected_function_name)
        analyze_program(code_string, function_names, selected_index, py_cfg, max_depth, max_tries, max_iter, check_constant)
    # analyze all functions from input program
    else:
        for i in range(len(function_names)):
            print_func(function_names[i])
            analyze_program(code_string, function_names, i, py_cfg, max_depth, max_tries, max_iter, check_constant)


# analysis
def analyze_program(code_string, function_names, index, py_cfg, max_depth, max_tries, max_iter, check_constant, insert_constant=[]):
    asymfz_ct = AdvancedSymbolicFuzzer(code_string, function_names, index, py_cfg,\
                max_depth=max_depth, max_tries=max_tries, max_iter=max_iter)
    # print(asymfz_ct.used_variables)
    # print("code_String", code_string)
    paths = asymfz_ct.get_all_paths(asymfz_ct.fnenter)

    num_of_paths = 0
    used_constraint = []
    functions_with_constant = {}

    for i in range(len(paths)):
        # print("i======", i)
        constraint = asymfz_ct.extract_constraints(paths[i].get_path_to_root())
        constraint_key = '__'.join(constraint)
        if constraint_key in used_constraint or len(constraint) < 2:
            continue
        num_of_paths += 1
        print('\n ---------------------------------------- path: ' + str(num_of_paths)+ ' ---------------------------------------- ')
        used_constraint.append(constraint_key)
        # print(constraint)
        constraint, function_with_constant = ConstantDetector.check_function_call(constraint, function_names)
        if insert_constant:
            constraint = generate_constraint_constant(insert_constant, constraint)
        if check_constant:
            functions_with_constant.update(function_with_constant)
        # constraints
        print('Contraint Path: ', constraint)

        print('Contraint Arguments: ', asymfz_ct.solve_constraint(constraint,paths[i].get_path_to_root()))

    if check_constant:
        print(check_constant)
        print('########################## RE-CHECK FUNCTIONS CALL WITH CONSTANT VALUES ########################## ')
        recheck_func_with_constant(functions_with_constant, code_string,\
                                function_names, index, py_cfg, max_depth, max_tries, max_iter)


# re-check some functions which with constant input argument values
def recheck_func_with_constant(functions_with_constant, code_string,\
                            function_names, index, py_cfg, max_depth, max_tries, max_iter):
    for fc_name_key in functions_with_constant:
        fc_name = fc_name_key.split('**')[0]
        arg_values = functions_with_constant[fc_name_key]
        insert_constant = []
        print("########################## ", fc_name, arg_values)
        for index, fn_name in enumerate(function_names):
            if fn_name == fc_name:
                analyze_program(code_string, function_names, index, py_cfg,
                        max_depth, max_tries, max_iter, False, insert_constant=arg_values)
                


# generate additional consraints for constant values
def generate_constraint_constant(insert_constant, constraint):
    constraint_args = constraint[0]
    if 'z3.And(' in constraint_args:
        args = constraint_args.split('(')[1].split(')')[0].split(',')
        if len(args) != len(insert_constant):
            print('args length does not match', args, insert_constant)
            return constraint
        for i, (x, y) in enumerate(zip(args, insert_constant)):
            if y != 'unknown':
                renamed_variable = x.split('==')[-1].strip()
                if is_constant_assigned(renamed_variable, constraint):
                    continue
                temp = renamed_variable + ' == ' + str(y)
                constraint.insert(1, temp)
    return constraint


# a variable can be assigned with constant value
def is_constant_assigned(renamed_variable, constraint):
    for c in constraint:
        if ' == ' in c:
            if ConstantDetector.is_number(c.split(' == ')[-1]):
                return True
    return False


# print function name
def print_func(s):
    fixed_string = "{0:>20}".format(s)
    print('\n############################################################################################### ')
    print('########################### Function Name: ' + fixed_string + '      ########################## ')
    print('############################################################################################### ')


# generate a report for UNSAT constraint path
def report():
    pass


# main 
if __name__ == "__main__":
    # ============================ Arguments ============================
    parser = argparse.ArgumentParser(description='Argument parser')
    # ============== required arguments ==============
    parser.add_argument("-i", "--input", help="input program path", type=str, required=True)
    # ============== optional arguments ==============
    parser.add_argument("-d", "--depth", help="max depth", type=int, default=10)
    parser.add_argument("-t", "--tries", help="max tries", type=int, default=10)
    parser.add_argument("-r", "--iter", help="max iterations", type=int, default=10)
    parser.add_argument("-f", "--func", help="specify function name", type=str, default=None)
    parser.add_argument("-c", "--constant", help="re-check function if constant detected", type=int, default=1)
    args = parser.parse_args()
    main(args)