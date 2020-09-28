import re
import constants


#
# Rattled Programming Language Lexer
#
# Lexing regex:
class Lexer(object):
    def __init__(self, source_code):
        self.source_code = source_code

    def main(self):
        tokens = []

        sourceTokenized = self.source_code

        currentString = ""
        trackingString = False;
        stringPrefix = None;
        stringLineNo = None;
        trackingIdentifier = False;
        currentIdentifier = ""
        commentSkip = False;

        lineNo = 1;

        for line in sourceTokenized:
            # line represents each different line in the source code
            print("The line is: " + line);
            for v in line:
                # v represents each single character in the line
                if not commentSkip:
                    print("The value is: '" + v + "'")
                    if "'" in v or '"' in v:
                        # The start of a string
                        if trackingString and stringPrefix == v:
                            # A string is being tracked, close the string now
                            trackingString = False;
                            tokens.append([stringLineNo, currentString, 'STRING']);
                            currentString = "";
                            stringPrefix = None;
                            stringLineNo = None;
                        elif not trackingString:
                            # A string is now being tracked
                            trackingString = True;
                            stringPrefix = v;
                            stringLineNo = lineNo;
                    elif (re.match('[a-z]', v) or re.match('[A-Z]', v)):
                        if trackingString:
                            # It's a string, we add it to currentString
                            currentString += v;
                        else:
                            # It's not a string, should be part of an identifier
                            trackingIdentifier = True;
                            currentIdentifier += v;
                    elif (" " in v) or ('\n' in v):
                        # It's a space, if there is a currentIdentifier or currentString, submit them
                        if trackingString:
                            # A string was being tracked, add the space in there
                            currentString += v;
                        elif trackingIdentifier:
                            # A identifier was being tracked, now there is a space, submit it
                            tokens.append([lineNo, currentIdentifier, 'IDENTIFIER']);
                            currentIdentifier = "";
                            trackingIdentifier = False;
                    elif "#" in v:
                        # The start of a comment, skip line
                        commentSkip = True;
                    elif v in "+ - = / *":
                        # This is an operator
                        tokens.append([lineNo, v, 'OPERATOR']);
            lineNo += 1;
            commentSkip = False;
        print("Lexer Tokens: " + str(tokens))
        self.tokens = tokens;
    def getTokens(self):
        return self.tokens
