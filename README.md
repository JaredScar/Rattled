# Rattled

Rattled is a programming language that **transpiles to Python**, so your programs run at native Python speed with access to the full standard library and ecosystem. The syntax is meant to reduce typing for common operations (for example `pr "hello"` instead of `print("hello")`) while keeping block bodies in **curly braces** `{ }` for readability.

See **`PLAN.md`** for the full language design and feature checklist.

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
| `PLAN.md` | Language specification and phased roadmap |

## Documentation

- **`docs/`** — Open `docs/index.html` locally or publish with GitHub Pages (**Settings → Pages →** branch `main`, folder **`/docs`**). Includes a full **reference** page covering syntax, stdlib, and CLI.
- **`PLAN.md`** — Authoritative design doc and phase status.

## What’s implemented

- **Lexer / parser / transpiler** — Token stream, AST, Python emission with `# ry:N` line markers for errors.
- **Language** — Variables, casting (`str` / `int` / `flo` / `boo`), operators, `if` / `elif` / `el`, `for` (range, collection, C-style), `while`, `sw` / `cs`, `try` / `catch` / `fin`, functions (variadic `...args`, `~~kwargs`), generators (`yld`), classes as above, list/hashmap literals, string interpolation `{name}`, `.ry` imports, runtime errors mapped back to `.ry` lines where possible.
- **Packaging** — `pyproject.toml` with `rattled` console script.
- **Extras** — Windows installers, VS Code extension, static documentation site.

Early TODO items (lexer, runner, spacing, parsing) are **done**; see `PLAN.md` for the detailed roadmap through Phase 7.
