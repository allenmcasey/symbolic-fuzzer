# symbolic-fuzzer

A symbolic fuzzing tool capable of generating symbolic inputs for Python functions 
in a given source file, and determining whether or not each function contains execution 
paths that are unreachable based on accumulated constraints. This project extends the 
functionality of the fuzzingbook.SymbolicFuzzer tool provided by The Fuzzing Book (see 
**References** below). The extensions this tool offers include the following:

  * Support for List initialization and use inside of functions
  * Support for function calls from the function being analyzed
  * Support for unsat core collection, and the ability to trace the unsat 
  core up the path back to the source
  
Please refer to the section **Assumptions We Make** below for more information on the
limitations of these supported extensions. <br><br>


### Installation
  This symbolic fuzzer works on Python 3.8+ (other versions should work as well, but not tested yet)
  
` Unix:`
  * `git clone https://github.com/allenmcasey/symbolic-fuzzer.git`
  * `python3 -m venv venv_name`
  * `source venv_name/bin/activate`
  * `cd symbolic-fuzzer`
  * `pip install -r requirements.txt`

`Windows:`
  * `git clone https://github.com/allenmcasey/symbolic-fuzzer.git`
  * `python3 -m venv venv_name`
  * `.\venv_name\Scripts\activate.bat`
  * `cd symbolic-fuzzer`
  * `pip install -r requirements.txt`<br><br>

### How To Run
`Unix:`
  * `python src/run.py -i examples/check_triangle.py`
  * For help, or to see optional args: `python src/run.py -h`

`Windows:`
  * `python src\run.py -i examples\check_triangle.py`
  * For help, or to see optional args: `python src\run.py -h`

<br>The argument passed with `-i INPUT` above can be replaced with other test files in the 
`examples` directory, or any valid path to a Python file of your choice. The optional 
arguments are as follows:

  * `-h, --help`: get information on argument usage for this tool
  * `-o OUTPUT, --output OUTPUT`: the output path for the analysis report
  * `-d DEPTH, --depth DEPTH`: maximum depth to explore in each path
  * `-t TRIES, --tries TRIES`: maximum tries to produce a value
  * `-r ITER, --iter ITER`: maximum iterations to generate paths
  * `-f FUNC, --func FUNC`: specify the name of the function in the file that you'd like to analyze
  * `-c CONSTANT, --constant CONSTANT`: re-check function if constant is detected. Devault setting is True<br><br>
  
### Using the Tool

In order to use the tool to verify your program, you must first run the analysis described above by passing in a Python file
as an argument. The tool will find all execution paths of the functions in the program, and gather boolean constraints for
each path. It will then determine if any of the paths accumulated a set of constraints that is not logically satisfiable. As 
each path is discovered and analyzed, you will see information about it printed in standard output. If an unsatisfiable
path is detected, you will see the following banner alert appear in the standard output:

`================== ERROR: UNSAT PATH FOUND ===================`

Following this alert, the program will display information about the unsatisfiable path that has been found, which can help 
you address the unreachability issue. First, the tool prints information regarding the 'unsat core' of the path - in other 
words, the subset of constraints that directly cause the path to be unsatisfiable. You will see the number of constraints 
in the unsat core, as well as the constraints themselves. It'll look something like this:

`Unsat core length: 3`<br>
`Unsat core:`<br> 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`1 : z3.And(a == _a_0, b == _b_0, c == _c_0)`<br> 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`2 : (_a_0 == _b_0)`<br> 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`3 : (_a_0 == _c_0)`<br> 

Next, the statements in the path's source code are printed in the order they appear in the source file, so that you can 
trace the path using the code itself:

`Statements in Unsat Path: `<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`Line 1 : enter: check_triangle(a, b, c)`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`Line 2 : _if: a == b`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`Line 3 : _if: a == c`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`Line 4 : _if: b == c`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`Line 7 : return 'Isosceles'`<br>

If you combine all of the information printed above, you should be able to detect and resolve the statements in your program 
causing an unsatisfiable path in two simple steps:

  1. Use the unsat core to determine the conflicting boolean constraints
  2. Find these constraints in the unsat path source, then modify your code accordingly

### Assumptions We Make

  * Functions in input file are not recursive, and all functions called from other functions are self-contained
  * All variables are annotated with the type information, and the only containers used in the programs will be of type List with the maximum size 10
  * Lists cannot be passed as arguments to functions, they can only be initialized inside of a function body<br><br>

### Requirements of the Tool

  * It must generate and print the path constraints in the program
  * Each constraint should be traceable to the part of code that created the constraint
  * If a path is unsatisfiable, the fuzzer should generate the corresponding unsat core and the statements that it belongs to
  * If a function calls other functions, the paths of the called function(s) should be taken into account
  * Lists with a maximum length of 10 should result in correct constraints<br><br>

### Changes to AdvancedFuzzer class
  * Created a script called `SymbolicFuzzer.py` to override original one from Fuzzingbook
  * Changed input format for the class:
      - old: only take function name as input from same script
      - new: we take filename from command then generate arbitary code as input for the class
  * Changed `solve_path_constraint` to `solve_constraint`:
      - old: input a path contraint and try to solve
      - new: we check, analyze, and clean constraint path before call this function. Then, we take clean version of contraint as input to solve
  * Added features into `solve_constraint`:
      - old: return solve_args, but sometimes failed with assertion errors
      - new: removed assertion error and return it even if empty object. Then, we collect all uncore information for the report
  * Many other features are added outside of the class


### References
  * https://www.fuzzingbook.org/html/SymbolicFuzzer.html
