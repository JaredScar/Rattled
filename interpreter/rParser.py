#
# Rattled Programming Language — Parser
#
# Recursive-descent / Pratt-operator-precedence parser.
# Consumes a flat token list produced by the Lexer and returns a ProgramNode AST.
#
# Statement boundary detection:
#   All whitespace (including newlines) was already discarded by the Lexer.
#   Statements are delimited implicitly: the expression parser stops when it
#   encounters a token that is not a binary operator, so each statement keyword
#   or identifier that follows naturally starts the next statement.
#
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from constants import (
    TT_KEYWORD, TT_IDENT, TT_STRING, TT_INT, TT_FLOAT, TT_OP,
    TT_LPAREN, TT_RPAREN, TT_LBRACE, TT_RBRACE,
    TT_LBRACKET, TT_RBRACKET, TT_COMMA, TT_DOT, TT_COLON, TT_EOF,
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

    # ─── public entry point ──────────────────────────────────────────────────

    def parse(self):
        stmts = []
        while not self._at_eof():
            stmts.append(self._parse_stmt())
        return ProgramNode(stmts)

    # ─── statement dispatch ───────────────────────────────────────────────────

    def _parse_stmt(self):
        tok = self._cur()

        if tok.is_kw('pr'):    return self._parse_print()
        if tok.is_kw('if'):    return self._parse_if()
        if tok.is_kw('for'):   return self._parse_for()
        if tok.is_kw('while'): return self._parse_while()
        if tok.is_kw('fn'):    return self._parse_fn()
        if tok.is_kw('Clas'):  return self._parse_class()
        if tok.is_kw('glo'):   return self._parse_global()
        if tok.is_kw('arr'):   return self._parse_arr_decl()
        if tok.is_kw('hashm'): return self._parse_hashm_decl()
        if tok.is_kw('imp'):   return self._parse_import()
        if tok.is_kw('ret'):   return self._parse_return()
        if tok.is_kw('sw'):    return self._parse_switch()
        if tok.is_kw('try'):   return self._parse_try()
        if tok.is_kw('rd'):    return self._parse_read_file()
        if tok.is_kw('wr'):    return self._parse_write_file()
        if tok.is_kw('fl'):
            self._eat()
            return FlushNode()

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

    def _parse_class(self):
        self._eat()  # Clas
        name = self._expect(TT_IDENT).value

        # optional parent: Clas Dog(Animal)
        parent = None
        if self._cur().type == TT_LPAREN:
            self._eat()
            parent = self._expect(TT_IDENT).value
            self._expect(TT_RPAREN)

        self._expect(TT_LBRACE)
        constructor = None
        methods     = []

        while self._cur().type != TT_RBRACE:
            if self._at_eof():
                self._err('Unexpected EOF inside class body')

            if self._cur().is_kw('def'):        # constructor
                self._eat()
                params = self._parse_params()
                body   = self._parse_block()
                constructor = ConstructorNode(params, body)

            elif self._cur().is_kw('fn'):       # method
                self._eat()
                mname  = self._expect(TT_IDENT).value
                params = self._parse_params()
                body   = self._parse_block()
                methods.append(MethodNode(mname, params, body))

            else:
                self._err('Expected def or fn in class body, got {!r}'.format(
                    self._cur().value))

        self._expect(TT_RBRACE)
        return ClassNode(name, parent, constructor, methods)

    def _parse_global(self):
        self._eat()  # glo
        name = self._expect(TT_IDENT).value
        if self._cur().is_op('='):
            self._eat()
            return GlobalAssignNode(name, self._parse_expr())
        return GlobalDeclNode(name)

    def _parse_arr_decl(self):
        self._eat()  # arr (just a readability hint — same as plain assignment)
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
        if tok.type not in (TT_IDENT, TT_KEYWORD):
            self._err('Expected module or symbol name after imp')
        name = self._eat().value

        # imp sqrt from math  →  from math import sqrt
        if self._cur().is_kw('from'):
            self._eat()
            module = self._expect(TT_IDENT).value
            return ImportNode(module=module, names=[name])

        # imp math  →  import math
        return ImportNode(module=name, names=[])

    def _parse_return(self):
        self._eat()  # ret
        # bare return when next token is } or EOF
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

            elif self._cur().is_kw('def'):      # default case
                self._eat()
                default_body = self._parse_block()

            else:
                self._err('Expected cs or def inside switch block, got {!r}'.format(
                    self._cur().value))

        self._expect(TT_RBRACE)
        return SwitchNode(expr, cases, default_body)

    def _parse_try(self):
        self._eat()  # try
        try_body   = self._parse_block()
        self._expect_kw('catch')
        catch_body = self._parse_block()
        return TryCatchNode(try_body, catch_body)

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
        Handles assignment, increment/decrement, and plain expression statements.
        After parsing the LHS expression, peek for '=' to decide if it's an assignment.
        """
        expr = self._parse_expr()

        if self._cur().is_op('='):
            self._eat()
            rhs = self._parse_expr()
            return AssignNode(expr, rhs)

        return ExprStmtNode(expr)

    # ─── block parser ─────────────────────────────────────────────────────────

    def _parse_block(self):
        """Parse { stmt* }  and return [stmt, ...]"""
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
        """Parse (p1, p2=default, ...)  →  [(name, default_or_None), ...]"""
        self._expect(TT_LPAREN)
        params = []
        while self._cur().type != TT_RPAREN:
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
        """Parse (arg1, arg2, ...)  →  [expr, ...]"""
        self._expect(TT_LPAREN)
        args = []
        while self._cur().type != TT_RPAREN:
            args.append(self._parse_expr())
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
            # ** is right-associative; all others are left-associative
            rhs_min = prec - 1 if op == '**' else prec
            right   = self._parse_expr(rhs_min)
            left    = BinOpNode(left, op, right)

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

            # Postfix increment / decrement
            if tok.is_op('++'):
                self._eat()
                node = IncrementNode(node)

            elif tok.is_op('--'):
                self._eat()
                node = DecrementNode(node)

            # Attribute access or method call:  obj.attr  /  obj.method(args)
            elif tok.type == TT_DOT:
                self._eat()  # .
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

            # Index access:  obj[index]
            elif tok.type == TT_LBRACKET:
                self._eat()  # [
                idx = self._parse_expr()
                self._expect(TT_RBRACKET)
                node = IndexNode(node, idx)

            # Function call:  callee(args)
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
            self._eat()
            return IntNode(tok.value)

        if tok.type == TT_FLOAT:
            self._eat()
            return FloatNode(tok.value)

        if tok.type == TT_STRING:
            self._eat()
            return StringNode(tok.value)

        if tok.is_kw('TRUE'):
            self._eat()
            return BoolNode(True)

        if tok.is_kw('FALSE'):
            self._eat()
            return BoolNode(False)

        if tok.is_kw('null'):
            self._eat()
            return NullNode()

        # ── inp prompt_expr  →  input(prompt_expr) ───────────────────────────
        if tok.is_kw('inp'):
            self._eat()
            return InputExprNode(self._parse_expr())

        # ── sup(args)  →  super().__init__(args) ─────────────────────────────
        if tok.is_kw('sup'):
            self._eat()
            return SuperCallNode(self._parse_args())

        # ── built-in algorithm names used as callable identifiers ─────────────
        if tok.type == TT_KEYWORD and tok.value in STD_FUNCS:
            self._eat()
            if self._cur().type == TT_LPAREN:
                return CallNode(IdentNode(tok.value), self._parse_args())
            return IdentNode(tok.value)

        # ── regular identifier (variable, function name, cast name, …) ────────
        if tok.type == TT_IDENT:
            self._eat()
            return IdentNode(tok.value)

        # ── parenthesised expression ──────────────────────────────────────────
        if tok.type == TT_LPAREN:
            self._eat()
            expr = self._parse_expr()
            self._expect(TT_RPAREN)
            return expr

        # ── array literal  [elem, ...] ────────────────────────────────────────
        if tok.type == TT_LBRACKET:
            return self._parse_array_literal()

        # ── hashmap / dict literal  {key: val, ...} ───────────────────────────
        if tok.type == TT_LBRACE:
            return self._parse_hashmap_literal()

        self._err('Unexpected token in expression: {} {!r}'.format(
            tok.type, tok.value))

    # ─── collection literals ──────────────────────────────────────────────────

    def _parse_array_literal(self):
        self._expect(TT_LBRACKET)
        elems = []
        while self._cur().type != TT_RBRACKET:
            elems.append(self._parse_expr())
            if self._cur().type == TT_COMMA:
                self._eat()
        self._expect(TT_RBRACKET)
        return ArrayNode(elems)

    def _parse_hashmap_literal(self):
        self._expect(TT_LBRACE)
        pairs = []
        while self._cur().type != TT_RBRACE:
            key_tok = self._cur()
            # bare identifier key → stored as string
            if key_tok.type == TT_IDENT:
                key = StringNode(key_tok.value)
                self._eat()
            elif key_tok.type == TT_STRING:
                key = StringNode(key_tok.value)
                self._eat()
            elif key_tok.type == TT_INT:
                key = IntNode(key_tok.value)
                self._eat()
            else:
                self._err('Expected hashmap key, got {!r}'.format(key_tok.value))
            self._expect(TT_COLON)
            val = self._parse_expr()
            pairs.append((key, val))
            if self._cur().type == TT_COMMA:
                self._eat()
        self._expect(TT_RBRACE)
        return HashmapNode(pairs)
