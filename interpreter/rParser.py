class Parser(object):
    def __init__(self, tokens):
        # Tokens created by the Lexer
        self.tokens = tokens
        self.variables = list()
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
                        print() # TODO Get rid of
                        varDec = self.parse_variable(index)
                        print(varDec) # TODO Get rid of
                        self.variables.append(varDec)
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
        varName = ''
        varVal = list()
        while curInd < len(self.tokens):
            lineNo = self.tokens[curInd][0]
            token_type = self.tokens[curInd][1]
            token_val = self.tokens[curInd][2]
            if curInd == startInd:
                varName = token_val
            elif curInd == startInd + 2:
                # This is the first value of the variable
                if token_type in 'IDENTIFIER' or token_type in 'STRING' or token_type in 'NUMBER':
                    varVal.append([lineNo, token_type, token_val])
                else:
                    # ERROR, Invalid variable
            # This is next value of variable if it is an operator before it
            elif token_type in 'OPERATOR':
                if token_val not in '=':
                    varVal.append([lineNo, token_type, token_val])
                    nextVal = self.tokens[curInd + 1]
                    nextLine = nextVal[0]
                    nextType = nextVal[1]
                    nextVal = nextVal[2]
                    if nextType in 'IDENTIFIER' or nextType in 'STRING' or nextType in 'NUMBER':
                        varVal.append([nextLine, nextType, nextVal])
                    else:
                        # ERROR, Invalid variable
                    curInd += 1
            else:
                break
            curInd += 1
        return [varName, varVal]
    def parse_function(self, startInd):
        # This is to set up a parsed function for Rattled
        # TODO