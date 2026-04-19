# Rattled Language — Design & Implementation Plan

> This document is a living specification. Edit any section freely before implementation begins.
> Rattled transpiles to Python, so runtime performance is identical to Python.

---

## Table of Contents

1. [Goals & Philosophy](#1-goals--philosophy)
2. [Architecture Overview](#2-architecture-overview)
3. [File Format](#3-file-format)
4. [Type System](#4-type-system)
5. [Syntax Reference](#5-syntax-reference)
   - 5.1 Comments
   - 5.2 Variables & Assignment
   - 5.3 Literals & Casting
   - 5.4 Operators
   - 5.5 Print & I/O
   - 5.6 Control Flow (if / elif / else)
   - 5.7 Loops (for / while)
   - 5.8 Functions
   - 5.9 Classes
   - 5.10 Collections (Arrays & Hashmaps)
   - 5.11 Imports
   - 5.12 Switch / Case
   - 5.13 Miscellaneous Keywords
6. [Standard Library (Built-ins)](#6-standard-library-built-ins)
7. [Error Handling](#7-error-handling)
8. [Implementation Roadmap](#8-implementation-roadmap)
9. [Open Questions / Decisions Needed](#9-open-questions--decisions-needed)
10. [Phase 6 — Language Completeness Backlog](#phase-6--language-completeness-)

---

## 1. Goals & Philosophy

| Goal | Description |
|------|-------------|
| **Less typing** | Common operations use the shortest possible keyword (e.g. `pr` instead of `print`). |
| **Readability** | Curly-brace blocks make structure explicit. No significant whitespace rules. |
| **Simplicity** | Auto-initializing loop counters, optional semicolons, forgiving style. |
| **Python parity** | Transpiles 1-to-1 to Python — no performance overhead beyond the transpile step itself. |
| **Familiar feel** | Anyone who knows Python, Java, or JavaScript should be comfortable immediately. |

---

## 2. Architecture Overview

```
Source (.ry file)
       │
       ▼
  ┌─────────┐
  │  Lexer  │  ── Reads source, produces a flat list of typed tokens
  └─────────┘
       │  tokens[]
       ▼
  ┌──────────┐
  │  Parser  │  ── Consumes tokens, builds an AST (Abstract Syntax Tree)
  └──────────┘
       │  AST
       ▼
  ┌────────────┐
  │ Transpiler │  ── Walks the AST, emits valid Python source code
  └────────────┘
       │  Python source (string)
       ▼
  ┌──────────────┐
  │ Python exec()|  ── Python runtime executes the generated code
  └──────────────┘
```

**Key design decision:** Rattled is a *transpiler*, not an interpreter. The generated Python string is passed to `exec()` (or optionally written to a `.py` file for inspection). This means:
- Speed == Python speed.
- You can inspect the generated Python if something goes wrong.
- Python's full standard library is available via `imp`.

---

## 3. File Format

- Extension: `.ry`
- Encoding: UTF-8
- Semicolons at line-end are **optional** (stripped by the lexer).
- Indentation inside blocks is cosmetic only — braces `{}` define scope.

---

## 4. Type System

Rattled is **dynamically typed**, matching Python's behavior exactly.

| Rattled Concept | Python Equivalent | Notes |
|-----------------|-------------------|-------|
| Integer literal | `int` | `42`, `-7` |
| Float literal | `float` | `3.14`, `-0.5` |
| String literal | `str` | `"hello"` or `'hello'` |
| Boolean literal | `bool` | `TRUE` / `FALSE` (uppercase) |
| Array | `list` | `[1, 2, 3]` |
| Hashmap | `dict` | `{key: value}` |
| Null / None | `None` | `null` keyword (TBD — see §9) |

### Casting

| Rattled | Python | Example |
|---------|--------|---------|
| `str(x)` | `str(x)` | `str(42)` → `"42"` |
| `int(x)` | `int(x)` | `int("5")` → `5` |
| `flo(x)` | `float(x)` | `flo("3.14")` → `3.14` |
| `boo(x)` | `bool(x)` | `boo("TRUE")` → `True` |

---

## 5. Syntax Reference

### 5.1 Comments

```
`This is a single-line comment`
```

Backtick-delimited. Everything between the backticks is ignored.

> **Decision needed:** Do we want multi-line backtick comments, or a second syntax (e.g. `\` … `\`)?

---

### 5.2 Variables & Assignment

```
name = "Jared"
age  = 21
pi   = 3.14159
flag = TRUE
```

- No declaration keyword needed (like Python).
- Variables are global by default within their scope.
- Use `glo` to declare a variable that is accessible everywhere (maps to Python's `global`):

```
glo counter = 0
```

- Multi-line assignment using parentheses:

```
message = ("Hello, "
    + "world!")
```

---

### 5.3 Literals & Casting

```
x = 10
y = 3.14
s = "hello"
b = TRUE          ` Boolean — TRUE or FALSE `
n = null          ` None (TBD) `

casted = str(x)   ` "10" `
back   = int("5") ` 5    `
```

---

### 5.4 Operators

#### Arithmetic

| Symbol | Operation |
|--------|-----------|
| `+` | Addition / string concat |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |
| `%` | Modulo |
| `**` | Exponentiation |

#### Comparison

| Symbol | Operation |
|--------|-----------|
| `==` | Equal |
| `!=` | Not equal |
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater than or equal |
| `<=` | Less than or equal |

#### Logical

| Rattled | Meaning |
|---------|---------|
| `&&` | Logical AND |
| `\|\|` | Logical OR |
| `!` | Logical NOT |

#### Increment / Decrement

| Rattled | Python equiv |
|---------|--------------|
| `x++` | `x += 1` |
| `x--` | `x -= 1` |

---

### 5.5 Print & I/O

```
pr "Hello, World!"
pr "Name: " + name + " Age: " + str(age)
```

- `pr` maps to Python's `print()`.
- String concatenation with `+` works as in Python; non-strings must be cast.

```
name = inp "Enter your name: "
```

- `inp` maps to Python's `input()`. The result is always a string.

```
wr "output.txt" "Some content"    ` Write to file `
rd "input.txt"                    ` Read from file — returns string `
```

> **Decision needed:** Should `pr` automatically cast non-strings (i.e. allow `pr age` without `str(age)`)?  
> Python's `print()` handles this natively; we could mirror that.

---

### 5.6 Control Flow

#### if / elif / else

```
if condition {
    ` body `
} elif otherCondition {
    ` body `
} el {
    ` body `
}
```

- `el` = `else`
- `elif` = `elif`
- Condition does not need parentheses (but they are allowed).
- Body must be in curly braces `{}`.

Examples:

```
age = 18

if age >= 18 {
    pr "Adult"
} elif age >= 13 {
    pr "Teenager"
} el {
    pr "Child"
}

flag = FALSE
if !flag {
    pr "Flag is not set"
}
```

---

### 5.7 Loops

#### for loop

If the loop variable has **not** been declared before the loop, it is automatically initialised to `0` and incremented by `1` each iteration.

```
for i < 10 {
    pr "Iteration: " + str(i)
}
```

If the variable **has** been declared, its current value is used as the starting point:

```
index = 5
for index < 20 {
    pr index
}
```

Transpiles to a Python `while` loop:

```python
i = 0
while i < 10:
    print("Iteration: " + str(i))
    i += 1
```

> **Decision needed:** Should `for` support a range-style syntax like `for i in 0..10`? This would be more explicit and map cleanly to Python's `range()`.

#### while loop

```
while condition {
    ` body `
}
```

The variable is **not** auto-initialised or auto-incremented — the programmer manages it manually.

```
i = 0
while i < 5 {
    pr "While: " + str(i)
    i++
}
```

---

### 5.8 Functions

```
fn greet(name) {
    pr "Hello, " + name
}

fn add(a, b) {
    ret a + b
}

result = add(3, 4)
pr str(result)
```

- `fn` declares a function (maps to Python `def`).
- `ret` returns a value (maps to Python `return`).
- Parameters are comma-separated, no type annotations required.
- Functions can be called before they are defined (transpiler resolves ordering — TBD).

#### Default Parameters

```
fn greet(name, greeting = "Hello") {
    pr greeting + ", " + name
}
```

---

### 5.9 Classes

```
Clas Animal {
    def(name, sound) {
        self.name = name
        self.sound = sound
    }

    fn speak() {
        pr self.name + " says " + self.sound
    }
}

dog = Animal("Rex", "Woof")
dog.speak()
```

- `Clas` declares a class (maps to Python `class`).
- `def` is the constructor (maps to Python `__init__`).
- `self` works exactly as in Python.
- Inheritance syntax (proposed):

```
Clas Dog(Animal) {
    def(name) {
        sup("Dog", "Woof")   ` sup = super().__init__() `
    }
}
```

> **Decision needed:** Should `sup` be the keyword for `super()`?

---

### 5.10 Collections

#### Arrays (Lists)

```
arr nums = [1, 2, 3, 4, 5]
arr names = ["Alice", "Bob"]

nums.push(6)       ` append `
nums.pop()         ` remove last `
pr nums[0]         ` indexing `
pr nums.len()      ` length `
```

> **Decision needed:** Map `.push()` / `.pop()` / `.len()` to Python's `.append()` / `.pop()` / `len()` — or just allow Python-style method calls directly?

#### Hashmaps (Dicts)

```
hashm person = {name: "Jared", age: 21}

pr person["name"]
person["email"] = "jared@example.com"
```

---

### 5.11 Imports

```
imp math
imp os

pr str(math.sqrt(16))
```

Maps directly to Python's `import`. You can also import specific items:

```
imp sqrt from math    ` from math import sqrt `
```

---

### 5.12 Switch / Case

```
sw score {
    cs 100 {
        pr "Perfect!"
    }
    cs 90 {
        pr "Great!"
    }
    def {
        pr "Keep trying"    ` default case `
    }
}
```

Transpiles to Python `match` / `case` (Python 3.10+) or an `if/elif/else` chain for older Python.

> **Decision needed:** Minimum Python version to target? Recommend 3.10+ for `match` support.

---

### 5.13 Miscellaneous Keywords

| Rattled | Python | Notes |
|---------|--------|-------|
| `fn` | `def` | Function declaration |
| `glo` | `global` | Global variable |
| `ret` | `return` | Return value |
| `Clas` | `class` | Class declaration |
| `def` (inside Clas) | `__init__` | Constructor |
| `sup` | `super()` | Parent constructor |
| `arr` | list literal | Array declaration |
| `hashm` | dict literal | Hashmap declaration |
| `imp` | `import` | Import module |
| `sw` | `match` | Switch statement |
| `cs` | `case` | Case in switch |
| `pr` | `print()` | Print to stdout |
| `inp` | `input()` | Read from stdin |
| `rd` | `open().read()` | Read file |
| `wr` | `open().write()` | Write file |
| `fl` | `sys.stdout.flush()` | Flush output |
| `TRUE` | `True` | Boolean true |
| `FALSE` | `False` | Boolean false |
| `null` | `None` | Null value (TBD) |

---

## 6. Standard Library (Built-ins)

These map to Python's standard library and are available without an explicit import:

| Rattled | Python | Description |
|---------|--------|-------------|
| `pr` | `print()` | Print to stdout |
| `inp` | `input()` | Read line from stdin |
| `str(x)` | `str(x)` | Cast to string |
| `int(x)` | `int(x)` | Cast to integer |
| `flo(x)` | `float(x)` | Cast to float |
| `boo(x)` | `bool(x)` | Cast to boolean |
| `binSer(arr, val)` | Binary search | Built-in algorithm |
| `mergSor(arr)` | Merge sort | Built-in algorithm |
| `quikSor(arr)` | Quick sort | Built-in algorithm |
| `heapSor(arr)` | Heap sort | Built-in algorithm |
| `bubSor(arr)` | Bubble sort | Built-in algorithm |

> The sorting/searching algorithms will be implemented in a Rattled standard library file that gets prepended to the transpiled output when used.

---

## 7. Error Handling

### Syntax Errors

The lexer and parser should produce friendly, line-numbered error messages:

```
[Rattled] SyntaxError on line 7: Unexpected token '}'
```

### Runtime Errors

Since Rattled transpiles to Python, Python's own runtime errors will surface. The transpiler should map line numbers back to the original `.ry` file where possible.

### Try / Catch (Proposed)

```
try {
    result = int("not a number")
} catch {
    pr "Conversion failed"
}
```

Maps to Python's `try / except`.

> **Decision needed:** Should `catch` accept an exception type, e.g. `catch ValueError`?

---

## 8. Implementation Roadmap

### Phase 1 — Lexer (Foundation) ✅ Complete
- [x] Tokenize all keywords, identifiers, operators, literals, and delimiters
- [x] Handle single-quoted and double-quoted strings
- [x] Handle backtick comments
- [x] Handle `#` line comments (legacy support)
- [x] Track line numbers for error reporting
- [x] Ignore optional semicolons
- [x] Support multi-line expressions in parentheses

### Phase 2 — Parser (AST) ✅ Complete
- [x] Define AST node types (AssignNode, PrintNode, IfNode, ForNode, WhileNode, FnNode, ClassNode, …)
- [x] Parse variable assignment
- [x] Parse `pr` / `inp` statements
- [x] Parse `if` / `elif` / `el` blocks
- [x] Parse `for` (condition form + range form `for i in 0..n`) and `while` loops
- [x] Parse `fn` function definitions and calls
- [x] Parse `Clas` class definitions (constructor `def`, instance `fn`, static `stat fn`)
- [x] Parse `arr` and `hashm` literals
- [x] Parse `sw` / `cs` switch blocks
- [x] Parse `imp` imports (`imp mod` and `imp name from mod`)
- [x] Parse expressions (arithmetic, comparison, logical, casting, `++`/`--`, `&&`/`||`/`!`)
- [x] Parse `try` / `catch` (bare and typed: `catch ValueError`)
- [x] Parse `brk` (break) and `cont` (continue)

### Phase 3 — Transpiler ✅ Complete
- [x] Walk AST and emit Python source
- [x] Handle auto-init and auto-increment of `for` loop variables
- [x] Map all keywords to their Python equivalents
- [x] Emit `__init__` for `def` inside `Clas`
- [x] Prepend standard library stubs when built-in algorithms are used
- [x] Line-number comment annotations (`# ry:N`) in generated Python for debugging
- [x] `pr` auto-cast: non-strings in `+` chains are wrapped in `str()` automatically
- [x] String interpolation: `"Hello {name}"` emits Python f-strings
- [x] Static methods: `stat fn` emits `@staticmethod`
- [x] Typed catch: `catch ValueError` emits `except ValueError:`

### Phase 4 — Runner ✅ Complete
- [x] Accept a `.ry` file path as a CLI argument (`python rattled.py file.ry`)
- [x] Lex → Parse → Transpile pipeline
- [x] Execute generated Python via `exec()`
- [x] `--emit-python` flag to dump the generated Python source
- [x] `--check` flag for lint-only mode (no execution)
- [x] Interactive REPL (`python rattled.py` with no arguments)
- [x] Root-level launcher `rattled.py` (no need to `cd` into `interpreter/`)

### Phase 5 — Polish ✅ Complete
- [x] Friendly error messages with `.ry` line numbers
- [x] `--check` flag (lint only, no execution)
- [x] REPL mode (`python rattled.py` with no arguments)
- [x] **VS Code syntax-highlighting extension** — TextMate grammar for `.ry` files (`vscode-rattled/`)
- [x] **PyPI packaging** — `pyproject.toml` so `pip install rattled` and `rattled file.ry` work
- [x] **Installer** — `install.bat` / `install.ps1` that pip-installs and adds to PATH automatically

---

### Phase 6 — Language Completeness ✅ Complete

Features present in most modern languages (Go, Kotlin, Swift, TypeScript, Rust) that Rattled does not yet support. Grouped by area.

#### 6A — Operators & Expressions

| Feature | Rattled syntax (proposed) | Python equivalent | Status |
|---------|--------------------------|-------------------|--------|
| Augmented assignment | `x += 3` `x -= 1` `x *= 2` `x /= 4` `x %= 2` `x **= 3` | same | ✅ done |
| Ternary expression | `val = cond ? a : b` | `a if cond else b` | ✅ done |
| Null coalescing | `val = x ?? "default"` | `x if x is not None else "default"` | ✅ done |

#### 6B — Iteration

| Feature | Rattled syntax (proposed) | Python equivalent | Status |
|---------|--------------------------|-------------------|--------|
| For-each over array | `for item in myArr { }` | `for item in myArr:` | ✅ done |
| For-each over hashmap | `for key, val in myMap { }` | `for k,v in myMap.items():` | ✅ done |
| Array / string slice | `myArr[1..4]` | `myArr[1:4]` | ✅ done |

> Note: `for i in 0..10` (numeric range) already works. The missing form is iterating *elements* of an existing collection.

#### 6C — Error Handling

| Feature | Rattled syntax (proposed) | Python equivalent | Status |
|---------|--------------------------|-------------------|--------|
| `finally` block | `fin { }` after `try/catch` | `finally:` | ✅ done |
| Multi-type catch | `catch ValueError, TypeError { }` | `except (ValueError, TypeError):` | ✅ done |
| Throw / raise | `thr ValueError("msg")` | `raise ValueError("msg")` | ✅ done |

#### 6D — Functions

| Feature | Rattled syntax (proposed) | Python equivalent | Status |
|---------|--------------------------|-------------------|--------|
| Lambda / anonymous fn | `lam x -> x * 2` / `fn(x) { ret x*2 }` | `lambda x: x * 2` | ✅ done |
| Variadic positional args | `fn foo(...args) { }` | `def foo(*args):` | ✅ done |
| Variadic keyword args | `fn foo(~~kwargs) { }` | `def foo(**kwargs):` | ✅ done |
| Generator / yield | `yld value` inside `fn` | `yield value` | ✅ done |
| Keyword call args | `foo(key = val)` | same | ✅ done |

#### 6E — Strings & Collections

| Feature | Rattled syntax (proposed) | Python equivalent | Status |
|---------|--------------------------|-------------------|--------|
| Multi-line string | `"""line1\nline2"""` or `'''...'''` | same | ✅ done |
| Array comprehension | `[x * 2 for x in arr]` (+ `if` filter) | same | ✅ done |
| Spread / concat arrays | `[...arr1, ...arr2]` | `[*arr1, *arr2]` | ✅ done |

#### 6F — OOP

| Feature | Rattled syntax (proposed) | Python equivalent | Status |
|---------|--------------------------|-------------------|--------|
| Class-level (static) variable | `stat x = 0` inside `Clas` | class attribute | ✅ done |
| Property getter / setter | `get fn name() { }` / `set fn name(v) { }` | `@property` | ✅ done |
| Abstract base class | `abst Clas Shape { }` / `abst fn method() {}` | `abc.ABC` | ✅ done |
| Multiple inheritance | `Clas C(A, B) { }` | same | ✅ done |

#### 6G — Imports

| Feature | Rattled syntax (proposed) | Python equivalent | Status |
|---------|--------------------------|-------------------|--------|
| Import alias | `imp numpy as np` | same | ✅ done |
| Wildcard import | `imp * from math` | `from math import *` | ✅ done |

#### 6H — Standard Library Built-ins

These can be supported without new syntax — they just need auto-import wrappers or direct pass-through.

| Function | Notes |
|----------|-------|
| `len(x)` | Already works via Python pass-through |
| `abs(x)` `min(x,y)` `max(x,y)` `round(x,n)` `pow(x,n)` | Pass-through to Python built-ins |
| `type(x)` | Rattled-friendly type inspection |
| `range(n)` `range(a,b)` | Should be usable directly inside `for` |
| `zip(a, b)` `enumerate(a)` | Useful for iteration patterns |
| `open(path, mode)` | Direct file I/O; `rd`/`wr` cover basic cases |
| String methods | `.upper()` `.lower()` `.strip()` `.split()` `.replace()` `.startsWith()` → `.startswith()` |

---

## 9. Open Questions / Decisions Needed

These items are marked as TBD above. Please review and fill in your preferences:

| # | Question | Options | Your Choice |
|---|----------|---------|-------------|
| 1 | Multi-line comments | Nested backticks \`\` … \`\` vs. dedicated syntax | |
| 2 | `pr` with non-strings | Auto-cast like Python's `print()`, or require explicit `str()` | |
| 3 | `for` range syntax | `for i < n` (current) vs. `for i in 0..n` (explicit range) | |
| 4 | `null` keyword | Use `null` → `None`, or omit and use Python's `None` directly | |
| 5 | Array methods | `.push()/.pop()/.len()` aliases vs. raw Python method names | |
| 6 | `sup` keyword | Use `sup(…)` for `super().__init__(…)` | |
| 7 | `catch` with types | `catch` only vs. `catch ExceptionType` | |
| 8 | Minimum Python version | 3.8 (no match), 3.10+ (match/case for `sw`) | |
| 9 | Forward function calls | Allow calling `fn` before definition? (requires two-pass parse) | |
| 10 | String interpolation | Plain concat `+` only, or template strings like `` `Hello {name}` `` | |
| 11 | Ternary syntax | `a if cond el b` (Rattled-native) vs. `cond ? a : b` (C-style) | |
| 12 | Lambda syntax | `lam x -> expr` vs. `fn(x) { ret expr }` (anonymous fn) | |
| 13 | Variadic args | `...args` (JS-style spread) vs. `*args` (Python-style) | |
| 14 | Augmented assignment | `+=` `-=` `*=` `/=` (standard symbols — no real alternative) | |
| 15 | For-each vs range-for | Same `for x in y` keyword for both collection iteration and range? | |

---

### Phase 7 — Polish & Completeness ✅ Complete

Remaining gaps identified after Phase 6.

| Feature | Rattled syntax | Python equivalent | Status |
|---------|---------------|-------------------|--------|
| **Destructuring assignment** | `[a, b] = expr` · `a, b = expr` · `[first, ...rest] = arr` | tuple/starred unpack | ✅ done |
| **Tuple return** | `ret a, b` | `return (a, b)` | ✅ done |
| **Dict comprehension** | `{k: v for k, v in hashm}` · `{k: v for k in arr [if cond]}` | dict comprehension | ✅ done |
| **Pattern match guards** | `cs val if guard { }` | equality + guard condition | ✅ done |
| **Type-check case** | `cs str { }` / `cs int { }` / `cs MyClass { }` | `isinstance(x, str)` | ✅ done |
| **Type hints — params** | `fn foo(x: int, y: str) { }` | `def foo(x: int, y: str):` | ✅ done |
| **Type hints — return** | `fn foo(x) -> int { }` | `def foo(x) -> int:` | ✅ done |
| **Type hints — variables** | `x: int = 5` | `x: int = 5` | ✅ done |
| **Runtime .ry line numbers** | Runtime errors show `.ry:N` not Python line | traceback mapping | ✅ done |
| **Import .ry modules** | `imp myUtils` where `myUtils.ry` exists nearby | compile + inject into `sys.modules` | ✅ done |
