#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This material is part of "The Fuzzing Book".
# Web site: https://www.fuzzingbook.org/html/SymbolicFuzzer.html
# Last change: 2019-12-21 16:38:57+01:00
#
# !/
# Copyright (c) 2018-2020 CISPA, Saarland University, authors, and contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys
import inspect
import z3
import ast
import astor
from fuzzingbook.ControlFlow import PyCFG, CFGNode, to_graph, gen_cfg
from graphviz import Source, Graph
from fuzzingbook.Fuzzer import Fuzzer
from contextlib import contextmanager

# ============================ Helper Functions ============================


def show_cfg(fn, **kwargs):
    return Source(to_graph(gen_cfg(inspect.getsource(fn)), **kwargs))


def get_annotations(fn):
    sig = inspect.signature(fn)
    return ([(i.name, i.annotation)
             for i in sig.parameters.values()], sig.return_annotation)


SYM_VARS = {
    int: (
        z3.Int, z3.IntVal), float: (
            z3.Real, z3.RealVal), str: (
                z3.String, z3.StringVal)}


def get_symbolicparams(fn):
    params, ret = get_annotations(fn)
    return [SYM_VARS[typ][0](name)
            for name, typ in params], SYM_VARS[ret][0]('__return__')


def prefix_vars(astnode, prefix):
    if isinstance(astnode, ast.BoolOp):
        return ast.BoolOp(astnode.op,
                          [prefix_vars(i, prefix) for i in astnode.values], [])
    elif isinstance(astnode, ast.BinOp):
        return ast.BinOp(
            prefix_vars(astnode.left, prefix), astnode.op,
            prefix_vars(astnode.right, prefix))
    elif isinstance(astnode, ast.UnaryOp):
        return ast.UnaryOp(astnode.op, prefix_vars(astnode.operand, prefix))
    elif isinstance(astnode, ast.Call):
        return ast.Call(prefix_vars(astnode.func, prefix),
                        [prefix_vars(i, prefix) for i in astnode.args],
                        astnode.keywords)
    elif isinstance(astnode, ast.Compare):
        return ast.Compare(
            prefix_vars(astnode.left, prefix), astnode.ops,
            [prefix_vars(i, prefix) for i in astnode.comparators])
    elif isinstance(astnode, ast.Name):
        if astnode.id in {'And', 'Or', 'Not'}:
            return ast.Name('z3.%s' % (astnode.id), astnode.ctx)
        else:
            return ast.Name('%s%s' % (prefix, astnode.id), astnode.ctx)
    elif isinstance(astnode, ast.Return):
        return ast.Return(prefix_vars(astnode.value, env))
    else:
        return astnode


def get_expression(src):
    return ast.parse(src).body[0].value


def to_src(astnode):
    # print("to_src", astor.to_source(astnode))
    return astor.to_source(astnode).strip()


def z3_names_and_types(z3_ast):
    hm = {}
    children = z3_ast.children()
    if children:
        for c in children:
            hm.update(z3_names_and_types(c))
    else:
        # HACK.. How else to distinguish literals and vars?
        if (str(z3_ast.decl()) != str(z3_ast.sort())):
            hm["%s" % str(z3_ast.decl())] = 'z3.%s' % str(z3_ast.sort())
        else:
            pass


def used_identifiers(src):
    def names(astnode):
        lst = []
        if isinstance(astnode, ast.BoolOp):
            for i in astnode.values:
                lst.extend(names(i))
        elif isinstance(astnode, ast.BinOp):
            lst.extend(names(astnode.left))
            lst.extend(names(astnode.right))
        elif isinstance(astnode, ast.UnaryOp):
            lst.extend(names(astnode.operand))
        elif isinstance(astnode, ast.Call):
            for i in astnode.args:
                lst.extend(names(i))
        elif isinstance(astnode, ast.Compare):
            lst.extend(names(astnode.left))
            for i in astnode.comparators:
                lst.extend(names(i))
        elif isinstance(astnode, ast.Subscript):
            lst.append(to_src(astnode))
        elif isinstance(astnode, ast.Name):
            lst.append(astnode.id)
        elif isinstance(astnode, ast.Expr):
            lst.extend(names(astnode.value))
        elif isinstance(astnode, (ast.Num, ast.Str, ast.Tuple, ast.NameConstant)):
            pass
        elif isinstance(astnode, ast.Assign):
            for t in astnode.targets:
                lst.extend(names(t))
            lst.extend(names(astnode.value))
        elif isinstance(astnode, ast.Module):
            for b in astnode.body:
                lst.extend(names(b))
        else:
            raise Exception(str(astnode))
        return list(set(lst))
    return names(ast.parse(src))


SYM_VARS_STR = {
    k.__name__: ("z3.%s" % v1.__name__, "z3.%s" % v2.__name__)
    for k, (v1, v2) in SYM_VARS.items()
}


Function_Summaries = {}
Function_Summaries['func_name'] = {
        'predicate': "",
        'vars': {}}


def translate_to_z3_name(v):
    return SYM_VARS_STR[v][0]

def declarations(astnode, hm=None):
    if hm is None:
        hm = {}
    if isinstance(astnode, ast.Module):
        for b in astnode.body:
            declarations(b, hm)
    elif isinstance(astnode, ast.FunctionDef):
        #hm[astnode.name + '__return__'] = translate_to_z3_name(astnode.returns.id)
        for a in astnode.args.args:
            # print(a.annotation, type(a.annotation))
            hm[a.arg] = translate_to_z3_name(a.annotation.id)
        for b in astnode.body:
            declarations(b, hm)
    elif isinstance(astnode, ast.Call):
        # get declarations from the function summary.
        n = astnode.function
        assert isinstance(n, ast.Name)  # for now.
        name = n.id
        hm.update(dict(Function_Summaries[name]['vars']))
    elif isinstance(astnode, ast.AnnAssign):
        assert isinstance(astnode.target, ast.Name)
        if isinstance(astnode.value, ast.List):
            if isinstance(astnode.value.elts[0], ast.Num):
                element_type = type(astnode.value.elts[0].n)
            else:
                element_type = type(astnode.value.elts[0].s)
            list_name = astnode.target.id
            for i in range(0, len(astnode.value.elts)):
                hm["%s_%d" % (list_name, i)] = translate_to_z3_name(element_type.__name__)
        else:
            hm[astnode.target.id] = translate_to_z3_name(astnode.annotation.id)
    elif isinstance(astnode, ast.Assign):
        if not isinstance(astnode.targets[0], ast.Subscript):
            for t in astnode.targets:
                assert isinstance(t, ast.Name)
                assert t.id in hm
    elif isinstance(astnode, ast.AugAssign):
        assert isinstance(astnode.target, ast.Name)
        assert astnode.target.id in hm
    elif isinstance(astnode, (ast.If, ast.For, ast.While)):
        for b in astnode.body:
            declarations(b, hm)
        for b in astnode.orelse:
            declarations(b, hm)
    elif isinstance(astnode, ast.Return):
        pass
    else:
        return {}
        # raise Exception(to_src(astnode))
    return hm


def define_symbolic_vars(fn_vars, prefix):
    sym_var_dec = ', '.join([prefix + n for n in fn_vars])
    sym_var_def = ', '.join(["%s('%s%s')" % (t, prefix, n) for n, t in fn_vars.items()])
    result = "%s = %s" % (sym_var_dec, sym_var_def)
    return result


def gen_fn_summary(prefix, fn):
    summary = Function_Summaries[fn.__name__]['predicate']
    fn_vars = Function_Summaries[fn.__name__]['vars']
    decl = define_symbolic_vars(fn_vars, prefix)
    summary_ast = get_expression(summary)
    return decl, to_src(prefix_vars(summary_ast, prefix))


def used_vars(fn):
    return declarations(ast.parse(inspect.getsource(fn)))


@contextmanager
def checkpoint(z3solver):
    z3solver.push()
    yield z3solver
    z3solver.pop()


MAX_DEPTH = 100
MAX_TRIES = 100
MAX_ITER = 100


# ============================ Simple Symbolic Fuzzer ============================


class SimpleSymbolicFuzzer(Fuzzer):

    def __init__(self, arbitary_code, function_names, index, py_cfg, **kwargs):

        self.fn_name = function_names[index]
        self.function_names = function_names
        self.py_cfg = py_cfg
        self.fnenter, self.fnexit = self.py_cfg.functions[self.fn_name]

        # a dictionary of used variables; ex. {'a': 'z3.Int', 'b': 'z3.Int', 'c': 'z3.Int'}
        self.used_variables = declarations(ast.parse(arbitary_code))

        # a list of arguments; ex. ['a', 'b', 'c']
        self.fn_args = list(self.used_variables.keys())

        self.z3 = z3.Solver()

        self.paths = None
        self.last_path = None

        self.options(kwargs)
        self.process()

    def options(self, kwargs):
        self.max_depth = kwargs.get('max_depth', MAX_DEPTH)
        self.max_tries = kwargs.get('max_tries', MAX_TRIES)
        self.max_iter = kwargs.get('max_iter', MAX_ITER)
        self._options = kwargs

    def get_all_paths(self, fenter, depth=0):
        if depth > self.max_depth:
            raise Exception('Maximum depth exceeded')
        if not fenter.children:
            return [[(0, fenter)]]

        fnpaths = []
        for idx, child in enumerate(fenter.children):
            child_paths = self.get_all_paths(child, depth + 1)
            for path in child_paths:
                # In a conditional branch, idx is 0 for IF, and 1 for Else
                fnpaths.append([(idx, fenter)] + path)
        return fnpaths

    def process(self):
        self.paths = self.get_all_paths(self.fnenter)
        self.last_path = len(self.paths)

    def extract_constraints(self, path):
        predicates = []
        for (idx, elt) in path:
            if isinstance(elt.ast_node, ast.AnnAssign):
                if elt.ast_node.target.id in {'_if', '_while'}:
                    s = to_src(elt.ast_node.annotation)
                    predicates.append(("%s" if idx == 0 else "z3.Not(%s)") % s)
                elif isinstance(elt.ast_node.annotation, ast.Call):
                    assert elt.ast_node.annotation.func.id == self.fn_name
                else:
                    node = elt.ast_node
                    t = ast.Compare(node.target, [ast.Eq()], [node.value])
                    predicates.append(to_src(t))
            elif isinstance(elt.ast_node, ast.Assign):
                node = elt.ast_node
                t = ast.Compare(node.targets[0], [ast.Eq()], [node.value])
                predicates.append(to_src(t))
            else:
                pass
        return predicates

    def solve_path_constraint(self, path):
        # re-initializing does not seem problematic.
        # a = z3.Int('a').get_id() remains the same.
        constraints = self.extract_constraints(path)
        decl = define_symbolic_vars(self.used_variables, '')
        exec(decl)

        solutions = {}
        with checkpoint(self.z3):
            st = 'self.z3.add(%s)' % ', '.join(constraints)
            eval(st)
            if self.z3.check() != z3.sat:
                return {}
            m = self.z3.model()
            solutions = {d.name(): m[d] for d in m.decls()}
            my_args = {k: solutions.get(k, None) for k in self.fn_args}
        predicate = 'z3.And(%s)' % ','.join(["%s == %s" % (k, v) for k, v in my_args.items()])
        eval('self.z3.add(z3.Not(%s))' % predicate)
        return my_args

    def get_next_path(self):
        self.last_path -= 1
        if self.last_path == -1:
            self.last_path = len(self.paths) - 1
        return self.paths[self.last_path]

    def fuzz(self):
        for i in range(self.max_tries):
            res = self.solve_path_constraint(self.get_next_path())
            if res:
                return res
        return {}


def rename_variables(astnode, env):
    if isinstance(astnode, ast.BoolOp):
        fn = 'z3.And' if isinstance(astnode.op, ast.And) else 'z3.Or'
        return ast.Call(
            ast.Name(fn, None),
            [rename_variables(i, env) for i in astnode.values], [])
    elif isinstance(astnode, ast.BinOp):
        return ast.BinOp(
            rename_variables(astnode.left, env), astnode.op,
            rename_variables(astnode.right, env))
    elif isinstance(astnode, ast.UnaryOp):
        if isinstance(astnode.op, ast.Not):
            return ast.Call(
                ast.Name('z3.Not', None),
                [rename_variables(astnode.operand, env)], [])
        else:
            return ast.UnaryOp(astnode.op,
                               rename_variables(astnode.operand, env))
    elif isinstance(astnode, ast.Call):
        return ast.Call(astnode.func,
                        [rename_variables(i, env) for i in astnode.args],
                        astnode.keywords)
    elif isinstance(astnode, ast.Compare):
        return ast.Compare(
            rename_variables(astnode.left, env), astnode.ops,
            [rename_variables(i, env) for i in astnode.comparators])
    elif isinstance(astnode, ast.Name):
        if astnode.id not in env:
            env[astnode.id] = 0
        num = env[astnode.id]
        return ast.Name('_%s_%d' % (astnode.id, num), astnode.ctx)

    # fixed
    elif isinstance(astnode, ast.Subscript):
        identifier = to_src(astnode)
        name = identifier[:-3] + '_' + identifier[-2]
        if name not in env:
            env[name] = 0
        num = env[name]
        return ast.Name('_%s_%d' % (name, num), astnode.ctx)
    elif isinstance(astnode, ast.Return):
        return ast.Return(rename_variables(astnode.value, env))
    else:
        return astnode


def to_single_assignment_predicates(path):
    env = {}
    new_path = []
    node_list = []
    completed_path = False
    for i, node in enumerate(path):
        ast_node = node.cfgnode.ast_node
        new_node = None
        if isinstance(ast_node, ast.AnnAssign) and ast_node.target.id in {
                'exit'}:
            completed_path = True
            new_node = None
        elif isinstance(ast_node, ast.AnnAssign) and ast_node.target.id in {'enter'}:
            args = [
                ast.parse(
                    "%s == _%s_0" %
                    (a.id, a.id)).body[0].value for a in ast_node.annotation.args]
            new_node = ast.Call(ast.Name('z3.And', None), args, [])
        elif isinstance(ast_node, ast.AnnAssign) and ast_node.target.id in {'_if', '_while'}:
            new_node = rename_variables(ast_node.annotation, env)
            if node.order != 0:
                # assert node.order == 1
                if node.order != 1:
                    return [], False
                new_node = ast.Call(ast.Name('z3.Not', None), [new_node], [])

        # fixed
        elif isinstance(ast_node, ast.AnnAssign):
            if isinstance(ast_node.value, ast.List):
                for idx, element in enumerate(ast_node.value.elts):
                    assigned = ast_node.target.id + "_" + str(idx)
                    val = [rename_variables(element, env)]
                    env[assigned] = 0
                    target = ast.Name('_%s_%d' % (assigned, env[assigned]), None)
                    new_path.append(ast.Expr(ast.Compare(target, [ast.Eq()], val)))
                    node_list.append(node)
                pass
            else:
                assigned = ast_node.target.id
                val = [rename_variables(ast_node.value, env)]
                env[assigned] = 0 if assigned not in env else env[assigned] + 1
                target = ast.Name('_%s_%d' % (assigned, env[assigned]), None)
                new_node = ast.Expr(ast.Compare(target, [ast.Eq()], val))

        # fixed
        elif isinstance(ast_node, ast.Assign):
            if isinstance(ast_node.targets[0], ast.Subscript):
                identifier = to_src(ast_node.targets[0])
                assigned = identifier[:-3] + '_' + identifier[-2]
                val = [rename_variables(ast_node.value, env)]
                env[assigned] = 0 if assigned not in env else env[assigned] + 1
                target = ast.Name('_%s_%d' % (assigned, env[assigned]), None)
            else:
                assigned = ast_node.targets[0].id
                val = [rename_variables(ast_node.value, env)]
                env[assigned] = 0 if assigned not in env else env[assigned] + 1
                target = ast.Name('_%s_%d' % (assigned, env[assigned]), None)
            new_node = ast.Expr(ast.Compare(target, [ast.Eq()], val))
        elif isinstance(ast_node, (ast.Return, ast.Pass)):
            new_node = None
        else:
            continue
            # s = "NI %s %s" % (type(ast_node), ast_node.target.id)
            # raise Exception(s)


        new_path.append(new_node)
        if(new_node):
            node_list.append(node)
        # for node in path:
        #     cfgnode_json = node.cfgnode.to_json()
        #     at = cfgnode_json['at']
        #     ast = cfgnode_json['ast']
        #     unsat_info_dict['*statement*'].append("\tLine" + str(at) + ":" + str(ast))
        #     print("\tLine", at, ":", ast)

    return new_path, completed_path, node_list


def identifiers_with_types(identifiers, defined):
    with_types = dict(defined)
    for i in identifiers:
        if i[0] == '_':
            if i.count('_') > 2:
                last = i.rfind('_')
                name = i[1:last]
            else:
                nxt = i[1:].find('_', 1)
                name = i[1:nxt + 1]
            assert name in defined
            typ = defined[name]
            with_types[i] = typ
    return with_types
  
  
# ============================ PNode ============================


class PNode:

    def __init__(self, idx, cfgnode, parent=None, order=0, seen=None):
        self.seen = {} if seen is None else seen
        self.max_iter = MAX_ITER
        self.idx, self.cfgnode, self.parent, self.order = idx, cfgnode, parent, order

    def __repr__(self):
        return "PNode:%d[%s order:%d]" % (self.idx, str(self.cfgnode), self.order)

    def copy(self, order):
        p = PNode(self.idx, self.cfgnode, self.parent, order, self.seen)
        assert p.order == order
        return p

    def explore(self):
        ret = []
        for (i, n) in enumerate(self.cfgnode.children):
            key = "[%d]%s" % (self.idx + 1, n)
            ccount = self.seen.get(key, 0)
            if ccount > self.max_iter:
                continue  # drop this child
            self.seen[key] = ccount + 1
            pn = PNode(self.idx + 1, n, self.copy(i), seen=self.seen)
            ret.append(pn)
        return ret

    def get_path_to_root(self):
        path = []
        n = self
        while n:
            path.append(n)
            n = n.parent
        # print(list(reversed(path)))
        return list(reversed(path))

    def __str__(self):
        path = self.get_path_to_root()
        ssa_path = to_single_assignment_predicates(path)
        return ', '.join([to_src(p) for p in ssa_path])

 
# ============================ Advanced Symbolic Fuzzer ============================


class AdvancedSymbolicFuzzer(SimpleSymbolicFuzzer):
    def options(self, kwargs):
        super().options(kwargs)

    def extract_constraints(self, path):
        result = []
        generated_path, completed, node_list = to_single_assignment_predicates(path)
        if not completed:
            return [],[]
        for p in generated_path:
            # if (isinstance(p, ast.AnnAssign) and p.target.id in {'exit', 'return'}):
            if p:
                result.append(to_src(p))
        # if not node_list:

        return result, node_list
        # return [to_src(p) for p in to_single_assignment_predicates(path) if p]

    def solve_constraint(self, constraints, pNodeList):
        # re-initializing does not seem problematic.
        # a = z3.Int('a').get_id() remains the same.
        identifiers = [c for i in constraints for c in used_identifiers(i)]  # <- changes
        with_types = identifiers_with_types(identifiers, self.used_variables)  # <- changes
        decl = define_symbolic_vars(with_types, '')
        exec(decl)

        solutions = {}
        with checkpoint(self.z3):
            print('origin constraints: ', constraints)
            i = 0
            unsa_path = {}

            for con in constraints:
                print("con: ",con)
                st2 = 'self.z3.assert_and_track(%s,"p%s")' % (con,str(i))
                i=i+1
                path_name = 'p'+ str(i)
                unsa_path[z3.Bool(path_name)] = con
                eval(st2)
            if self.z3.check() != z3.sat:
                unsat_info_dict = {}
                unsat_info_dict['*core*'] = []
                unsat_info_dict['*statement*'] = []

                unsat_info_dict['*core*'].append("\n================== ERROR: UNSAT PATH FOUND ===================")
                print("\n================== ERROR: UNSAT PATH FOUND ===================\n")
                unsat_info_dict['*core*'].append("Unsat core length:" + str(len(self.z3.unsat_core())))
                print("Unsat core length:", len(self.z3.unsat_core()))
                unsa_core = self.z3.unsat_core()
                unsat_info_dict['*core*'].append("Unsat core: ")
                print("Unsat core: ")
                for i in range(len(unsa_core)):
                    if unsa_core[i] not in unsa_path:
                        continue
                    unsat_info_dict['*core*'].append("\t" + str(i+1) + ":" + str(unsa_path[unsa_core[i]]))
                    print("\t",i+1,":", unsa_path[unsa_core[i]])
                    # unsa_result.append(unsa_path[unsa_core[i]])

                unsat_info_dict['*statement*'].append("Statements in Unsat Path: ")
                print("Statements in Unsat Path: ")
                for node in pNodeList:
                    cfgnode_json = node.cfgnode.to_json()
                    at = cfgnode_json['at']
                    ast = cfgnode_json['ast']
                    unsat_info_dict['*statement*'].append("\tLine" + str(at) + ":" + str(ast))
                    print("\tLine", at, ":", ast)
                # return unsa_result
                return unsat_info_dict, True
            m = self.z3.model()
            solutions = {d.name(): m[d] for d in m.decls()}
            my_args = {k: solutions.get(k, None) for k in self.fn_args}
        predicate = 'z3.And(%s)' % ','.join(["%s == %s" % (k, v) for k, v in my_args.items() if v is not None])
        eval('self.z3.add(z3.Not(%s))' % predicate)
        return my_args, False

    def solve_path_constraint(self, path):
        # re-initializing does not seem problematic.
        # a = z3.Int('a').get_id() remains the same.
        constraints = self.extract_constraints(path)
        identifiers = [c for i in constraints for c in used_identifiers(i)]  # <- changes
        with_types = identifiers_with_types(identifiers, self.used_variables)  # <- changes
        decl = define_symbolic_vars(with_types, '')
        exec(decl)

        solutions = {}
        with checkpoint(self.z3):
            print('constraints: ', constraints)
            st = 'self.z3.add(%s)' % ', '.join(constraints)
            print('---------- st: ', st)
            eval(st)
            if self.z3.check() != z3.sat:
                print("====== ERROR: UNSAT PATH ======\n\t", {k: solutions.get(k, None) for k in self.fn_args})

                return {}
            m = self.z3.model()
            solutions = {d.name(): m[d] for d in m.decls()}
            my_args = {k: solutions.get(k, None) for k in self.fn_args}
        predicate = 'z3.And(%s)' % ','.join(["%s == %s" % (k, v) for k, v in my_args.items() if v is not None])
        eval('self.z3.add(z3.Not(%s))' % predicate)
        return my_args

    def get_all_paths(self, fenter):
        path_lst = [PNode(0, fenter)]
        completed = []
        for i in range(self.max_iter):
            new_paths = [PNode(0, fenter)]
            for path in path_lst:
                # explore each path once
                if path.cfgnode.children:
                    np = path.explore()
                    for p in np:
                        if path.idx > self.max_depth:
                            break
                        # if self.can_be_satisfied(p):
                        #     new_paths.append(p)
                        # else:
                        #     break
                        new_paths.append(p)
                else:
                    completed.append(path)
            path_lst = new_paths
        return completed + path_lst


    def can_be_satisfied(self, p):
        s2 = self.extract_constraints(p.get_path_to_root())
        # if any(fn_name in s2 for fn_name in self.function_names):
        #     print("asdasdasdsadas")
        # print(s2)
        s = z3.Solver()
        identifiers = [c for i in s2 for c in used_identifiers(i)]
        with_types = identifiers_with_types(identifiers, self.used_variables)
        decl = define_symbolic_vars(with_types, '')
        exec(decl)
        exec("s.add(z3.And(%s))" % ','.join(s2), globals(), locals())
        # sys.exit(0)
        return s.check() == z3.sat

    def get_next_path(self):
        self.last_path -= 1
        if self.last_path == -1:
            self.last_path = len(self.paths) - 1
        return self.paths[self.last_path].get_path_to_root()
