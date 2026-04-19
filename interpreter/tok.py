#
# Rattled Programming Language — Token
#
from constants import TT_KEYWORD, TT_OP


class Token:
    __slots__ = ('type', 'value', 'line')

    def __init__(self, type_, value, line=0):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return 'Token({}, {!r}, ln={})'.format(self.type, self.value, self.line)

    def is_kw(self, keyword):
        return self.type == TT_KEYWORD and self.value == keyword

    def is_op(self, op):
        return self.type == TT_OP and self.value == op
