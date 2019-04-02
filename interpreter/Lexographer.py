import re
class Lexer(object):
    def __init__(self, source_code):
        self.source_code = source_code
    def main(self):
        tokens = []

        sourceTokenized = self.source_code.split()
        stringTracked = False
        trackedString = ""
        trackedSymbol = ""
        for token in sourceTokenized:
            # This tokenizes the string part of source code
            if('"' in token or "'" in token or stringTracked == True):
                if not (token[0] in token[len(token) - 1] and (token[0] in "'" or token[0] in '"')):
                    if(stringTracked == True and trackedSymbol in token):
                        # This is where the string ends, since we already have been tracked a string
                        trackedSymbol = ""
                        stringTracked = False
                        trackedString += token[0:len(token) - 1]
                        tokens.append(['STRING', trackedString])
                        trackedString = ""
                    else:
                        # This is still part of a string, add it to trackedString
                        if(stringTracked == False):
                            trackedString += token[1:len(token)] + " "
                        else:
                            trackedString += token + " "
                        if('"' in token):
                            trackedSymbol = '"'
                        elif("'" in token):
                            trackedSymbol = "'"
                        print("Token is: " + token)
                        print("TrackedString is: " + trackedString)
                        print("TrackedSymbol is: " + trackedSymbol)
                        stringTracked = True
                else:
                    tokens.append(['STRING', token[1:len(token) - 1]])
            elif(token in "pr"):
                tokens.append(['FUNCTION', token])
            elif(token in "rd"):
                tokens.append(['FUNCTION', token])
            elif(token in "wr"):
                tokens.append(['FUNCTION', token])
            elif(re.match('[a-z]', token) or re.match('[A-Z]', token)):
                if(";" in token):
                    tokens.append(['IDENTIFIER', token[0:len(token) - 2]])
                else:
                    tokens.append(['IDENTIFIER', token])
            elif(re.match('[0-9]', token)):
                if (";" in token):
                    tokens.append(['INTEGER', token[0:len(token) - 1]])
                else:
                    tokens.append(['INTEGER', token])
            elif(token in "-+=/*%!"):
                tokens.append(['OPERATOR', token])

        print(tokens)
lex = Lexer(open('../examples/printStatement.ry', 'r').read())
lex.main()