#
# Rattled Programming Language — Constants
#

# ─── Token Types ─────────────────────────────────────────────────────────────
TT_KEYWORD   = 'KEYWORD'
TT_IDENT     = 'IDENT'
TT_STRING    = 'STRING'
TT_INT       = 'INT'
TT_FLOAT     = 'FLOAT'
TT_OP        = 'OP'
TT_LPAREN    = 'LPAREN'    # (
TT_RPAREN    = 'RPAREN'    # )
TT_LBRACE    = 'LBRACE'    # {
TT_RBRACE    = 'RBRACE'    # }
TT_LBRACKET  = 'LBRACKET'  # [
TT_RBRACKET  = 'RBRACKET'  # ]
TT_COMMA     = 'COMMA'
TT_DOT       = 'DOT'
TT_COLON     = 'COLON'
TT_RANGE     = 'RANGE'     # ..
TT_EOF       = 'EOF'

# ─── Reserved Keywords ───────────────────────────────────────────────────────
KEYWORDS = frozenset({
    # control flow
    'if', 'elif', 'el',
    'for', 'while',
    'sw', 'cs',
    'try', 'catch', 'fin',
    # definitions
    'fn', 'Clas', 'def', 'ret', 'sup', 'glo', 'abst',
    # collections
    'arr', 'hashm',
    # I/O
    'pr', 'inp', 'rd', 'wr', 'fl',
    # imports
    'imp', 'from', 'as',
    # literals
    'TRUE', 'FALSE', 'null',
    # built-in algorithms
    'binSer', 'mergSor', 'quikSor', 'heapSor', 'bubSor',
    # range-for / iteration
    'in',
    # loop control
    'brk', 'cont',
    # method modifiers
    'stat',
    # lambdas / generators / errors
    'lam', 'yld', 'thr',
})

# ─── Cast-function identifier → Python builtin ──────────────────────────────
CAST_MAP = {
    'flo': 'float',
    'boo': 'bool',
    'str': 'str',
    'int': 'int',
}

# ─── List method aliases (Rattled name → Python name) ───────────────────────
METHOD_ALIAS = {
    'push': 'append',
    # 'len' is special: transpiles to len(obj) not obj.len()
}
LEN_METHOD = 'len'

# ─── Logical operator mapping ────────────────────────────────────────────────
LOGICAL_OP = {
    '&&': 'and',
    '||': 'or',
}

# ─── Binary operator precedence table (higher = tighter binding) ─────────────
# ?? is lower than || so it evaluates after logical OR chains.
# All values shifted up by 1 vs the original table to make room for ?? at 1.
OP_PREC = {
    '??': 1,
    '||': 2,
    '&&': 3,
    '==': 4, '!=': 4,
    '<':  5, '>':  5, '<=': 5, '>=': 5,
    '+':  6, '-':  6,
    '*':  7, '/':  7, '%':  7,
    '**': 8,
}

# ─── Standard library function names (built-in algorithms) ───────────────────
STD_FUNCS = frozenset({'binSer', 'mergSor', 'quikSor', 'heapSor', 'bubSor'})
