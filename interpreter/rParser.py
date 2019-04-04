class Parser(object):
    def __init__(self, tokens):
        # Tokens created by the Lexer
        self.tokens = tokens
        self.variables = list()
        self.varTypes = list()
    def parse(self):
        index = 0
        for token in self.tokens:
            lineNo = token[0]
            token_type = token[1]
            token_val = token[2]

            # Parsing starts below:

            # This is an IDENTIFIER being set to some value if it has an = after it
            if 'IDENTIFIER' in token_type:
                if(len(self.tokens) > index + 1):
                    if self.tokens[index + 1][2] in '=':
                        self.parse_variable(index)
            if 'FUNCTION' in token_type:
                # TODO Parse function
                print()
            if 'KEYWORD' in token_type:
                # TODO
                print()
            if 'CAST' in token_type:
                # TODO
                print()

            index += 1
    def parse_variable(self, startInd):
        # This is to set up a variable defined
        curInd = startInd
        while curInd < len(self.tokens):
            lineNo = self.tokens[curInd][0]
            token_type = self.tokens[curInd][1]
            token_val = self.tokens[curInd][2]
            # TODO
            curInd += 1