import re
import constants


#
# Rattled Programming Language Lexer
#
# Lexing regex:
'''
variable declaration: 
pr function:
if statement: (if\(.*\)|if.\(.*\))                  Doesn't factor in that each open parenthesis has a closed one yet
if body: {([^}]+)}                                  Encounters problem when another } in String
'''
class Lexer(object):
    def __init__(self, source_code):
        self.source_code = source_code

    def main(self):
        tokens = []

        sourceTokenized = self.source_code

        stringTracked = False
        trackedString = ""
        trackedSymbol = ""
        for lineNo in range(len(sourceTokenized)):
            for token in str(sourceTokenized[lineNo]).split():
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
                            tokens.append([lineNo, 'STRING', trackedString])
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
                            tokens.append([lineNo, 'STRING', token[1:len(token) - 2]])
                        else:
                            tokens.append([lineNo, 'STRING', token[1:len(token) - 1]])
                # Is performing a function
                elif (token in constants.functions):
                    tokens.append([lineNo, 'FUNCTION', token])
                # Is calling for a cast
                elif (token in constants.casts):
                    tokens.append([lineNo, 'CAST', token])
                # Is calling a Rattled keyword
                elif (token in constants.keywords):
                    tokens.append([lineNo, 'KEYWORD', token])
                # Is creating a variable identifier
                elif (re.match('[a-z]', token) or re.match('[A-Z]', token)):
                    if (";" in token):
                        tokens.append([lineNo, 'IDENTIFIER', token[0:len(token) - 2]])
                    else:
                        tokens.append([lineNo, 'IDENTIFIER', token])
                # Is creating an Integer
                elif (re.match('[0-9]', token)):
                    if (";" in token):
                        tokens.append([lineNo, 'NUMBER', token[0:len(token) - 1]])
                    else:
                        tokens.append([lineNo, 'NUMBER', token])
                # Is trying to perform an operation
                elif (token in "-+=/*%!"):
                    tokens.append([lineNo, 'OPERATOR', token])
        print(str(tokens)) # TODO Get rid of debugger
        self.tokens = tokens
    def getTokens(self):
        return self.tokens
