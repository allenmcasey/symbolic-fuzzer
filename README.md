# symbolic-fuzzer

A symbolic fuzzer tool capable of generating input values symbolically for Python functions in a given source file.


### Installation


### How To Run
  * `python3 -m venv venv_name`
  * `source venv_name/bin/activate`
  * `pip install -r requirements.txt`
  * `python src/run.py -i examples/check_triangle.py`


### Assumptions:

  * We assume that the function is not recursive and at most calls two self-contained methods
  * We assume that all variables are annotated with the type information, and only container used in the programs are lists with the maximum size 10

### Tool Description & Requirements:

  * Generate and print the path constraints in the program.
  * Each constraint should be traceable to the part of code that created the constraint.
  * If a path is unsatisfiable, the fuzzer should generate the corresponding unsat core and the statements that it belongs to.


### References:
  * https://www.fuzzingbook.org/html/SymbolicFuzzer.html