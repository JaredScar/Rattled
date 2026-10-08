# Rattled

Rattled is a programming language that **transpiles to Python**, so your programs run at native Python speed with access to the full standard library and ecosystem. The syntax is meant to reduce typing for common operations (for example `pr "hello"` instead of `print("hello")`) while keeping block bodies in **curly braces** `{ }` for readability.

The language in **`PLAN.md`** is fully implemented (Phases 1–7). That file is the specification, not a list of remaining work.

## Quick example

```
fn greet(name: str, times: int = 1) {
    for i in 0..times {
        pr "Hello, {name}!"
    }
}

hashm scores = {alice: 95, bob: 82}
for person, score in scores {
    pr "{person}: {score}"
}

greet("Rattled", 2)
```

(`.ry` files use the same syntax.)

## Features (high level)

- **Python runtime** — no interpreter VM; output is Python 3 source executed with `exec()`.
- **Modern syntax** — ternary `? :`, null coalescing `??`, lambdas `lam x -> expr`, comprehensions, destructuring, type hints (optional), switch/case with guards and type checks.
- **OOP** — classes, inheritance, abstract classes, static methods, properties (`get fn` / `set fn`), `sup()` for super calls.
- **Modules** — `imp` for Python packages and for other `.ry` files in the same directory (auto-compiled).
- **Tooling** — CLI `rattled`, REPL, `--emit-python` / `--check`, VS Code syntax extension under `vscode-rattled/`, GitHub Pages docs in `docs/`.

## Installation

**From PyPI** (recommended):

```bash
pip install rattled
rattled --help
rattled examples/fullDemo.ry
```

**From source** (editable install):

```bash
git clone https://github.com/JaredScar/Rattled.git
cd Rattled
pip install -e .
```

On Windows you can also run `install.bat` or `install.ps1` to install and help put the `rattled` script on your PATH.

Requires **Python 3.8+**. Runtime has no extra dependencies beyond the standard library.

## CLI

| Command | Description |
|--------|-------------|
| `rattled file.ry` | Run a Rattled program |
| `rattled file.ry --emit-python` | Print generated Python only |
| `rattled file.ry --check` | Parse/check without running |
| `rattled` | Start the REPL |

You can still run via `python interpreter/main.py …` if you prefer.

## Project layout

| Path | Role |
|------|------|
| `interpreter/` | Lexer, parser, transpiler, CLI (`main.py`) |
| `rattled.py` | Top-level launcher |
| `examples/` | Demo `.ry` files (`fullDemo.ry`, `phase6Demo.ry`, `phase7Demo.ry`, …) |
| `docs/` | Static site for **GitHub Pages** (landing + full reference) |
| `vscode-rattled/` | VS Code grammar for `.ry` |
| `PLAN.md` | Completed language specification (Phases 1–7) |

## Documentation

- **`docs/`** — Open `docs/index.html` locally, or publish with GitHub Pages (**Settings → Pages →** branch `main`, folder **`/docs`**). `docs/reference.html` is the full syntax reference.
- **`PLAN.md`** — The finished specification. Every phase is checked off, and the design decisions in section 9 are the ones the compiler implements.

## Language status

Rattled is complete relative to `PLAN.md`.

- **Compiler** — Lexer, parser, and transpiler. Generated Python carries `# ry:N` markers, and runtime errors report the `.ry` line when they can.
- **Language** — Variables, casting, operators, `if` / `elif` / `el`, `for` (condition, range, and collection), `while`, `sw` / `cs` (guards and type checks), `try` / `catch` / `fin`, functions (defaults, `...args`, `~~kwargs`, calls before the definition), lambdas, generators, classes, list and dict comprehensions, destructuring, string interpolation, optional type hints, and `.ry` modules.
- **Aliases** — `pr`, `push` → `append`, `len()`, `startsWith` / `endsWith`.
- **Distribution** — `pyproject.toml` (`rattled` command), Windows installers, VS Code grammar, and the docs site.
