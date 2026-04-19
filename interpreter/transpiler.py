#
# Rattled Programming Language — Transpiler
#
# Walks the AST produced by the Parser and emits valid Python 3 source code.
#
# Key behaviours
#   - Indentation is tracked by _indent (4 spaces per level).
#   - Cast functions (flo, boo) are remapped to Python builtins.
#   - `for` loops auto-initialise and auto-increment their loop variable.
#   - Class methods automatically receive `self` as their first parameter.
#   - Logical operators &&/|| are mapped to and/or.
#   - The standard-library preamble is only prepended when std-lib symbols
#     are actually used in the program.
#
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ast_nodes import *
from constants import CAST_MAP, METHOD_ALIAS, LEN_METHOD, LOGICAL_OP, STD_FUNCS
from rattled_std import RATTLED_STD


class TranspileError(Exception):
    pass


class Transpiler:
    def __init__(self, filename='<input>'):
        self.filename  = filename
        self._lines    = []
        self._indent   = 0
        self._fn_depth = 0          # >0 when inside a function/method
        # stack of variable-name sets, one per lexical scope
        self._scopes   = [set()]
        self._needs_sys = False     # whether 'import sys' must be prepended
        self._used_std  = set()     # names of std-lib functions that were called

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

    def _emit(self, line):
        self._lines.append('    ' * self._indent + line)

    def _enter_scope(self):
        self._indent += 1
        self._scopes.append(set())

    def _leave_scope(self):
        self._indent -= 1
        self._scopes.pop()

    def _track(self, name):
        """Mark a variable as declared in the current scope."""
        self._scopes[-1].add(name)

    def _is_declared(self, name):
        """Check if a variable has been declared in any enclosing scope."""
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
        if isinstance(node, AssignNode):
            self._do_assign(node)
        elif isinstance(node, GlobalAssignNode):
            self._do_global_assign(node)
        elif isinstance(node, GlobalDeclNode):
            if self._fn_depth > 0:
                self._emit('global {}'.format(node.name))
        elif isinstance(node, PrintNode):
            self._emit('print({})'.format(self._expr(node.expr)))
        elif isinstance(node, ReadFileNode):
            # rd used as a statement (result discarded)
            self._emit('open({}, "r").read()'.format(self._expr(node.path_expr)))
        elif isinstance(node, WriteFileNode):
            self._emit('open({}, "w").write({})'.format(
                self._expr(node.path_expr), self._expr(node.content_expr)))
        elif isinstance(node, FlushNode):
            self._needs_sys = True
            self._emit('sys.stdout.flush()')
        elif isinstance(node, ImportNode):
            if node.names:
                self._emit('from {} import {}'.format(
                    node.module, ', '.join(node.names)))
            else:
                self._emit('import {}'.format(node.module))
        elif isinstance(node, ReturnNode):
            if node.expr is None:
                self._emit('return')
            else:
                self._emit('return {}'.format(self._expr(node.expr)))
        elif isinstance(node, IfNode):
            self._do_if(node)
        elif isinstance(node, ForNode):
            self._do_for(node)
        elif isinstance(node, WhileNode):
            self._do_while(node)
        elif isinstance(node, FnDefNode):
            self._do_fn(node)
        elif isinstance(node, ClassNode):
            self._do_class(node)
        elif isinstance(node, SwitchNode):
            self._do_switch(node)
        elif isinstance(node, TryCatchNode):
            self._do_try_catch(node)
        elif isinstance(node, ExprStmtNode):
            self._do_expr_stmt(node.expr)
        else:
            self._err('Unknown statement node: {}'.format(type(node).__name__))

    # ── assignment ────────────────────────────────────────────────

    def _do_assign(self, node):
        lhs = self._lhs(node.lhs)
        rhs = self._expr(node.rhs)
        self._emit('{} = {}'.format(lhs, rhs))
        if isinstance(node.lhs, IdentNode):
            self._track(node.lhs.name)

    def _do_global_assign(self, node):
        if self._fn_depth > 0:
            self._emit('global {}'.format(node.name))
        self._emit('{} = {}'.format(node.name, self._expr(node.rhs)))
        self._track(node.name)

    def _lhs(self, node):
        """Render an LHS target to a Python string."""
        if isinstance(node, IdentNode):
            return node.name
        if isinstance(node, AttrNode):
            return '{}.{}'.format(self._expr(node.obj), node.attr)
        if isinstance(node, IndexNode):
            return '{}[{}]'.format(self._expr(node.obj), self._expr(node.index))
        self._err('Invalid assignment target: {}'.format(type(node).__name__))

    # ── control flow ──────────────────────────────────────────────

    def _do_if(self, node):
        self._emit('if {}:'.format(self._expr(node.cond)))
        self._emit_block(node.body)

        for cond, body in node.elif_clauses:
            self._emit('elif {}:'.format(self._expr(cond)))
            self._emit_block(body)

        if node.else_body is not None:
            self._emit('else:')
            self._emit_block(node.else_body)

    def _do_for(self, node):
        """
        for cond { body }
        Finds the first identifier in cond, auto-initialises it to 0 if it
        has not been previously declared, then emits a while loop with
        auto-increment at the bottom of every iteration.
        """
        loop_var = _find_loop_var(node.cond)
        if loop_var and not self._is_declared(loop_var):
            self._emit('{} = 0'.format(loop_var))
            self._track(loop_var)

        self._emit('while {}:'.format(self._expr(node.cond)))
        self._enter_scope()
        for s in node.body:
            self._stmt(s)
        if loop_var:
            self._emit('{} += 1'.format(loop_var))
        elif not node.body:
            self._emit('pass')
        self._leave_scope()

    def _do_while(self, node):
        self._emit('while {}:'.format(self._expr(node.cond)))
        self._emit_block(node.body)

    # ── functions & classes ───────────────────────────────────────

    def _do_fn(self, node):
        params_str = self._fmt_params(node.params)
        self._emit('def {}({}):'.format(node.name, params_str))
        self._fn_depth += 1
        self._emit_block(node.body)
        self._fn_depth -= 1

    def _do_class(self, node):
        header = 'class {}({}):'.format(node.name, node.parent) \
                 if node.parent else 'class {}:'.format(node.name)
        self._emit(header)
        self._enter_scope()

        wrote_something = False

        if node.constructor:
            c      = node.constructor
            params = self._class_params(c.params)
            self._emit('def __init__({}):'.format(params))
            self._fn_depth += 1
            self._emit_block(c.body)
            self._fn_depth -= 1
            wrote_something = True

        for meth in node.methods:
            params = self._class_params(meth.params)
            self._emit('def {}({}):'.format(meth.name, params))
            self._fn_depth += 1
            self._emit_block(meth.body)
            self._fn_depth -= 1
            wrote_something = True

        if not wrote_something:
            self._emit('pass')

        self._leave_scope()

    def _class_params(self, raw_params):
        """Prepend 'self' to a parameter list if it's not already there."""
        if raw_params and raw_params[0][0] == 'self':
            return self._fmt_params(raw_params)
        return self._fmt_params([('self', None)] + raw_params)

    # ── switch ────────────────────────────────────────────────────

    def _do_switch(self, node):
        expr_py = self._expr(node.expr)
        first   = True
        for val, body in node.cases:
            kw = 'if' if first else 'elif'
            self._emit('{} {} == {}:'.format(kw, expr_py, self._expr(val)))
            self._emit_block(body)
            first = False
        if node.default_body is not None:
            kw = 'else' if not first else 'if True'
            self._emit('{}:'.format(kw))
            self._emit_block(node.default_body)

    # ── try / catch ───────────────────────────────────────────────

    def _do_try_catch(self, node):
        self._emit('try:')
        self._emit_block(node.try_body)
        self._emit('except Exception:')
        self._emit_block(node.catch_body)

    # ── expression statements ─────────────────────────────────────

    def _do_expr_stmt(self, node):
        if isinstance(node, IncrementNode):
            self._emit('{} += 1'.format(self._lhs(node.operand)))
        elif isinstance(node, DecrementNode):
            self._emit('{} -= 1'.format(self._lhs(node.operand)))
        else:
            self._emit(self._expr(node))

    # ─── shared block emitter ─────────────────────────────────────

    def _emit_block(self, stmts):
        self._enter_scope()
        if stmts:
            for s in stmts:
                self._stmt(s)
        else:
            self._emit('pass')
        self._leave_scope()

    # ═══════════════════════════════════════════════════════════════
    # Expression transpilation
    # ═══════════════════════════════════════════════════════════════

    def _expr(self, node):
        if isinstance(node, IntNode):
            return str(node.value)

        if isinstance(node, FloatNode):
            return repr(node.value)

        if isinstance(node, StringNode):
            return repr(node.value)

        if isinstance(node, BoolNode):
            return 'True' if node.value else 'False'

        if isinstance(node, NullNode):
            return 'None'

        if isinstance(node, IdentNode):
            # remap flo → float, boo → bool; str/int pass through unchanged
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
            # callee is a complex expression
            callee = self._expr(node.callee)
            args   = ', '.join(self._expr(a) for a in node.args)
            return '{}({})'.format(callee, args)

        if isinstance(node, MethodCallNode):
            obj    = self._expr(node.obj)
            method = node.method
            args   = ', '.join(self._expr(a) for a in node.args)
            # built-in method aliases
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

        # Increment / decrement used inside an expression (side-effect value)
        # — we emit the operand only; the += is handled at statement level.
        if isinstance(node, IncrementNode):
            return self._expr(node.operand)

        if isinstance(node, DecrementNode):
            return self._expr(node.operand)

        self._err('Unknown expression node: {}'.format(type(node).__name__))

    # ═══════════════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════════════

    def _fmt_params(self, params):
        """Format [(name, default_or_None), ...] → 'name, name=default, ...'"""
        parts = []
        for name, default in params:
            if default is None:
                parts.append(name)
            else:
                parts.append('{}={}'.format(name, self._expr(default)))
        return ', '.join(parts)


# ── module-level helper (no self needed) ─────────────────────────────────────

def _find_loop_var(node):
    """Return the name of the first IdentNode found in the expression tree."""
    if isinstance(node, IdentNode):
        return node.name
    if isinstance(node, BinOpNode):
        left = _find_loop_var(node.left)
        return left if left else _find_loop_var(node.right)
    return None
