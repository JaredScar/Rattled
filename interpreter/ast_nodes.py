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


class AugAssignNode:
    """lhs op= rhs  e.g. x += 3, y -= 1, z *= 2"""
    def __init__(self, lhs, op, rhs):
        self.lhs = lhs
        self.op  = op   # '+=', '-=', '*=', '/=', '%=', '**='
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
    imp module              →  import module
    imp module as alias     →  import module as alias
    imp name from mod       →  from mod import name
    imp * from mod          →  from mod import *
    """
    def __init__(self, module, names=None, alias=None):
        self.module = module
        self.names  = names or []   # list of names, or ['*'] for wildcard
        self.alias  = alias         # str or None — for 'import X as Y'


class ReturnNode:
    """ret [expr]  →  return [expr]"""
    def __init__(self, expr=None):
        self.expr = expr


class YieldNode:
    """yld [expr]  →  yield [expr]"""
    def __init__(self, expr=None):
        self.expr = expr


class ThrowNode:
    """thr [expr]  →  raise [expr]"""
    def __init__(self, expr=None):
        self.expr = expr


class IfNode:
    """if cond { body } [elif cond { body }]* [el { body }]"""
    def __init__(self, cond, body, elif_clauses, else_body):
        self.cond         = cond
        self.body         = body
        self.elif_clauses = elif_clauses
        self.else_body    = else_body


class ForNode:
    """
    for cond_expr { body }
    Loop variable is auto-initialised to 0 and auto-incremented by 1.
    """
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body


class ForRangeNode:
    """for var in start..end { body }  →  for var in range(start, end):"""
    def __init__(self, var, start, end, body):
        self.var   = var
        self.start = start
        self.end   = end
        self.body  = body


class ForEachNode:
    """for item in iterable { body }  →  for item in iterable:"""
    def __init__(self, var, iterable, body):
        self.var      = var
        self.iterable = iterable
        self.body     = body


class ForEachPairsNode:
    """for k, v in iterable { body }  →  for k, v in iterable.items():"""
    def __init__(self, key_var, val_var, iterable, body):
        self.key_var  = key_var
        self.val_var  = val_var
        self.iterable = iterable
        self.body     = body


class WhileNode:
    """while cond { body }"""
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body


class AnnotatedAssignNode:
    """x: Type = expr  (variable type annotation with optional value)"""
    def __init__(self, target, type_ann, rhs=None):
        self.target   = target     # IdentNode
        self.type_ann = type_ann   # str
        self.rhs      = rhs        # expr or None


class FnDefNode:
    """fn name(params) { body }  →  def name(params):"""
    def __init__(self, name, params, body, return_type=None):
        self.name        = name
        self.params      = params       # [(name, default, type_ann|None), ...]
        self.body        = body
        self.return_type = return_type  # str or None


class ConstructorNode:
    """def(params) { body }  inside a Clas block  →  def __init__(self, params):"""
    def __init__(self, params, body):
        self.params = params
        self.body   = body


class MethodNode:
    """fn / stat fn / abst fn inside a Clas block"""
    def __init__(self, name, params, body, is_static=False, is_abstract=False,
                 return_type=None):
        self.name        = name
        self.params      = params
        self.body        = body
        self.is_static   = is_static
        self.is_abstract = is_abstract
        self.return_type = return_type


class GetterNode:
    """get fn name() { body }  →  @property / def name(self):"""
    def __init__(self, name, body):
        self.name = name
        self.body = body


class SetterNode:
    """set fn name(param) { body }  →  @name.setter / def name(self, param):"""
    def __init__(self, name, param, body):
        self.name  = name
        self.param = param   # str — the setter's value parameter
        self.body  = body


class StaticVarNode:
    """stat varName = expr  inside a Clas block  →  class-level attribute"""
    def __init__(self, name, value):
        self.name  = name
        self.value = value


class ClassNode:
    """Clas Name[(Parents)] { [constructor] [members] }"""
    def __init__(self, name, parents, constructor, methods, is_abstract=False):
        self.name        = name
        self.parents     = parents      # [str, ...]  (was a single parent str)
        self.constructor = constructor
        self.methods     = methods      # [MethodNode|GetterNode|SetterNode|StaticVarNode, ...]
        self.is_abstract = is_abstract


class SwitchNode:
    """sw expr { cs val [if guard] { body } ... [def { body }] }"""
    def __init__(self, expr, cases, default_body):
        self.expr         = expr
        self.cases        = cases        # [(val_expr, guard_or_None, [stmt,...]), ...]
        self.default_body = default_body


class TryCatchNode:
    """
    try { } catch { }
    try { } catch TypeError { }
    try { } catch TypeError, ValueError { }
    try { } catch { } fin { }
    """
    def __init__(self, try_body, catch_body, exc_types=None, finally_body=None):
        self.try_body     = try_body
        self.catch_body   = catch_body
        self.exc_types    = exc_types or []    # [str, ...] — empty = catch all
        self.finally_body = finally_body       # [stmt, ...] or None


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
        self.value = value


class FloatNode:
    def __init__(self, value):
        self.value = value


class StringNode:
    def __init__(self, value):
        self.value = value


class BoolNode:
    def __init__(self, value):
        self.value = value


class NullNode:
    """null  →  None"""
    pass


class IdentNode:
    def __init__(self, name):
        self.name = name


class BinOpNode:
    def __init__(self, left, op, right):
        self.left  = left
        self.op    = op
        self.right = right


class UnaryOpNode:
    def __init__(self, op, operand):
        self.op      = op
        self.operand = operand


class TernaryNode:
    """cond ? then_expr : else_expr"""
    def __init__(self, cond, then_expr, else_expr):
        self.cond      = cond
        self.then_expr = then_expr
        self.else_expr = else_expr


class NullCoalNode:
    """left ?? right  →  left if left is not None else right"""
    def __init__(self, left, right):
        self.left  = left
        self.right = right


class IncrementNode:
    """x++  →  x += 1"""
    def __init__(self, operand):
        self.operand = operand


class DecrementNode:
    """x--  →  x -= 1"""
    def __init__(self, operand):
        self.operand = operand


class LambdaNode:
    """lam x, y -> expr  →  lambda x, y: expr"""
    def __init__(self, params, body_expr):
        self.params    = params       # [str, ...]
        self.body_expr = body_expr    # expression node


class AnonFnNode:
    """fn(params) { body }  — anonymous function expression"""
    def __init__(self, params, body):
        self.params = params
        self.body   = body


class YieldExprNode:
    """yld expr used as an expression (rare, but valid in Python)"""
    def __init__(self, expr=None):
        self.expr = expr


class SpreadNode:
    """...expr  — spread/unpack inside array literals or call args"""
    def __init__(self, expr):
        self.expr = expr


class SliceNode:
    """start..end  — used as the index inside obj[start..end]"""
    def __init__(self, start, end):
        self.start = start
        self.end   = end


class ComprehensionNode:
    """[expr for var in iterable (if cond)]  →  Python list comprehension"""
    def __init__(self, expr, var, iterable, cond=None):
        self.expr     = expr
        self.var      = var       # str
        self.iterable = iterable
        self.cond     = cond      # expression node or None


class DictComprehensionNode:
    """{key: val for k[, v] in iterable [if cond]}  →  Python dict comprehension"""
    def __init__(self, key_expr, val_expr, key_var, val_var, iterable, cond=None):
        self.key_expr  = key_expr
        self.val_expr  = val_expr
        self.key_var   = key_var   # str
        self.val_var   = val_var   # str or None (single-var form)
        self.iterable  = iterable
        self.cond      = cond


class CallNode:
    """callee(args)"""
    def __init__(self, callee, args):
        self.callee = callee
        self.args   = args


class MethodCallNode:
    """obj.method(args)"""
    def __init__(self, obj, method, args):
        self.obj    = obj
        self.method = method
        self.args   = args


class AttrNode:
    """obj.attr"""
    def __init__(self, obj, attr):
        self.obj  = obj
        self.attr = attr


class IndexNode:
    """obj[index]  — index may be a SliceNode for slices"""
    def __init__(self, obj, index):
        self.obj   = obj
        self.index = index


class ArrayNode:
    """[elem, ...]"""
    def __init__(self, elements):
        self.elements = elements


class HashmapNode:
    """{key: val, ...}"""
    def __init__(self, pairs):
        self.pairs = pairs


class InputExprNode:
    """inp prompt_expr  →  input(prompt_expr)"""
    def __init__(self, prompt):
        self.prompt = prompt


class SuperCallNode:
    """sup(args)  →  super().__init__(args)"""
    def __init__(self, args):
        self.args = args


class KwargNode:
    """name=value inside a call arg list  →  Python keyword argument"""
    def __init__(self, name, value):
        self.name  = name
        self.value = value
