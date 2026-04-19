# Rattled Python
Rattled Python is a programming language I have set out to create
in attempts to decrease the amount of typing a programmer actually
has to do. The whole idea behind it was to decrease the amount of
letters to be typed for simple functions as well as programming
identifiers. Instead of typing out 'print("")' in python, in Rattled
Python you can type 'pr ""' which would do the same thing as a print()
function in python. Rattled Python was also designed for readability,
which is why brackets ({}) have been required for containing the bodies of
if statements, for, and while loops. I will admit that Java was my
first language and I always did love brackets. Loops were designed with
simplicity in mind at best. Rather than having to increment variables
within the loop declaration, if the variable within the loop has not
been previously defined, then it will be automatically set to 0 and
increment as the loop passes through its body. This of course will not
work so well if you have a loop like 'while i > 5' in which the variable
i should be previously defined.
# Code Preview
```
age = 21
name = 'Jared'
bool = boo('TRUE')
`This is a comment in Rattled`
for i < 5 {
    pr 'Example of a for loop in Rattled ' + i
}

while i < 5 {
    pr 'Example of a while loop in Rattled ' + i
}

if bool {
    pr "My name is " + name + " and I am " + age + " years old";
}
```
# TODO List
- [x] Lexer splits up source code into tokens and sets up their types

- [x] Code actually runs the functions

- [x] Spaces get ignored by lexer

- [x] Multi-line variable declaration by keeping variable values in parenthesis

- [x] Keywords (if, for, while) ignore spacing and equal amount of
parenthesis when parsing their bodies and conditionals

# What's been built
- **Lexer** — tokenises `.ry` source into a typed token stream; strips comments (backtick and `#`), skips all whitespace, and handles optional semicolons
- **Parser** — recursive-descent + Pratt operator-precedence parser that produces a full AST
- **Transpiler** — walks the AST and emits valid Python 3 source
- **Runner / CLI** — `python interpreter/main.py file.ry` runs a Rattled program; `--emit-python` prints the generated Python instead
- **REPL** — interactive prompt launched by running `python interpreter/main.py` with no arguments
- **Standard library** — built-in sorting (`mergSor`, `quikSor`, `heapSor`, `bubSor`) and searching (`binSer`) algorithms
- **All core language features** — variables, types, casting (`str`/`int`/`flo`/`boo`), arithmetic, comparisons, logical operators (`&&` `||` `!`), `++`/`--`, `if`/`elif`/`el`, `for` (auto-init + auto-increment), `while`, functions (`fn`/`ret`), classes (`Clas`/`def`/`fn`/`sup`), arrays (`arr`), hashmaps (`hashm`), imports (`imp`), switch/case (`sw`/`cs`), `try`/`catch`

# Installation
```
git clone https://github.com/your-username/Rattled.git
cd Rattled
python interpreter/main.py examples/fullDemo.ry
```
Requires Python 3.6 or newer. No external dependencies.

# Documentation
A full documentation website lives in the `docs/` folder and is published via **GitHub Pages**.

To enable it:
1. Push this repository to GitHub.
2. Go to **Settings → Pages**.
3. Set **Source** to `Deploy from a branch`, branch `main`, folder `/docs`.
4. Your docs will be live at `https://your-username.github.io/Rattled/`.

- `docs/index.html` — Landing page with features, install, and code samples
- `docs/reference.html` — Full language reference (all syntax, OOP, stdlib, CLI)

For the raw language spec see `PLAN.md`.
