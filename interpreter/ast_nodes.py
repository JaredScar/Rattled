#
# Rattled Programming Language — AST Node Definitions
#
# Each node class represents one syntactic construct.
# Statement nodes are transpiled by Transpiler._stmt().
# Expression nodes are transpiled by Transpiler._expr().
#

# ═══════════════════════════════════════════════════════════════════
# Statement nodes
# ═══════════════════════════════════════════════════════════════════

class ProgramNode:
    """Root node — a list of top-level statements."""
    def __init__(self, stmts):
        self.stmts = stmts


class AssignNode:
    """lhs = rhs  (lhs is IdentNode, AttrNode, or IndexNode)"""
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs


class GlobalDeclNode:
    """glo name  (inside a function → 'global name'; at module level → no-op)"""
    def __init__(self, name):
        self.name = name


class GlobalAssignNode:
    """glo name = expr"""
    def __init__(self, name, rhs):
        self.name = name
        self.rhs  = rhs


class PrintNode:
    """pr expr  →  print(expr)"""
    def __init__(self, expr):
        self.expr = expr


class ReadFileNode:
    """rd path_expr  →  open(path_expr).read()"""
    def __init__(self, path_expr):
        self.path_expr = path_expr


class WriteFileNode:
    """wr path_expr content_expr  →  open(path_expr, 'w').write(content_expr)"""
    def __init__(self, path_expr, content_expr):
        self.path_expr    = path_expr
        self.content_expr = content_expr


class FlushNode:
    """fl  →  sys.stdout.flush()"""
    pass


class ImportNode:
    """
    imp module          →  import module
    imp name from mod   →  from mod import name
    """
    def __init__(self, module, names=None):
        self.module = module
        self.names  = names or []


class ReturnNode:
    """ret [expr]  →  return [expr]"""
    def __init__(self, expr=None):
        self.expr = expr


class IfNode:
    """if cond { body } [elif cond { body }]* [el { body }]"""
    def __init__(self, cond, body, elif_clauses, else_body):
        self.cond         = cond
        self.body         = body            # [stmt, ...]
        self.elif_clauses = elif_clauses    # [(cond, [stmt,...]), ...]
        self.else_body    = else_body       # [stmt, ...] or None


class ForNode:
    """
    for cond_expr { body }
    The first identifier in cond_expr is the loop variable; if it has not
    been previously assigned it is auto-initialised to 0 and auto-incremented
    by 1 at the bottom of every iteration.
    """
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body


class ForRangeNode:
    """
    for var in start..end { body }
    Maps to Python: for var in range(start, end):
    """
    def __init__(self, var, start, end, body):
        self.var   = var    # str
        self.start = start
        self.end   = end
        self.body  = body


class WhileNode:
    """while cond { body }  (no auto-management of loop variable)"""
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body


class FnDefNode:
    """fn name(params) { body }  →  def name(params):"""
    def __init__(self, name, params, body):
        self.name   = name
        self.params = params    # [(name_str, default_expr_or_None), ...]
        self.body   = body


class ConstructorNode:
    """def(params) { body }  inside a Clas block  →  def __init__(self, params):"""
    def __init__(self, params, body):
        self.params = params
        self.body   = body


class MethodNode:
    """fn name(params) { body }  inside a Clas block  →  def name(self, params):
       stat fn name(params) { body }                  →  @staticmethod / def name(params):
    """
    def __init__(self, name, params, body, is_static=False):
        self.name      = name
        self.params    = params
        self.body      = body
        self.is_static = is_static


class ClassNode:
    """Clas Name[(Parent)] { [constructor] [methods] }"""
    def __init__(self, name, parent, constructor, methods):
        self.name        = name
        self.parent      = parent       # str or None
        self.constructor = constructor  # ConstructorNode or None
        self.methods     = methods      # [MethodNode, ...]


class SwitchNode:
    """sw expr { cs val { body } ... [def { body }] }"""
    def __init__(self, expr, cases, default_body):
        self.expr         = expr
        self.cases        = cases           # [(val_expr, [stmt,...]), ...]
        self.default_body = default_body    # [stmt,...] or None


class TryCatchNode:
    """
    try { body } catch { body }          →  try: ... except Exception: ...
    try { body } catch SomeError { body }  →  try: ... except SomeError: ...
    """
    def __init__(self, try_body, catch_body, exc_type=None):
        self.try_body   = try_body
        self.catch_body = catch_body
        self.exc_type   = exc_type   # str or None


class BreakNode:
    """brk  →  break"""
    pass


class ContinueNode:
    """cont  →  continue"""
    pass


class ExprStmtNode:
    """A statement consisting of a single expression (call, x++, x--, etc.)"""
    def __init__(self, expr):
        self.expr = expr


# ═══════════════════════════════════════════════════════════════════
# Expression nodes
# ═══════════════════════════════════════════════════════════════════

class IntNode:
    def __init__(self, value):
        self.value = value      # Python int


class FloatNode:
    def __init__(self, value):
        self.value = value      # Python float


class StringNode:
    def __init__(self, value):
        self.value = value      # Python str (already unescaped by lexer)


class BoolNode:
    def __init__(self, value):
        self.value = value      # True or False


class NullNode:
    """null  →  None"""
    pass


class IdentNode:
    def __init__(self, name):
        self.name = name


class BinOpNode:
    def __init__(self, left, op, right):
        self.left  = left
        self.op    = op     # str e.g. '+', '<', '&&', …
        self.right = right


class UnaryOpNode:
    def __init__(self, op, operand):
        self.op      = op       # 'not' or '-'
        self.operand = operand


class IncrementNode:
    """x++  →  x += 1  (used both as expression and statement)"""
    def __init__(self, operand):
        self.operand = operand


class DecrementNode:
    """x--  →  x -= 1"""
    def __init__(self, operand):
        self.operand = operand


class CallNode:
    """callee(args)  (callee is any expression)"""
    def __init__(self, callee, args):
        self.callee = callee
        self.args   = args      # [expr, ...]


class MethodCallNode:
    """obj.method(args)"""
    def __init__(self, obj, method, args):
        self.obj    = obj
        self.method = method    # str
        self.args   = args


class AttrNode:
    """obj.attr  (read access)"""
    def __init__(self, obj, attr):
        self.obj  = obj
        self.attr = attr        # str


class IndexNode:
    """obj[index]"""
    def __init__(self, obj, index):
        self.obj   = obj
        self.index = index


class ArrayNode:
    """[elem, ...]"""
    def __init__(self, elements):
        self.elements = elements


class HashmapNode:
    """{key: val, ...}  (bare identifier keys are auto-quoted)"""
    def __init__(self, pairs):
        self.pairs = pairs      # [(key_expr, val_expr), ...]


class InputExprNode:
    """inp prompt_expr  →  input(prompt_expr)"""
    def __init__(self, prompt):
        self.prompt = prompt


class SuperCallNode:
    """sup(args)  →  super().__init__(args)"""
    def __init__(self, args):
        self.args = args
