import re



# check if there is a function call; constraint is a list of z3 tokens
def check_function_call(constraints, function_names):
	original_constraints = constraints
	removed_indexs = []
	for i, ct in enumerate(constraints):
		temp_list =  ct.split('(')
		for j, fc in enumerate(temp_list):
			if fc in function_names:
				print('function call detected: ', fc)
				arguments = temp_list[j+1]
				print('args: ', arguments.replace(')', '').split(','))
				removed_indexs.append(i)
	for i in sorted(removed_indexs):
		original_constraints.pop(i)
	return original_constraints