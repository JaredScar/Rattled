import lexer
import rParser

def main():
    # JUST FOR TESTING: - TODO Get rid of
    lex = lexer.Lexer(open('../examples/printStatement.ry', 'r').read())
    lex.main()
    parser = rParser.Parser(lex.getTokens())
    parser.parse()
main()