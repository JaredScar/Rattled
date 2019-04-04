import re
import constants


#
# Rattled Programming Language Lexer
#
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
            if ('"' in token or "'" in token or stringTracked == True):
                # Make sure the string doesn't end on the first token:
                if not (token[0] in token[1:len(token)] and (token[0] in "'" or token[0] in '"')):
                    # We are currently interpreting a string, so we keep adding it to the trackedString
                    if (stringTracked == True and trackedSymbol in token):
                        # This is where the string ends, since we already have been tracked a string
                        trackedSymbol = ""
                        stringTracked = False
                        if (";" in token[len(token) - 1]):
                            trackedString += token[0:len(token) - 2]
                        else:
                            trackedString += token[0:len(token) - 1]
                        trackedString += " "
                        tokens.append(['STRING', trackedString])
                        trackedString = ""
                    else:
                        # This is still part of a string, add it to trackedString
                        if (stringTracked == False):
                            trackedString += token[1:len(token)] + " "
                        else:
                            trackedString += token + " "
                        if (len(trackedSymbol) == 0 and '"' in token):
                            trackedSymbol = '"'
                        elif (len(trackedSymbol) == 0 and "'" in token):
                            trackedSymbol = "'"
                        stringTracked = True
                else:
                    if ";" in token[len(token) - 1]:
                        tokens.append(['STRING', token[1:len(token) - 2]])
                    else:
                        tokens.append(['STRING', token[1:len(token) - 1]])
            # Is performing a function
            elif (token in constants.functions):
                tokens.append(['FUNCTION', token])
            # Is calling for a cast
            elif (token in constants.casts):
                tokens.append(['CAST', token])
            # Is calling a Rattled keyword
            elif (token in constants.keywords):
                tokens.append(['KEYWORD', token])
            # Is creating a variable identifier
            elif (re.match('[a-z]', token) or re.match('[A-Z]', token)):
                if (";" in token):
                    tokens.append(['IDENTIFIER', token[0:len(token) - 2]])
                else:
                    tokens.append(['IDENTIFIER', token])
            # Is creating an Integer
            elif (re.match('[0-9]', token)):
                if (";" in token):
                    tokens.append(['INTEGER', token[0:len(token) - 1]])
                else:
                    tokens.append(['INTEGER', token])
            # Is trying to perform an operation
            elif (token in "-+=/*%!"):
                tokens.append(['OPERATOR', token])
        #print(tokens)
        self.tokens = tokens
    def getTokens(self):
        return self.tokens
