#
# Rattled Programming Language — Lexer
#
# Converts a .ry source string into a flat list of Token objects.
# Design notes:
#   - All whitespace (including newlines) is skipped — no significant indentation.
#   - Semicolons are silently discarded (they are optional statement terminators).
#   - Backtick-delimited strings are comments: `like this`.
#   - Hash (#) starts a line comment.
#   - Multi-char operators are tokenized greedily (++ before +, etc.).
#
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from constants import (
    TT_KEYWORD, TT_IDENT, TT_STRING, TT_INT, TT_FLOAT, TT_OP,
    TT_LPAREN, TT_RPAREN, TT_LBRACE, TT_RBRACE,
    TT_LBRACKET, TT_RBRACKET, TT_COMMA, TT_DOT, TT_COLON, TT_RANGE, TT_EOF,
    KEYWORDS,
)
from tok import Token


class LexError(Exception):
    pass


class Lexer:
    def __init__(self, source, filename='<input>'):
        self.src      = source
        self.filename = filename
        self.pos      = 0
        self.line     = 1

    # ─── private helpers ─────────────────────────────────────────────────────

    def _err(self, msg):
        raise LexError('[Rattled] {}:{}: {}'.format(self.filename, self.line, msg))

    def _ch(self, offset=0):
        p = self.pos + offset
        return self.src[p] if p < len(self.src) else None

    def _eat(self):
        c = self.src[self.pos]
        self.pos += 1
        return c

    # ─── public interface ────────────────────────────────────────────────────

    def tokenize(self):
        tokens = []

        while self.pos < len(self.src):
            c = self._ch()

            # ── whitespace (including newlines – Rattled ignores them) ──────
            if c in ' \t\r\n':
                if c == '\n':
                    self.line += 1
                self._eat()
                continue

            # ── hash comment: skip to end of line ───────────────────────────
            if c == '#':
                while self.pos < len(self.src) and self._ch() != '\n':
                    self._eat()
                continue

            # ── backtick comment: `...` ──────────────────────────────────────
            if c == '`':
                self._eat()
                while self.pos < len(self.src) and self._ch() != '`':
                    if self._ch() == '\n':
                        self.line += 1
                    self._eat()
                if self.pos >= len(self.src):
                    self._err('Unterminated comment (missing closing backtick)')
                self._eat()  # consume closing `
                continue

            # ── optional semicolons (statement terminators) ──────────────────
            if c == ';':
                self._eat()
                continue

            # ── string literals ──────────────────────────────────────────────
            if c in '"\'':
                tokens.append(self._read_string())
                continue

            # ── numeric literals ─────────────────────────────────────────────
            if c.isdigit():
                tokens.append(self._read_number())
                continue

            # ── identifiers and keywords ─────────────────────────────────────
            if c.isalpha() or c == '_':
                tokens.append(self._read_ident())
                continue

            # ── operators (greedy, multi-char first) ─────────────────────────
            if c in '+-*/%=!<>&|':
                tokens.append(self._read_op())
                continue

            # ── single-character punctuation (and .. range) ───────────────────
            if c == '.':
                # Check for range operator ..
                if self._ch(1) == '.':
                    tokens.append(Token(TT_RANGE, '..', self.line))
                    self._eat()   # first dot
                    self._eat()   # second dot
                else:
                    tokens.append(Token(TT_DOT, '.', self.line))
                    self._eat()
                continue

            punct = {
                '{': TT_LBRACE, '}': TT_RBRACE,
                '(': TT_LPAREN, ')': TT_RPAREN,
                '[': TT_LBRACKET, ']': TT_RBRACKET,
                ',': TT_COMMA, ':': TT_COLON,
            }
            if c in punct:
                tokens.append(Token(punct[c], c, self.line))
                self._eat()
                continue

            self._err("Unexpected character '{}'".format(c))

        tokens.append(Token(TT_EOF, None, self.line))
        return tokens

    # ─── sub-readers ─────────────────────────────────────────────────────────

    def _read_string(self):
        quote      = self._eat()
        start_line = self.line
        chars      = []
        esc_map    = {'n': '\n', 't': '\t', '\\': '\\', '"': '"', "'": "'"}

        while self.pos < len(self.src):
            c = self._eat()
            if c == quote:
                return Token(TT_STRING, ''.join(chars), start_line)
            if c == '\\':
                nxt = self._eat() if self.pos < len(self.src) else ''
                chars.append(esc_map.get(nxt, '\\' + nxt))
            elif c == '\n':
                self.line += 1
                chars.append('\n')
            else:
                chars.append(c)

        self._err('Unterminated string literal (opened on line {})'.format(start_line))

    def _read_number(self):
        start = self.pos
        line  = self.line

        while self.pos < len(self.src) and self._ch().isdigit():
            self._eat()

        # check for decimal point followed by more digits (float)
        if (self.pos < len(self.src)
                and self._ch() == '.'
                and self._ch(1) is not None
                and self._ch(1).isdigit()):
            self._eat()  # consume '.'
            while self.pos < len(self.src) and self._ch().isdigit():
                self._eat()
            return Token(TT_FLOAT, float(self.src[start:self.pos]), line)

        return Token(TT_INT, int(self.src[start:self.pos]), line)

    def _read_ident(self):
        start = self.pos
        line  = self.line

        while self.pos < len(self.src) and (self._ch().isalnum() or self._ch() == '_'):
            self._eat()

        word = self.src[start:self.pos]
        tt   = TT_KEYWORD if word in KEYWORDS else TT_IDENT
        return Token(tt, word, line)

    def _read_op(self):
        line = self.line
        c    = self._eat()
        n    = self._ch()

        # two-character operators (check greedily)
        two = c + (n or '')
        if two in ('++', '--', '**', '==', '!=', '<=', '>=', '&&', '||'):
            self._eat()
            return Token(TT_OP, two, line)

        # single-character operators
        if c in '+-*/%=!<>':
            return Token(TT_OP, c, line)

        self._err("Unknown operator character '{}'".format(c))
