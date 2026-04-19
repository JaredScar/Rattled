#
# Rattled Programming Language — Transpiler
#
# Walks the AST produced by the Parser and emits valid Python 3 source code.
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
_INTERP_RE = re.compile(r'\{(\w[^}]*)\}')


class TranspileError(Exception):
    pass


class Transpiler:
    def __init__(self, filename='<input>'):
        self.filename      = filename
        self._lines        = []
        self._indent       = 0
        self._fn_depth     = 0
        self._scopes       = [set()]
        self._needs_sys    = False
        self._needs_abc    = False
        self._used_std     = set()
        self._anon_counter = 0

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
        if self._needs_abc:
            prelude.append('from abc import ABC, abstractmethod')
        if self._used_std:
            prelude.append(RATTLED_STD)

        return ('\n'.join(prelude) + ('\n' if prelude else '')) + body

    # ═══════════════════════════════════════════════════════════════
    # Emit helpers
    # ═══════════════════════════════════════════════════════════════

    def _emit(self, line, ry_line=0):
        indent     = '    ' * self._indent
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
        ry = getattr(node, 'line', 0)

        if isinstance(node, AnnotatedAssignNode):
            name_s = node.target.name
            if node.rhs is not None:
                self._emit('{}: {} = {}'.format(
                    name_s, node.type_ann, self._expr(node.rhs)), ry)
                self._track(name_s)
            else:
                self._emit('{}: {}'.format(name_s, node.type_ann), ry)

        elif isinstance(node, AssignNode):
            lhs = self._lhs(node.lhs)
            rhs = self._expr(node.rhs)
            self._emit('{} = {}'.format(lhs, rhs), ry)
            if isinstance(node.lhs, IdentNode):
                self._track(node.lhs.name)

        elif isinstance(node, AugAssignNode):
            lhs = self._lhs(node.lhs)
            rhs = self._expr(node.rhs)
            self._emit('{} {} {}'.format(lhs, node.op, rhs), ry)
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
            self._emit('open({}, "r").read()'.format(
                self._expr(node.path_expr)), ry)

        elif isinstance(node, WriteFileNode):
            self._emit('open({}, "w").write({})'.format(
                self._expr(node.path_expr),
                self._expr(node.content_expr)), ry)

        elif isinstance(node, FlushNode):
            self._needs_sys = True
            self._emit('sys.stdout.flush()', ry)

        elif isinstance(node, ImportNode):
            if node.names == ['*']:
                self._emit('from {} import *'.format(node.module), ry)
            elif node.names:
                self._emit('from {} import {}'.format(
                    node.module, ', '.join(node.names)), ry)
            elif node.alias:
                self._emit('import {} as {}'.format(node.module, node.alias), ry)
            else:
                self._emit('import {}'.format(node.module), ry)

        elif isinstance(node, ReturnNode):
            if node.expr is None:
                self._emit('return', ry)
            else:
                self._emit('return {}'.format(self._expr(node.expr)), ry)

        elif isinstance(node, YieldNode):
            if node.expr is None:
                self._emit('yield', ry)
            else:
                self._emit('yield {}'.format(self._expr(node.expr)), ry)

        elif isinstance(node, ThrowNode):
            if node.expr is None:
                self._emit('raise', ry)
            else:
                self._emit('raise {}'.format(self._expr(node.expr)), ry)

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

        elif isinstance(node, ForEachNode):
            self._emit('for {} in {}:'.format(
                node.var, self._expr(node.iterable)), ry)
            self._enter_scope()
            self._track(node.var)
            for s in node.body:
                self._stmt(s)
            if not node.body:
                self._emit('pass')
            self._leave_scope()

        elif isinstance(node, ForEachPairsNode):
            # Iterate dict items: for k, v in myMap { }
            self._emit('for {}, {} in {}.items():'.format(
                node.key_var, node.val_var,
                self._expr(node.iterable)), ry)
            self._enter_scope()
            self._track(node.key_var)
            self._track(node.val_var)
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
            ret_ann    = ' -> {}'.format(node.return_type) if node.return_type else ''
            self._emit('def {}({}){}:'.format(node.name, params_str, ret_ann), ry)
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
            if node.exc_types:
                if len(node.exc_types) == 1:
                    exc_str = node.exc_types[0]
                else:
                    exc_str = '({})'.format(', '.join(node.exc_types))
                self._emit('except {}:'.format(exc_str))
            else:
                self._emit('except Exception:')
            self._emit_block(node.catch_body)
            if node.finally_body is not None:
                self._emit('finally:')
                self._emit_block(node.finally_body)

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
        parents = list(node.parents)
        if node.is_abstract:
            self._needs_abc = True
            if 'ABC' not in parents:
                parents.insert(0, 'ABC')

        if parents:
            header = 'class {}({}):'.format(node.name, ', '.join(parents))
        else:
            header = 'class {}:'.format(node.name)
        self._emit(header, ry)
        self._enter_scope()
        wrote = False

        # Static variables first (class-level attributes)
        for m in node.methods:
            if isinstance(m, StaticVarNode):
                self._emit('{} = {}'.format(m.name, self._expr(m.value)))
                wrote = True

        if node.constructor:
            c      = node.constructor
            params = self._class_params(c.params)
            self._emit('def __init__({}):'.format(params))
            self._fn_depth += 1
            self._emit_block(c.body)
            self._fn_depth -= 1
            wrote = True

        for m in node.methods:
            if isinstance(m, StaticVarNode):
                continue   # already emitted above

            if isinstance(m, MethodNode):
                if m.is_abstract:
                    self._emit('@abstractmethod')
                if m.is_static:
                    self._emit('@staticmethod')
                    params = self._fmt_params(m.params)
                else:
                    params = self._class_params(m.params)
                ret_ann = ' -> {}'.format(m.return_type) if m.return_type else ''
                self._emit('def {}({}){}:'.format(m.name, params, ret_ann))
                self._fn_depth += 1
                self._emit_block(m.body)
                self._fn_depth -= 1

            elif isinstance(m, GetterNode):
                self._emit('@property')
                self._emit('def {}(self):'.format(m.name))
                self._fn_depth += 1
                self._emit_block(m.body)
                self._fn_depth -= 1

            elif isinstance(m, SetterNode):
                self._emit('@{}.setter'.format(m.name))
                self._emit('def {}(self, {}):'.format(m.name, m.param))
                self._fn_depth += 1
                self._emit_block(m.body)
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
        for val, guard, body in node.cases:
            kw = 'if' if first else 'elif'
            val_s = self._expr(val)
            # Type-check case:  cs str { }  /  cs MyClass { }
            # Detected when case value is a plain identifier that is either
            # capitalised (user-defined class) or a known built-in type name.
            _BUILTIN_TYPES = frozenset({
                'str', 'int', 'float', 'bool', 'list', 'dict',
                'tuple', 'set', 'bytes', 'bytearray',
            })
            is_type = (isinstance(val, IdentNode) and
                       (val.name[:1].isupper() or val.name in _BUILTIN_TYPES))
            if is_type:
                condition = 'isinstance({}, {})'.format(expr_py, val_s)
            else:
                condition = '{} == {}'.format(expr_py, val_s)
            if guard is not None:
                condition = '({}) and ({})'.format(condition, self._expr(guard))
            self._emit('{} {}:'.format(kw, condition), ry if first else 0)
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
        if isinstance(node, ArrayNode):
            # Destructuring:  [a, b, ...rest] = expr  →  a, b, *rest = expr
            parts = []
            for e in node.elements:
                if isinstance(e, SpreadNode):
                    if not isinstance(e.expr, IdentNode):
                        self._err('Spread in destructuring must be a simple name')
                    parts.append('*' + e.expr.name)
                elif isinstance(e, IdentNode):
                    parts.append(e.name)
                else:
                    self._err('Destructuring targets must be identifiers')
            return ', '.join(parts)
        self._err('Invalid assignment target: {}'.format(type(node).__name__))

    # ═══════════════════════════════════════════════════════════════
    # pr auto-cast helpers
    # ═══════════════════════════════════════════════════════════════

    def _pr_expr(self, node):
        if isinstance(node, BinOpNode) and node.op == '+':
            if self._chain_has_string(node):
                parts    = self._collect_concat_parts(node)
                rendered = [self._pr_auto_wrap(p) for p in parts]
                return ' + '.join(rendered)
        return self._expr(node)

    def _chain_has_string(self, node):
        if isinstance(node, StringNode):
            return True
        if isinstance(node, BinOpNode) and node.op == '+':
            return (self._chain_has_string(node.left)
                    or self._chain_has_string(node.right))
        return False

    def _pr_auto_wrap(self, part):
        if isinstance(part, StringNode):
            return self._render_string(part)
        if (isinstance(part, CallNode)
                and isinstance(part.callee, IdentNode)
                and part.callee.name == 'str'):
            return self._expr(part)
        return 'str({})'.format(self._expr(part))

    def _collect_concat_parts(self, node):
        if isinstance(node, BinOpNode) and node.op == '+':
            if self._chain_has_string(node.left) or self._chain_has_string(node.right):
                return (self._collect_concat_parts(node.left)
                        + self._collect_concat_parts(node.right))
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

        if isinstance(node, TernaryNode):
            cond = self._expr(node.cond)
            then = self._expr(node.then_expr)
            els  = self._expr(node.else_expr)
            return '({} if {} else {})'.format(then, cond, els)

        if isinstance(node, NullCoalNode):
            left  = self._expr(node.left)
            right = self._expr(node.right)
            # Simple identifier — no double-evaluation concern
            if isinstance(node.left, IdentNode):
                return '({} if {} is not None else {})'.format(left, left, right)
            # Complex expression — evaluate once with walrus (Python 3.8+)
            tmp = '_ry_nc{}'.format(self._anon_counter)
            self._anon_counter += 1
            return '(({t} := {l}) if ({t} := {l}) is not None else {r})'.format(
                t=tmp, l=left, r=right)

        if isinstance(node, LambdaNode):
            params_str = ', '.join(node.params)
            body_str   = self._expr(node.body_expr)
            return '(lambda {}: {})'.format(params_str, body_str)

        if isinstance(node, AnonFnNode):
            # If body is exactly one return statement, use lambda
            if (len(node.body) == 1
                    and isinstance(node.body[0], ReturnNode)
                    and node.body[0].expr is not None):
                params_str = self._fmt_params(node.params)
                body_str   = self._expr(node.body[0].expr)
                return '(lambda {}: {})'.format(params_str, body_str)
            self._err(
                'Multi-line anonymous functions must use a named function. '
                'Use:  fn myName(params) { body }')

        if isinstance(node, SpreadNode):
            return '*{}'.format(self._expr(node.expr))

        if isinstance(node, SliceNode):
            return '{}:{}'.format(self._expr(node.start), self._expr(node.end))

        if isinstance(node, ComprehensionNode):
            expr_s = self._expr(node.expr)
            iter_s = self._expr(node.iterable)
            cond_s = ' if {}'.format(self._expr(node.cond)) if node.cond else ''
            return '[{} for {} in {}{}]'.format(expr_s, node.var, iter_s, cond_s)

        if isinstance(node, DictComprehensionNode):
            k_s    = self._expr(node.key_expr)
            v_s    = self._expr(node.val_expr)
            iter_s = self._expr(node.iterable)
            cond_s = ' if {}'.format(self._expr(node.cond)) if node.cond else ''
            if node.val_var:
                # Two-variable form  {k: v for k, v in d}  →  iterate dict items
                return '{{{}: {} for {}, {} in {}.items(){}}}'.format(
                    k_s, v_s, node.key_var, node.val_var, iter_s, cond_s)
            else:
                return '{{{}: {} for {} in {}{}}}'.format(
                    k_s, v_s, node.key_var, iter_s, cond_s)

        if isinstance(node, KwargNode):
            return '{}={}'.format(node.name, self._expr(node.value))

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
            idx = node.index
            if isinstance(idx, SliceNode):
                return '{}[{}:{}]'.format(
                    self._expr(node.obj),
                    self._expr(idx.start),
                    self._expr(idx.end))
            return '{}[{}]'.format(self._expr(node.obj), self._expr(idx))

        if isinstance(node, ArrayNode):
            parts = []
            for e in node.elements:
                if isinstance(e, SpreadNode):
                    parts.append('*{}'.format(self._expr(e.expr)))
                else:
                    parts.append(self._expr(e))
            return '[{}]'.format(', '.join(parts))

        if isinstance(node, HashmapNode):
            pairs = ', '.join(
                '{}: {}'.format(self._expr(k), self._expr(v))
                for k, v in node.pairs)
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
        if _INTERP_RE.search(node.value):
            return 'f' + repr(node.value)
        return repr(node.value)

    # ═══════════════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════════════

    def _fmt_params(self, params):
        parts = []
        for param in params:
            name     = param[0]
            default  = param[1] if len(param) > 1 else None
            type_ann = param[2] if len(param) > 2 else None
            if name.startswith('**') or name.startswith('*'):
                parts.append(name)   # * / ** already in the name string
            elif type_ann and default is None:
                parts.append('{}: {}'.format(name, type_ann))
            elif type_ann and default is not None:
                parts.append('{}: {} = {}'.format(name, type_ann, self._expr(default)))
            elif default is None:
                parts.append(name)
            else:
                parts.append('{} = {}'.format(name, self._expr(default)))
        return ', '.join(parts)


def _find_loop_var(node):
    """Return the name of the first IdentNode found in the expression tree."""
    if isinstance(node, IdentNode):
        return node.name
    if isinstance(node, BinOpNode):
        left = _find_loop_var(node.left)
        return left if left else _find_loop_var(node.right)
    return None
