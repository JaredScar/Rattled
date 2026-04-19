#
# Rattled Programming Language — CLI Runner
#
# Usage:
#   python main.py <file.ry>                Run a Rattled source file
#   python main.py <file.ry> --emit-python  Print the generated Python, don't run
#   python main.py <file.ry> --check        Lint only (no execution)
#   python main.py                          Start the interactive REPL
#
import sys
import os
import re
import types
import traceback as _traceback

try:
    from .lexer      import Lexer,      LexError
    from .rParser    import Parser,     ParseError
    from .transpiler import Transpiler, TranspileError
    from .ast_nodes  import ImportNode
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from lexer       import Lexer,       LexError
    from rParser     import Parser,      ParseError
    from transpiler  import Transpiler,  TranspileError
    from ast_nodes   import ImportNode


# ═══════════════════════════════════════════════════════════════════
# Core pipeline
# ═══════════════════════════════════════════════════════════════════

def compile_source(source, filename='<input>'):
    """
    Lex → Parse → Transpile a Rattled source string.
    Returns the generated Python source string.
    Raises LexError, ParseError, or TranspileError on failure.
    """
    tokens     = Lexer(source, filename).tokenize()
    ast        = Parser(tokens, filename).parse()
    python_src = Transpiler(filename).transpile(ast)
    return python_src


def _compile_ast(source, filename='<input>'):
    """Return (ast, python_src) so callers can inspect the AST."""
    tokens     = Lexer(source, filename).tokenize()
    ast        = Parser(tokens, filename).parse()
    python_src = Transpiler(filename).transpile(ast)
    return ast, python_src


def _setup_ry_modules(ast, source_dir, seen=None):
    """
    Pre-compile any  imp ModName  statements where ModName.ry exists next to the
    source file, then inject the resulting module into sys.modules so that the
    normal  import ModName  Python statement works at runtime.
    """
    if seen is None:
        seen = set()
    for stmt in ast.stmts:
        if not isinstance(stmt, ImportNode):
            continue
        # Only handle bare  imp Name  (no 'from', no '*', with or without alias)
        if stmt.names:
            continue
        mod_name = stmt.module
        ry_path  = os.path.join(source_dir, mod_name + '.ry')
        if not os.path.isfile(ry_path) or ry_path in seen:
            continue
        seen.add(ry_path)
        try:
            with open(ry_path, 'r', encoding='utf-8') as fh:
                mod_src = fh.read()
            sub_ast, mod_python = _compile_ast(mod_src, mod_name + '.ry')
            # Recursively resolve that module's own .ry imports
            _setup_ry_modules(sub_ast, os.path.dirname(ry_path), seen)
            mod = types.ModuleType(mod_name)
            exec(compile(mod_python, ry_path, 'exec'), mod.__dict__)
            sys.modules[mod_name] = mod
        except Exception as exc:
            print('[Rattled] Warning: could not load {}.ry — {}'.format(
                mod_name, exc), file=sys.stderr)


def _ry_line_from_tb(tb_str, python_src):
    """
    Given a Python traceback string and the generated Python source, attempt to
    find the nearest  # ry:N  annotation and return the Rattled line number N.
    """
    py_lines = [int(m.group(1)) for m in re.finditer(r'line (\d+)', tb_str)]
    if not py_lines:
        return None
    src_lines = python_src.split('\n')
    for py_ln in reversed(py_lines):
        for offset in range(3):
            idx = py_ln - 1 - offset
            if 0 <= idx < len(src_lines):
                m = re.search(r'#\s*ry:(\d+)', src_lines[idx])
                if m:
                    return int(m.group(1))
    return None


def run_source(source, filename='<input>'):
    """Compile and exec a Rattled source string."""
    python_src = compile_source(source, filename)
    code       = compile(python_src, filename, 'exec')
    exec(code, {'__name__': '__main__'})


def run_file(path, emit_python=False, check_only=False):
    """Read, compile, and optionally run a .ry file."""
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            source = fh.read()
    except FileNotFoundError:
        _fatal('File not found: {}'.format(path))
    except IOError as exc:
        _fatal('Cannot read file: {}'.format(exc))

    filename   = os.path.basename(path)
    source_dir = os.path.dirname(os.path.abspath(path))

    try:
        ast, python_src = _compile_ast(source, filename)
    except (LexError, ParseError, TranspileError) as exc:
        _fatal(str(exc))

    if check_only:
        print('[Rattled] {} — OK (no errors found)'.format(filename))
        return

    if emit_python:
        print(python_src)
        return

    # Pre-load any .ry module dependencies into sys.modules
    _setup_ry_modules(ast, source_dir)

    try:
        code = compile(python_src, filename, 'exec')
        exec(code, {'__name__': '__main__'})
    except SystemExit:
        raise
    except Exception as exc:
        tb_str  = _traceback.format_exc()
        ry_line = _ry_line_from_tb(tb_str, python_src)
        if ry_line:
            _fatal('[Rattled] {}: line {}: {}: {}'.format(
                filename, ry_line, type(exc).__name__, exc))
        else:
            _fatal('[Rattled] Runtime error: {}: {}'.format(
                type(exc).__name__, exc))


# ═══════════════════════════════════════════════════════════════════
# Interactive REPL
# ═══════════════════════════════════════════════════════════════════

def repl():
    print('Rattled REPL  (type "exit" or press Ctrl-C to quit)')
    print('─' * 46)
    env     = {'__name__': '<repl>'}
    buffer  = []

    while True:
        prompt = 'ry> ' if not buffer else '... '
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if line.strip() == 'exit':
            break

        buffer.append(line)
        source = '\n'.join(buffer)

        try:
            python_src = compile_source(source, '<repl>')
        except (LexError, ParseError, TranspileError):
            # Incomplete input or genuine error — keep buffering.
            # If the user enters a blank line, force-flush and report error.
            if line.strip() == '':
                try:
                    python_src = compile_source(source, '<repl>')
                except (LexError, ParseError, TranspileError) as exc:
                    print(str(exc))
                buffer = []
            continue

        try:
            code = compile(python_src, '<repl>', 'exec')
            exec(code, env)
        except SystemExit:
            break
        except Exception as exc:
            print('[Rattled] Runtime error: {}'.format(exc))

        buffer = []


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _fatal(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    if not args:
        repl()
        return

    path        = args[0]
    emit_flag   = '--emit-python' in args
    check_flag  = '--check' in args

    if not path.endswith('.ry'):
        print('[Rattled] Warning: expected a .ry source file', file=sys.stderr)

    run_file(path, emit_python=emit_flag, check_only=check_flag)


if __name__ == '__main__':
    main()
