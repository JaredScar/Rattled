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

# Ensure the interpreter directory is on the path so all modules resolve.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer       import Lexer,       LexError
from rParser     import Parser,      ParseError
from transpiler  import Transpiler,  TranspileError


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

    filename = os.path.basename(path)

    try:
        python_src = compile_source(source, filename)
    except (LexError, ParseError, TranspileError) as exc:
        _fatal(str(exc))

    if check_only:
        print('[Rattled] {} — OK (no errors found)'.format(filename))
        return

    if emit_python:
        print(python_src)
        return

    try:
        code = compile(python_src, filename, 'exec')
        exec(code, {'__name__': '__main__'})
    except SystemExit:
        raise
    except Exception as exc:
        _fatal('Runtime error: {}'.format(exc))


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
