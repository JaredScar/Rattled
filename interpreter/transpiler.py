#
# Rattled Programming Language — Transpiler
#
# Walks the AST produced by the Parser and emits valid Python 3 source code.
#
# Features
#   - pr auto-cast: "Name: " + age works without str(age)
#   - String interpolation: "Hello {name}" emits f"Hello {name}"
#   - for range form: for i in 0..10 emits for i in range(0, 10):
#   - brk / cont: break / continue
#   - stat fn: @staticmethod decorator on class methods
#   - Typed catch: catch ValueError { } -> except ValueError:
#   - Line-number annotations: # ry:N on every emitted statement
#
import re
import sys
import os

try:
    from .ast_nodes import *
    from .constants import CAST_MAP, METHOD_ALIAS, LEN_METHOD, LOGICAL_OP, STD_FUNCS
    from .rattled_std import RATTLED_STD
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from ast_nodes import *
    from constants import CAST_MAP, METHOD_ALIAS, LEN_METHOD, LOGICAL_OP, STD_FUNCS
    from rattled_std import RATTLED_STD

# Matches {identifier} or {identifier.attr} inside strings — triggers f-string
_INTERP_RE = re.compile(r'\{(\w[\w.]*)\}')


class TranspileError(Exception):
    pass


class Transpiler:
    def __init__(self, filename='<input>'):
        self.filename   = filename
        self._lines     = []
        self._indent    = 0
        self._fn_depth  = 0          # >0 when inside a function/method
        self._scopes    = [set()]    # stack of declared-var name sets
        self._needs_sys = False
        self._used_std  = set()

    # ═══════════════════════════════════════════════════════════════
    # Public interface
    # ═══════════════════════════════════════════════════════════════

    def transpile(self, program_node):
        for stmt in program_node.stmts:
            self._stmt(stmt)

        body = '\n'.join(self._lines)

        prelude = []
        if self._needs_sys:
            prelude.append('import sys')
        if self._used_std:
            prelude.append(RATTLED_STD)

        return ('\n'.join(prelude) + ('\n' if prelude else '')) + body

    # ═══════════════════════════════════════════════════════════════
    # Emit helpers
    # ═══════════════════════════════════════════════════════════════

    def _emit(self, line, ry_line=0):
        """Emit one Python line, optionally annotated with the Rattled source line."""
        indent = '    ' * self._indent
        annotation = '  # ry:{}'.format(ry_line) if ry_line else ''
        self._lines.append('{}{}{}'.format(indent, line, annotation))

    def _enter_scope(self):
        self._indent += 1
        self._scopes.append(set())

    def _leave_scope(self):
        self._indent -= 1
        self._scopes.pop()

    def _track(self, name):
        self._scopes[-1].add(name)

    def _is_declared(self, name):
        for scope in self._scopes:
            if name in scope:
                return True
        return False

    def _err(self, msg):
        raise TranspileError('[Rattled Transpiler] {}: {}'.format(self.filename, msg))

    # ═══════════════════════════════════════════════════════════════
    # Statement transpilation
    # ═══════════════════════════════════════════════════════════════

    def _stmt(self, node):
        ry = getattr(node, 'line', 0)   # Rattled source line for annotation

        if isinstance(node, AssignNode):
            lhs = self._lhs(node.lhs)
            rhs = self._expr(node.rhs)
            self._emit('{} = {}'.format(lhs, rhs), ry)
            if isinstance(node.lhs, IdentNode):
                self._track(node.lhs.name)

        elif isinstance(node, GlobalAssignNode):
            if self._fn_depth > 0:
                self._emit('global {}'.format(node.name), ry)
            self._emit('{} = {}'.format(node.name, self._expr(node.rhs)), ry)
            self._track(node.name)

        elif isinstance(node, GlobalDeclNode):
            if self._fn_depth > 0:
                self._emit('global {}'.format(node.name), ry)

        elif isinstance(node, PrintNode):
            self._emit('print({})'.format(self._pr_expr(node.expr)), ry)

        elif isinstance(node, ReadFileNode):
            self._emit('open({}, "r").read()'.format(self._expr(node.path_expr)), ry)

        elif isinstance(node, WriteFileNode):
            self._emit('open({}, "w").write({})'.format(
                self._expr(node.path_expr), self._expr(node.content_expr)), ry)

        elif isinstance(node, FlushNode):
            self._needs_sys = True
            self._emit('sys.stdout.flush()', ry)

        elif isinstance(node, ImportNode):
            if node.names:
                self._emit('from {} import {}'.format(
                    node.module, ', '.join(node.names)), ry)
            else:
                self._emit('import {}'.format(node.module), ry)

        elif isinstance(node, ReturnNode):
            if node.expr is None:
                self._emit('return', ry)
            else:
                self._emit('return {}'.format(self._expr(node.expr)), ry)

        elif isinstance(node, BreakNode):
            self._emit('break', ry)

        elif isinstance(node, ContinueNode):
            self._emit('continue', ry)

        elif isinstance(node, IfNode):
            self._emit('if {}:'.format(self._expr(node.cond)), ry)
            self._emit_block(node.body)
            for cond, body in node.elif_clauses:
                self._emit('elif {}:'.format(self._expr(cond)))
                self._emit_block(body)
            if node.else_body is not None:
                self._emit('else:')
                self._emit_block(node.else_body)

        elif isinstance(node, ForNode):
            self._do_for(node, ry)

        elif isinstance(node, ForRangeNode):
            self._emit('for {} in range({}, {}):'.format(
                node.var, self._expr(node.start), self._expr(node.end)), ry)
            self._enter_scope()
            self._track(node.var)
            for s in node.body:
                self._stmt(s)
            if not node.body:
                self._emit('pass')
            self._leave_scope()

        elif isinstance(node, WhileNode):
            self._emit('while {}:'.format(self._expr(node.cond)), ry)
            self._emit_block(node.body)

        elif isinstance(node, FnDefNode):
            params_str = self._fmt_params(node.params)
            self._emit('def {}({}):'.format(node.name, params_str), ry)
            self._fn_depth += 1
            self._emit_block(node.body)
            self._fn_depth -= 1

        elif isinstance(node, ClassNode):
            self._do_class(node, ry)

        elif isinstance(node, SwitchNode):
            self._do_switch(node, ry)

        elif isinstance(node, TryCatchNode):
            self._emit('try:', ry)
            self._emit_block(node.try_body)
            exc = node.exc_type if node.exc_type else 'Exception'
            self._emit('except {}:'.format(exc))
            self._emit_block(node.catch_body)

        elif isinstance(node, ExprStmtNode):
            self._do_expr_stmt(node.expr, ry)

        else:
            self._err('Unknown statement node: {}'.format(type(node).__name__))

    # ── for (condition form) ──────────────────────────────────────

    def _do_for(self, node, ry=0):
        loop_var = _find_loop_var(node.cond)
        if loop_var and not self._is_declared(loop_var):
            self._emit('{} = 0'.format(loop_var), ry)
            self._track(loop_var)
        self._emit('while {}:'.format(self._expr(node.cond)), ry)
        self._enter_scope()
        for s in node.body:
            self._stmt(s)
        if loop_var:
            self._emit('{} += 1'.format(loop_var))
        elif not node.body:
            self._emit('pass')
        self._leave_scope()

    # ── class ─────────────────────────────────────────────────────

    def _do_class(self, node, ry=0):
        header = 'class {}({}):'.format(node.name, node.parent) \
                 if node.parent else 'class {}:'.format(node.name)
        self._emit(header, ry)
        self._enter_scope()
        wrote = False

        if node.constructor:
            c      = node.constructor
            params = self._class_params(c.params)
            self._emit('def __init__({}):'.format(params))
            self._fn_depth += 1
            self._emit_block(c.body)
            self._fn_depth -= 1
            wrote = True

        for meth in node.methods:
            if meth.is_static:
                self._emit('@staticmethod')
                params = self._fmt_params(meth.params)
            else:
                params = self._class_params(meth.params)
            self._emit('def {}({}):'.format(meth.name, params))
            self._fn_depth += 1
            self._emit_block(meth.body)
            self._fn_depth -= 1
            wrote = True

        if not wrote:
            self._emit('pass')
        self._leave_scope()

    def _class_params(self, raw_params):
        if raw_params and raw_params[0][0] == 'self':
            return self._fmt_params(raw_params)
        return self._fmt_params([('self', None)] + raw_params)

    # ── switch ────────────────────────────────────────────────────

    def _do_switch(self, node, ry=0):
        expr_py = self._expr(node.expr)
        first   = True
        for val, body in node.cases:
            kw = 'if' if first else 'elif'
            self._emit('{} {} == {}:'.format(kw, expr_py, self._expr(val)),
                       ry if first else 0)
            self._emit_block(body)
            first = False
        if node.default_body is not None:
            kw = 'else' if not first else 'if True'
            self._emit('{}:'.format(kw))
            self._emit_block(node.default_body)

    # ── expression statements ─────────────────────────────────────

    def _do_expr_stmt(self, node, ry=0):
        if isinstance(node, IncrementNode):
            self._emit('{} += 1'.format(self._lhs(node.operand)), ry)
        elif isinstance(node, DecrementNode):
            self._emit('{} -= 1'.format(self._lhs(node.operand)), ry)
        else:
            self._emit(self._expr(node), ry)

    # ── shared block emitter ──────────────────────────────────────

    def _emit_block(self, stmts):
        self._enter_scope()
        if stmts:
            for s in stmts:
                self._stmt(s)
        else:
            self._emit('pass')
        self._leave_scope()

    # ── lhs helper ───────────────────────────────────────────────

    def _lhs(self, node):
        if isinstance(node, IdentNode):
            return node.name
        if isinstance(node, AttrNode):
            return '{}.{}'.format(self._expr(node.obj), node.attr)
        if isinstance(node, IndexNode):
            return '{}[{}]'.format(self._expr(node.obj), self._expr(node.index))
        self._err('Invalid assignment target: {}'.format(type(node).__name__))

    # ═══════════════════════════════════════════════════════════════
    # pr auto-cast helpers
    # ═══════════════════════════════════════════════════════════════

    def _pr_expr(self, node):
        """
        Render an expression for use in a pr statement.
        If the expression is a + chain containing at least one string literal,
        each non-string segment is automatically wrapped in str() so that
        pr "Name: " + name + " age: " + age works without explicit casting.

        Crucially, arithmetic sub-expressions that have no string literals
        are kept as a unit (not recursed into), so that:
          pr "result = " + (a + b)  →  print('result = ' + str(a + b))
        and NOT:
          print('result = ' + str(a) + str(b))   # wrong: gives "103" for 10+3
        """
        if isinstance(node, BinOpNode) and node.op == '+':
            if self._chain_has_string(node):
                parts    = self._collect_concat_parts(node)
                rendered = [self._pr_auto_wrap(p) for p in parts]
                return ' + '.join(rendered)
        # Single value: Python's print() handles any type natively.
        return self._expr(node)

    def _chain_has_string(self, node):
        """True if the + chain contains at least one StringNode."""
        if isinstance(node, StringNode):
            return True
        if isinstance(node, BinOpNode) and node.op == '+':
            return (self._chain_has_string(node.left)
                    or self._chain_has_string(node.right))
        return False

    def _pr_auto_wrap(self, part):
        """Wrap a concat-chain segment in str() — unless it already returns a string."""
        if isinstance(part, StringNode):
            return self._render_string(part)
        # Avoid str(str(x)) when the user already wrote str(x) explicitly.
        if (isinstance(part, CallNode)
                and isinstance(part.callee, IdentNode)
                and part.callee.name == 'str'):
            return self._expr(part)
        return 'str({})'.format(self._expr(part))

    def _collect_concat_parts(self, node):
        """
        Flatten the string-concat portion of a + chain into a flat list.
        Recurses into a child + node only when that child itself contains a
        string literal (i.e. is also a string-concat +).  Arithmetic +
        expressions that contain no string literals are left as a single unit,
        ensuring pr "sum = " + (a + b) → str(a + b) not str(a) + str(b).
        """
        if isinstance(node, BinOpNode) and node.op == '+':
            if self._chain_has_string(node.left) or self._chain_has_string(node.right):
                return (self._collect_concat_parts(node.left)
                        + self._collect_concat_parts(node.right))
            # Neither side contains a string → arithmetic expression; keep whole
            return [node]
        return [node]

    # ═══════════════════════════════════════════════════════════════
    # Expression transpilation
    # ═══════════════════════════════════════════════════════════════

    def _expr(self, node):
        if isinstance(node, IntNode):
            return str(node.value)

        if isinstance(node, FloatNode):
            return repr(node.value)

        if isinstance(node, StringNode):
            return self._render_string(node)

        if isinstance(node, BoolNode):
            return 'True' if node.value else 'False'

        if isinstance(node, NullNode):
            return 'None'

        if isinstance(node, IdentNode):
            return CAST_MAP.get(node.name, node.name)

        if isinstance(node, BinOpNode):
            op    = LOGICAL_OP.get(node.op, node.op)
            left  = self._expr(node.left)
            right = self._expr(node.right)
            return '({} {} {})'.format(left, op, right)

        if isinstance(node, UnaryOpNode):
            return '({} {})'.format(node.op, self._expr(node.operand))

        if isinstance(node, CallNode):
            if isinstance(node.callee, IdentNode):
                name    = node.callee.name
                py_name = CAST_MAP.get(name, name)
                if name in STD_FUNCS:
                    self._used_std.add(name)
                args = ', '.join(self._expr(a) for a in node.args)
                return '{}({})'.format(py_name, args)
            callee = self._expr(node.callee)
            args   = ', '.join(self._expr(a) for a in node.args)
            return '{}({})'.format(callee, args)

        if isinstance(node, MethodCallNode):
            obj    = self._expr(node.obj)
            method = node.method
            args   = ', '.join(self._expr(a) for a in node.args)
            if method in METHOD_ALIAS:
                return '{}.{}({})'.format(obj, METHOD_ALIAS[method], args)
            if method == LEN_METHOD:
                return 'len({})'.format(obj)
            return '{}.{}({})'.format(obj, method, args)

        if isinstance(node, AttrNode):
            return '{}.{}'.format(self._expr(node.obj), node.attr)

        if isinstance(node, IndexNode):
            return '{}[{}]'.format(self._expr(node.obj), self._expr(node.index))

        if isinstance(node, ArrayNode):
            elems = ', '.join(self._expr(e) for e in node.elements)
            return '[{}]'.format(elems)

        if isinstance(node, HashmapNode):
            pairs = ', '.join(
                '{}: {}'.format(self._expr(k), self._expr(v))
                for k, v in node.pairs
            )
            return '{{{}}}'.format(pairs)

        if isinstance(node, InputExprNode):
            return 'input({})'.format(self._expr(node.prompt))

        if isinstance(node, SuperCallNode):
            args = ', '.join(self._expr(a) for a in node.args)
            return 'super().__init__({})'.format(args)

        if isinstance(node, ReadFileNode):
            return 'open({}, "r").read()'.format(self._expr(node.path_expr))

        if isinstance(node, IncrementNode):
            return self._expr(node.operand)

        if isinstance(node, DecrementNode):
            return self._expr(node.operand)

        self._err('Unknown expression node: {}'.format(type(node).__name__))

    # ═══════════════════════════════════════════════════════════════
    # String interpolation
    # ═══════════════════════════════════════════════════════════════

    def _render_string(self, node):
        """
        Render a StringNode.
        If the value contains {identifier} or {identifier.attr} patterns,
        emit as a Python f-string so that "Hello {name}" works natively.
        Users who need a literal brace must double it: {{  }}
        """
        if _INTERP_RE.search(node.value):
            # repr() produces a properly quoted/escaped Python string literal.
            # Prepending 'f' turns it into an f-string.
            return 'f' + repr(node.value)
        return repr(node.value)

    # ═══════════════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════════════

    def _fmt_params(self, params):
        parts = []
        for name, default in params:
            if default is None:
                parts.append(name)
            else:
                parts.append('{}={}'.format(name, self._expr(default)))
        return ', '.join(parts)


def _find_loop_var(node):
    """Return the name of the first IdentNode found in the expression tree."""
    if isinstance(node, IdentNode):
        return node.name
    if isinstance(node, BinOpNode):
        left = _find_loop_var(node.left)
        return left if left else _find_loop_var(node.right)
    return None
