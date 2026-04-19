#
# Rattled Programming Language — Parser
#
# Recursive-descent / Pratt-operator-precedence parser.
# Consumes a flat token list produced by the Lexer and returns a ProgramNode AST.
#
import sys
import os

try:
    from .constants import (
        TT_KEYWORD, TT_IDENT, TT_STRING, TT_INT, TT_FLOAT, TT_OP,
        TT_LPAREN, TT_RPAREN, TT_LBRACE, TT_RBRACE,
        TT_LBRACKET, TT_RBRACKET, TT_COMMA, TT_DOT, TT_COLON, TT_RANGE, TT_EOF,
        OP_PREC, STD_FUNCS,
    )
    from .ast_nodes import *
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from constants import (
        TT_KEYWORD, TT_IDENT, TT_STRING, TT_INT, TT_FLOAT, TT_OP,
        TT_LPAREN, TT_RPAREN, TT_LBRACE, TT_RBRACE,
        TT_LBRACKET, TT_RBRACKET, TT_COMMA, TT_DOT, TT_COLON, TT_RANGE, TT_EOF,
        OP_PREC, STD_FUNCS,
    )
    from ast_nodes import *


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens, filename='<input>'):
        self.tokens   = tokens
        self.filename = filename
        self.pos      = 0

    # ─── private helpers ─────────────────────────────────────────────────────

    def _err(self, msg):
        tok = self._cur()
        raise ParseError('[Rattled] {}:{}: {}'.format(
            self.filename, tok.line, msg))

    def _cur(self):
        return self.tokens[self.pos]

    def _peek(self, offset=1):
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else self.tokens[-1]

    def _eat(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, type_, value=None):
        tok = self._cur()
        if tok.type != type_:
            self._err('Expected token type {} but got {} ({!r})'.format(
                type_, tok.type, tok.value))
        if value is not None and tok.value != value:
            self._err('Expected {!r} but got {!r}'.format(value, tok.value))
        return self._eat()

    def _expect_op(self, op):
        return self._expect(TT_OP, op)

    def _expect_kw(self, kw):
        return self._expect(TT_KEYWORD, kw)

    def _at_eof(self):
        return self._cur().type == TT_EOF

    def _cur_is(self, value):
        """True if the current token has the given value (regardless of type)."""
        return self._cur().value == value

    # ─── public entry point ──────────────────────────────────────────────────

    def parse(self):
        stmts = []
        while not self._at_eof():
            stmts.append(self._parse_stmt())
        return ProgramNode(stmts)

    # ─── statement dispatch ───────────────────────────────────────────────────

    def _parse_stmt(self):
        line = self._cur().line
        node = self._dispatch_stmt()
        node.line = line
        return node

    def _dispatch_stmt(self):
        tok = self._cur()

        if tok.is_kw('pr'):    return self._parse_print()
        if tok.is_kw('if'):    return self._parse_if()
        if tok.is_kw('for'):   return self._parse_for()
        if tok.is_kw('while'): return self._parse_while()
        if tok.is_kw('glo'):   return self._parse_global()
        if tok.is_kw('arr'):   return self._parse_arr_decl()
        if tok.is_kw('hashm'): return self._parse_hashm_decl()
        if tok.is_kw('imp'):   return self._parse_import()
        if tok.is_kw('ret'):   return self._parse_return()
        if tok.is_kw('sw'):    return self._parse_switch()
        if tok.is_kw('try'):   return self._parse_try()
        if tok.is_kw('rd'):    return self._parse_read_file()
        if tok.is_kw('wr'):    return self._parse_write_file()
        if tok.is_kw('Clas'):  return self._parse_class()
        if tok.is_kw('abst'):
            self._eat()   # abst
            return self._parse_class(is_abstract=True)

        if tok.is_kw('fn'):
            # Named function definition:  fn name( ...
            if self._peek().type == TT_IDENT:
                return self._parse_fn()
            # Anonymous function used as statement:  fn(...)  { }
            return self._parse_expr_stmt()

        if tok.is_kw('brk'):
            self._eat(); return BreakNode()
        if tok.is_kw('cont'):
            self._eat(); return ContinueNode()
        if tok.is_kw('fl'):
            self._eat(); return FlushNode()

        if tok.is_kw('yld'):
            self._eat()
            if self._cur().type in (TT_RBRACE, TT_EOF):
                return YieldNode(None)
            return YieldNode(self._parse_expr())

        if tok.is_kw('thr'):
            self._eat()
            if self._cur().type in (TT_RBRACE, TT_EOF):
                return ThrowNode(None)
            return ThrowNode(self._parse_expr())

        return self._parse_expr_stmt()

    # ─── individual statement parsers ─────────────────────────────────────────

    def _parse_print(self):
        self._eat()  # pr
        return PrintNode(self._parse_expr())

    def _parse_if(self):
        self._eat()  # if
        cond = self._parse_expr()
        body = self._parse_block()

        elif_clauses = []
        while self._cur().is_kw('elif'):
            self._eat()
            ec = self._parse_expr()
            eb = self._parse_block()
            elif_clauses.append((ec, eb))

        else_body = None
        if self._cur().is_kw('el'):
            self._eat()
            else_body = self._parse_block()

        return IfNode(cond, body, elif_clauses, else_body)

    def _parse_for(self):
        self._eat()  # for

        # Pairs form:  for k, v in iterable { }
        if self._cur().type == TT_IDENT and self._peek().type == TT_COMMA:
            key_var = self._eat().value
            self._eat()   # ,
            val_var = self._expect(TT_IDENT).value
            self._expect_kw('in')
            iterable = self._parse_expr()
            body     = self._parse_block()
            return ForEachPairsNode(key_var, val_var, iterable, body)

        # Range or each form:  for var in expr[..end]
        if self._cur().type == TT_IDENT and self._peek().is_kw('in'):
            var = self._eat().value    # variable name
            self._eat()                # in
            expr = self._parse_expr()
            if self._cur().type == TT_RANGE:
                # Range form:  for i in start..end { }
                self._eat()   # ..
                end  = self._parse_expr()
                body = self._parse_block()
                return ForRangeNode(var, expr, end, body)
            # Collection (each) form:  for item in iterable { }
            body = self._parse_block()
            return ForEachNode(var, expr, body)

        # Condition form:  for cond { }  (auto-init / auto-increment)
        cond = self._parse_expr()
        body = self._parse_block()
        return ForNode(cond, body)

    def _parse_while(self):
        self._eat()  # while
        cond = self._parse_expr()
        body = self._parse_block()
        return WhileNode(cond, body)

    def _parse_fn(self):
        self._eat()  # fn
        name   = self._expect(TT_IDENT).value
        params = self._parse_params()
        body   = self._parse_block()
        return FnDefNode(name, params, body)

    def _parse_class(self, is_abstract=False):
        self._eat()  # Clas
        name = self._expect(TT_IDENT).value

        # Optional parent list:  Clas Dog(Animal)  /  Clas C(A, B)
        parents = []
        if self._cur().type == TT_LPAREN:
            self._eat()
            while self._cur().type != TT_RPAREN:
                parents.append(self._expect(TT_IDENT).value)
                if self._cur().type == TT_COMMA:
                    self._eat()
            self._expect(TT_RPAREN)

        self._expect(TT_LBRACE)
        constructor = None
        methods     = []   # MethodNode | GetterNode | SetterNode | StaticVarNode

        while self._cur().type != TT_RBRACE:
            if self._at_eof():
                self._err('Unexpected EOF inside class body')

            if self._cur().is_kw('def'):             # constructor
                self._eat()
                params = self._parse_params()
                body   = self._parse_block()
                constructor = ConstructorNode(params, body)

            elif self._cur().is_kw('stat'):
                self._eat()   # stat
                if self._cur().is_kw('fn'):          # static method
                    self._eat()
                    mname  = self._expect(TT_IDENT).value
                    params = self._parse_params()
                    body   = self._parse_block()
                    methods.append(MethodNode(mname, params, body, is_static=True))
                else:                                # static class variable
                    var_name = self._expect(TT_IDENT).value
                    self._expect_op('=')
                    val = self._parse_expr()
                    methods.append(StaticVarNode(var_name, val))

            elif self._cur().is_kw('abst'):          # abstract method
                self._eat()
                self._expect_kw('fn')
                mname  = self._expect(TT_IDENT).value
                params = self._parse_params()
                body   = self._parse_block()
                methods.append(MethodNode(mname, params, body, is_abstract=True))

            elif self._cur().is_kw('fn'):            # instance method
                self._eat()
                mname  = self._expect(TT_IDENT).value
                params = self._parse_params()
                body   = self._parse_block()
                methods.append(MethodNode(mname, params, body))

            elif self._cur_is('get'):                # property getter
                self._eat()   # 'get' (contextual — not a keyword)
                self._expect_kw('fn')
                mname = self._expect(TT_IDENT).value
                self._parse_params()                 # typically empty ()
                body  = self._parse_block()
                methods.append(GetterNode(mname, body))

            elif self._cur_is('set'):                # property setter
                self._eat()   # 'set' (contextual)
                self._expect_kw('fn')
                mname  = self._expect(TT_IDENT).value
                params = self._parse_params()
                body   = self._parse_block()
                param_name = params[0][0] if params else 'value'
                methods.append(SetterNode(mname, param_name, body))

            else:
                self._err(
                    'Expected def, fn, stat, abst fn, get fn, or set fn in class '
                    'body; got {!r}'.format(self._cur().value))

        self._expect(TT_RBRACE)
        return ClassNode(name, parents, constructor, methods, is_abstract)

    def _parse_global(self):
        self._eat()  # glo
        name = self._expect(TT_IDENT).value
        if self._cur().is_op('='):
            self._eat()
            return GlobalAssignNode(name, self._parse_expr())
        return GlobalDeclNode(name)

    def _parse_arr_decl(self):
        self._eat()  # arr
        name = self._expect(TT_IDENT).value
        self._expect_op('=')
        return AssignNode(IdentNode(name), self._parse_expr())

    def _parse_hashm_decl(self):
        self._eat()  # hashm
        name = self._expect(TT_IDENT).value
        self._expect_op('=')
        return AssignNode(IdentNode(name), self._parse_expr())

    def _parse_import(self):
        self._eat()  # imp
        tok = self._cur()

        # Wildcard:  imp * from math
        if tok.type == TT_OP and tok.value == '*':
            self._eat()
            self._expect_kw('from')
            module = self._expect(TT_IDENT).value
            return ImportNode(module=module, names=['*'])

        if tok.type not in (TT_IDENT, TT_KEYWORD):
            self._err('Expected module or symbol name after imp')
        name = self._eat().value

        # Alias:  imp numpy as np
        if self._cur_is('as'):
            self._eat()   # 'as' (contextual keyword / ident)
            alias = self._expect(TT_IDENT).value
            return ImportNode(module=name, names=[], alias=alias)

        # Named:  imp sqrt from math
        if self._cur().is_kw('from'):
            self._eat()
            module = self._expect(TT_IDENT).value
            return ImportNode(module=module, names=[name])

        return ImportNode(module=name, names=[])

    def _parse_return(self):
        self._eat()  # ret
        if self._cur().type in (TT_RBRACE, TT_EOF):
            return ReturnNode(None)
        return ReturnNode(self._parse_expr())

    def _parse_switch(self):
        self._eat()  # sw
        expr = self._parse_expr()
        self._expect(TT_LBRACE)
        cases        = []
        default_body = None

        while self._cur().type != TT_RBRACE:
            if self._at_eof():
                self._err('Unexpected EOF inside switch block')
            if self._cur().is_kw('cs'):
                self._eat()
                val  = self._parse_expr()
                body = self._parse_block()
                cases.append((val, body))
            elif self._cur().is_kw('def'):
                self._eat()
                default_body = self._parse_block()
            else:
                self._err('Expected cs or def inside switch block, got {!r}'.format(
                    self._cur().value))

        self._expect(TT_RBRACE)
        return SwitchNode(expr, cases, default_body)

    def _parse_try(self):
        self._eat()  # try
        try_body = self._parse_block()
        self._expect_kw('catch')

        # Multi-type catch:  catch TypeError, ValueError { }
        exc_types = []
        if self._cur().type == TT_IDENT:
            exc_types.append(self._eat().value)
            while self._cur().type == TT_COMMA:
                self._eat()
                exc_types.append(self._expect(TT_IDENT).value)
        catch_body = self._parse_block()

        # Optional finally:  fin { }
        finally_body = None
        if self._cur().is_kw('fin'):
            self._eat()
            finally_body = self._parse_block()

        return TryCatchNode(try_body, catch_body, exc_types, finally_body)

    def _parse_read_file(self):
        self._eat()  # rd
        return ReadFileNode(self._parse_expr())

    def _parse_write_file(self):
        self._eat()  # wr
        path    = self._parse_expr()
        content = self._parse_expr()
        return WriteFileNode(path, content)

    def _parse_expr_stmt(self):
        """
        Assignment, augmented assignment, increment/decrement, or expression.
        """
        expr = self._parse_expr()

        # Regular assignment
        if self._cur().is_op('='):
            self._eat()
            rhs = self._parse_expr()
            return AssignNode(expr, rhs)

        # Augmented assignment:  +=  -=  *=  /=  %=  **=
        if self._cur().type == TT_OP and self._cur().value in (
                '+=', '-=', '*=', '/=', '%=', '**='):
            op = self._eat().value
            rhs = self._parse_expr()
            return AugAssignNode(expr, op, rhs)

        return ExprStmtNode(expr)

    # ─── block parser ─────────────────────────────────────────────────────────

    def _parse_block(self):
        """Parse { stmt* }  →  [stmt, ...]"""
        self._expect(TT_LBRACE)
        stmts = []
        while self._cur().type != TT_RBRACE:
            if self._at_eof():
                self._err('Unexpected EOF — expected }')
            stmts.append(self._parse_stmt())
        self._expect(TT_RBRACE)
        return stmts

    # ─── parameter / argument lists ───────────────────────────────────────────

    def _parse_params(self):
        """
        Parse (p1, p2=default, ...args, ~~kwargs)
        Variadic params are stored with a * / ** prefix in the name string so
        _fmt_params() can emit them correctly without changing the tuple shape.
        """
        self._expect(TT_LPAREN)
        params = []
        while self._cur().type != TT_RPAREN:
            if self._cur().type == TT_OP and self._cur().value == '...':
                self._eat()   # ...
                name = '*' + self._expect(TT_IDENT).value
                params.append((name, None))
            elif self._cur().type == TT_OP and self._cur().value == '~~':
                self._eat()   # ~~
                name = '**' + self._expect(TT_IDENT).value
                params.append((name, None))
            else:
                name    = self._expect(TT_IDENT).value
                default = None
                if self._cur().is_op('='):
                    self._eat()
                    default = self._parse_expr()
                params.append((name, default))
            if self._cur().type == TT_COMMA:
                self._eat()
        self._expect(TT_RPAREN)
        return params

    def _parse_args(self):
        """Parse (arg1, name=val, ...spread, ...)  →  [expr|KwargNode|SpreadNode, ...]"""
        self._expect(TT_LPAREN)
        args = []
        while self._cur().type != TT_RPAREN:
            if self._cur().type == TT_OP and self._cur().value == '...':
                self._eat()   # spread
                args.append(SpreadNode(self._parse_expr()))
            else:
                arg = self._parse_expr()
                # Keyword argument:  name = value
                if isinstance(arg, IdentNode) and self._cur().is_op('='):
                    self._eat()   # =
                    args.append(KwargNode(arg.name, self._parse_expr()))
                else:
                    args.append(arg)
            if self._cur().type == TT_COMMA:
                self._eat()
        self._expect(TT_RPAREN)
        return args

    # ─── expression parser (Pratt / operator-precedence) ─────────────────────

    def _parse_expr(self, min_prec=0):
        left = self._parse_unary()

        while True:
            tok = self._cur()
            if tok.type != TT_OP or tok.value not in OP_PREC:
                break
            prec = OP_PREC[tok.value]
            if prec <= min_prec:
                break
            op = self._eat().value
            # ?? is right-associative (like most null-coalescing operators)
            # ** is right-associative
            rhs_min = prec - 1 if op in ('**', '??') else prec
            right   = self._parse_expr(rhs_min)
            if op == '??':
                left = NullCoalNode(left, right)
            else:
                left = BinOpNode(left, op, right)

        # Ternary:  cond ? then : else  — lowest precedence, only at top level
        if min_prec == 0 and self._cur().type == TT_OP and self._cur().value == '?':
            self._eat()   # ?
            then_expr = self._parse_expr()
            self._expect(TT_COLON)
            else_expr = self._parse_expr()
            return TernaryNode(left, then_expr, else_expr)

        return left

    def _parse_unary(self):
        tok = self._cur()

        if tok.is_op('!'):
            self._eat()
            return UnaryOpNode('not', self._parse_unary())

        if tok.is_op('-'):
            self._eat()
            return UnaryOpNode('-', self._parse_unary())

        return self._parse_postfix()

    def _parse_postfix(self):
        node = self._parse_primary()

        while True:
            tok = self._cur()

            if tok.is_op('++'):
                self._eat()
                node = IncrementNode(node)

            elif tok.is_op('--'):
                self._eat()
                node = DecrementNode(node)

            elif tok.type == TT_DOT:
                self._eat()
                attr_tok = self._cur()
                if attr_tok.type not in (TT_IDENT, TT_KEYWORD):
                    self._err('Expected attribute name after ".", got {!r}'.format(
                        attr_tok.value))
                attr = self._eat().value
                if self._cur().type == TT_LPAREN:
                    args = self._parse_args()
                    node = MethodCallNode(node, attr, args)
                else:
                    node = AttrNode(node, attr)

            elif tok.type == TT_LBRACKET:
                self._eat()   # [
                idx = self._parse_expr()
                # Slice:  obj[start..end]
                if self._cur().type == TT_RANGE:
                    self._eat()   # ..
                    end = self._parse_expr()
                    self._expect(TT_RBRACKET)
                    node = IndexNode(node, SliceNode(idx, end))
                else:
                    self._expect(TT_RBRACKET)
                    node = IndexNode(node, idx)

            elif tok.type == TT_LPAREN:
                args = self._parse_args()
                node = CallNode(node, args)

            else:
                break

        return node

    def _parse_primary(self):
        tok = self._cur()

        # ── numeric / string / boolean / null literals ────────────────────────
        if tok.type == TT_INT:
            self._eat(); return IntNode(tok.value)

        if tok.type == TT_FLOAT:
            self._eat(); return FloatNode(tok.value)

        if tok.type == TT_STRING:
            self._eat(); return StringNode(tok.value)

        if tok.is_kw('TRUE'):
            self._eat(); return BoolNode(True)

        if tok.is_kw('FALSE'):
            self._eat(); return BoolNode(False)

        if tok.is_kw('null'):
            self._eat(); return NullNode()

        # ── inp  →  input() ───────────────────────────────────────────────────
        if tok.is_kw('inp'):
            self._eat()
            return InputExprNode(self._parse_expr())

        # ── sup(args)  →  super().__init__(args) ─────────────────────────────
        if tok.is_kw('sup'):
            self._eat()
            return SuperCallNode(self._parse_args())

        # ── lam x, y -> expr  →  lambda ──────────────────────────────────────
        if tok.is_kw('lam'):
            return self._parse_lambda()

        # ── fn(params) { body }  →  anonymous function ───────────────────────
        if tok.is_kw('fn') and self._peek().type == TT_LPAREN:
            self._eat()   # fn
            params = self._parse_params()
            body   = self._parse_block()
            return AnonFnNode(params, body)

        # ── built-in algorithm names ──────────────────────────────────────────
        if tok.type == TT_KEYWORD and tok.value in STD_FUNCS:
            self._eat()
            if self._cur().type == TT_LPAREN:
                return CallNode(IdentNode(tok.value), self._parse_args())
            return IdentNode(tok.value)

        # ── regular identifier ────────────────────────────────────────────────
        if tok.type == TT_IDENT:
            self._eat()
            return IdentNode(tok.value)

        # ── parenthesised expression ──────────────────────────────────────────
        if tok.type == TT_LPAREN:
            self._eat()
            expr = self._parse_expr()
            self._expect(TT_RPAREN)
            return expr

        # ── array literal / comprehension ─────────────────────────────────────
        if tok.type == TT_LBRACKET:
            return self._parse_array_literal()

        # ── hashmap / dict literal ────────────────────────────────────────────
        if tok.type == TT_LBRACE:
            return self._parse_hashmap_literal()

        # ── spread  ...expr ───────────────────────────────────────────────────
        if tok.type == TT_OP and tok.value == '...':
            self._eat()
            return SpreadNode(self._parse_unary())

        self._err('Unexpected token in expression: {} {!r}'.format(
            tok.type, tok.value))

    # ─── lambda ───────────────────────────────────────────────────────────────

    def _parse_lambda(self):
        self._eat()   # lam
        params = []
        while not (self._cur().type == TT_OP and self._cur().value == '->'):
            if self._at_eof():
                self._err('Expected -> in lambda expression')
            if self._cur().type == TT_IDENT:
                params.append(self._eat().value)
            if self._cur().type == TT_COMMA:
                self._eat()
            elif not (self._cur().type == TT_OP and self._cur().value == '->'):
                self._err('Expected -> or , in lambda parameter list')
        self._expect_op('->')
        body_expr = self._parse_expr()
        return LambdaNode(params, body_expr)

    # ─── collection literals ──────────────────────────────────────────────────

    def _parse_array_literal(self):
        self._expect(TT_LBRACKET)

        # Empty array
        if self._cur().type == TT_RBRACKET:
            self._eat()
            return ArrayNode([])

        # First element (or comprehension expression)
        first = self._parse_first_array_elem()

        # Comprehension:  [expr for var in iterable (if cond)]
        if self._cur().is_kw('for'):
            self._eat()   # for
            var      = self._expect(TT_IDENT).value
            self._expect_kw('in')
            iterable = self._parse_expr()
            cond     = None
            if self._cur().is_kw('if'):
                self._eat()
                cond = self._parse_expr()
            self._expect(TT_RBRACKET)
            return ComprehensionNode(first, var, iterable, cond)

        # Regular array
        elems = [first]
        while self._cur().type == TT_COMMA:
            self._eat()
            if self._cur().type == TT_RBRACKET:
                break   # trailing comma
            elems.append(self._parse_first_array_elem())
        self._expect(TT_RBRACKET)
        return ArrayNode(elems)

    def _parse_first_array_elem(self):
        """Parse one array element, handling the ...spread prefix."""
        if self._cur().type == TT_OP and self._cur().value == '...':
            self._eat()
            return SpreadNode(self._parse_expr())
        return self._parse_expr()

    def _parse_hashmap_literal(self):
        self._expect(TT_LBRACE)
        pairs = []
        while self._cur().type != TT_RBRACE:
            key_tok = self._cur()
            if key_tok.type == TT_IDENT:
                key = StringNode(key_tok.value); self._eat()
            elif key_tok.type == TT_STRING:
                key = StringNode(key_tok.value); self._eat()
            elif key_tok.type == TT_INT:
                key = IntNode(key_tok.value); self._eat()
            else:
                self._err('Expected hashmap key, got {!r}'.format(key_tok.value))
            self._expect(TT_COLON)
            val = self._parse_expr()
            pairs.append((key, val))
            if self._cur().type == TT_COMMA:
                self._eat()
        self._expect(TT_RBRACE)
        return HashmapNode(pairs)
