
class Parser(object):
    def __init__(self, tokens):
        # Tokens created by the Lexer
        self.tokens = tokens
        self.transpiled_code = ""
    def parse(self):
        # TODO REWRITE
        print("Python code to execute: ")
        print(self.transpiled_code)