# symbolic-fuzzer

A symbolic fuzzer tool capable of generating symbolic inputs for Python functions 
in a given source file, and determining whether or not each function contains execution 
paths that are unreachable based on accumulated constraints. This project extends the 
functionality of the fuzzingbook.SymbolicFuzzer tool provided by The Fuzzing Book (see 
**References** below). The extensions this tool offers include the following:

  * Support for List initialization and use inside of functions
  * Support for function calls from the function being analyzed
  * Support for unsat core collection, and the ability to trace the unsat 
  core up the path back to the source
  
Please refer to the section **Assumptions We Make** below for more information on the
limitations of these supported extensions.


### Installation
` Unix:`
  * `git clone https://github.com/allenmcasey/symbolic-fuzzer.git`
  * `python3 -m venv venv_name`
  * `source venv_name/bin/activate`
  * `cd symbolic-fuzzer`
  * `pip install -r requirements.txt`

`Windows:`
  * `git clone https://github.com/allenmcasey/symbolic-fuzzer.git`
  * `cd symbolic-fuzzer`
  * `python3 -m venv venv_name`
  * `.\venv_name\Scripts\activate.bat`
  * `pip install -r requirements.txt`

### How To Run
` Unix:`
  * `python src/run.py -i examples/check_triangle.py`
  * For help, or to see optional args: `python src/run.py -h`

`Windows:`
  * `python src\run.py -i examples\check_triangle.py`
  * For help, or to see optional args: `python src\run.py -h`

### Assumptions We Make:

  * Functions in input file are not recursive, and all functions called from other functions are self-contained
  * All variables are annotated with the type information, and the only containers used in the programs will be of type List with the maximum size 10
  * Lists cannot be passed as arguments to functions, they can only be initialized inside of a function body

### Requirements of the Tool:

  * Generate and print the path constraints in the program
  * Each constraint should be traceable to the part of code that created the constraint
  * If a path is unsatisfiable, the fuzzer should generate the corresponding unsat core and the statements that it belongs to


### References:
  * https://www.fuzzingbook.org/html/SymbolicFuzzer.html
