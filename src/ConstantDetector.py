import re


# check string number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# check if there is constant value assigned to such argument
def check_constant(variable, constraints, location):
    constant = None
    for index, ct in enumerate(constraints):
        if index > location:
            break
        if variable in ct and ' == ' in ct and ',' not in ct:
            value = ct.split(' == ')[-1].strip()
            if is_number(value):
                constant = value
    print('#########################', constraints, constant)
    return constant


# check if there is a function call; constraint is a list of z3 tokens
def check_function_call(constraints, function_names):
    original_constraints = constraints
    # original_node_list = node_list
    # print(constraints)
    removed_indexs = []
    function_with_args = {}
    function_with_constant = {}
    for i, ct in enumerate(constraints):
        temp_list =  ct.split('(')
        # print(temp_list)
        for j, fc in enumerate(temp_list):
            if fc in function_names:
                arguments = temp_list[j+1]
                arguments = arguments.replace(')', '').split(',')
                fc_name_key = fc + '**' + str(i)
                # print(fc, i)
                function_with_args[fc_name_key] = arguments + [str(i)]
                removed_indexs.append(i)

    for fc_name_key in function_with_args:
        function_with_constant[fc_name_key] = []
        arguments = function_with_args[fc_name_key][:-1]
        location = function_with_args[fc_name_key][-1]
        for variable in arguments:
            variable = variable.strip()
            constant = None
            constant = check_constant(variable, constraints, int(location))
            # print(variable, constraints)
            if constant:
                function_with_constant[fc_name_key].append(constant)
            else:
                # print(constant)
                function_with_constant[fc_name_key].append('unknown')
            # print(constant)

    # delete if all args are unknown
    for fc_name_key in function_with_constant.copy():
        if all(v == 'unknown' for v in function_with_constant[fc_name_key]):
            del function_with_constant[fc_name_key]

    for i in reversed(sorted(removed_indexs)):
        original_constraints.pop(i)
        # original_node_list.pop(i)

    # print(function_with_constant)
    return original_constraints, function_with_constant