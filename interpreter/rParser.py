class Parser(object):
    def __init__(self, tokens):
        # Tokens created by the Lexer
        self.tokens = tokens
        self.variables = list()
        self.varTypes = list()
    def parse(self):
        index = 0
        for token in self.tokens:
            token_type = token[0]
            token_val = token[1]

            # TODO Parsing starts below:
            #

            index += 1
    def parse_variable(self, startInd):
        # This is to set up a variable defined
        curInd = startInd
        while curInd < len(self.tokens):
            print()
            # TODO