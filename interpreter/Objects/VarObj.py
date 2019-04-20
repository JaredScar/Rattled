class Variable:
    def __init__(self):
        self.exec_string = ""
    def transpile(self, name, operator, body):
        # This creates a python executable for setting up a variable
        # Body needs to be looped through and added the values depending on their types
        bodyStr = ""
        for i in range(len(body[2])):
            tokenType = body[2][i][1]
            tokenVal = body[2][i][2]
            if(tokenType in 'STRING'):
                if("'" in tokenVal):
                    bodyStr += '"' + tokenVal + '"'
                else:
                    bodyStr += "'" + tokenVal + "'"
            else:
                bodyStr += tokenVal
        return name + " " + operator + " " + bodyStr + "\n"