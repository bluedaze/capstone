

class buttClass():
    def __init__(self):
        self.thing = None
        butts = 10
        self.butts = 12

butts = buttClass()


callStack = []
reservedWords = ["def", 'class', "if", "elif", "else", "while", "try", "except", "for", "import"]
quotations = ["'", '"']
indentCallStack = {}

class ast(object):
    def __init__(self):
        self.scope = None
        self.root = None
ast = ast()
variables = []

class Token(object):
    def __init__(self, tokenType=None, name=None):
        self.variables = []
        self.type = tokenType
        self.name = name
        self.args = []
        self.members = []
        self.references = {}
        self.parent = None
        self.indent = None

    def __str__(self):
        return 'Token({type}, {value})'.format(type=self.type, value=repr(self.name))

    def __repr__(self):
        return self.__str__()

class Scanner(object):
    def __init__(self, text, file=None, count=None):
        self.usedwords = []
        self.file = file
        self.text = text
        self.pos = 0
        self.current_word = self.text[self.pos]
        self.text_length = len(self.text)
        self.token = None
        self.conditionals = ["if", "elif", "else", "while", "try", "except", "for"]
        self.reservedWords = ["def", "class", "import"]
        self.objects = ["def", "class"]
        self.closingBrackets = ["}", "]", ")"]
        self.brackets = ["{", "[", "("]
        self.quotations = ["'", '"']
        self.indents = [0]

    def checkIndentation(self):
        # Some of the dumbest code I've ever written.
        token = self.token
        if token.indent < ast.scope.indent:
            while ast.scope.indent > token.indent:
                ast.scope = ast.scope.parent
            token.parent = ast.scope.parent
            token.parent.members.append(token)
        elif token.indent > ast.scope.indent:
            token.parent = ast.scope
            ast.scope.members.append(token)
        elif token.indent == ast.scope.indent:
            ast.scope = ast.scope.parent
            token.parent = ast.scope
            ast.scope.members.append(token)
        ast.scope = token

    def createToken(self, tokenType=None, name=None):
        token = Token(tokenType, name)
        self.token = token
        self.getIndent()
        return token

    def getIndent(self):

        line = self.text[self.pos]
        if line.isspace():
            linelength = len(line)
            self.token.indent = len(line)
            self.advance()
        else:
            self.token.indent = 0
            ast.scope = ast.root
        self.checkIndentation()
        # linelength = len(line)
        # if self.pos > 0 and len(line) > 1:
        #     self.token.indent = len(line)
        # else:
        #     self.token.indent = 0
        # if self.token.indent == 0:
        #     ast.scope = ast.root

    def advance(self):
        self.pos += 1
        if self.pos < len(self.text):
            self.current_word = self.text[self.pos]
        self.usedwords.append(self.current_word)
        return self.current_word

    def peek(self):
        if self.pos < len(self.text) - 1:
            nextword = self.text[self.pos + 1]
            return nextword

    def dotAccessor(self):
        firstArg = ast.scope.parent.args[0]
        variableName = self.current_word
        parentType = ast.scope.parent.parent.type
        self.advance()
        if variableName == firstArg and parentType == "class":
            # This needs a rewrite
            current_scope = ast.scope
            Class = ast.scope.parent.parent
            ast.scope = Class
            self.advance()
            self.equalityOperator()
            Class.members.append(self.token)
            ast.scope = current_scope

    def equalityOperator(self):
        token = self.token
        variableName = self.current_word
        self.advance()
        peek = self.peek()
        if peek in self.brackets:
            self.advance()
            assignment = self.mapBrackets()
            token.type = "Assignment"
            token.name = variableName
            token.members.append(assignment)
            ast.scope.references[token.name] = token
            self.token = token
        elif peek == "None":
            self.advance()
            assignment = self.createTerminator("None")
            token.type = "Assignment"
            token.name = variableName
            token.members.append(assignment)
            ast.scope.references[token.name] = token
            self.token = token
        elif peek.isnumeric():
            self.advance()
            assignment = self.createTerminator("Math")
            token.type = "Assignment"
            token.name = variableName
            token.members.append(assignment)
            ast.scope.references[token.name] = token
            self.token = token
        elif peek in ast.scope.parent.references:
            self.advance()
            reference = self.fetchReference(self.current_word)
            ast.scope.references[variableName] = reference
            token.name = variableName
            token.type = "Assignment"
            token.members.append(reference)
            if self.peek() == "(":
                self.advance()
                brackets = self.mapBrackets()
                token.args = brackets

    def createTerminator(self, token_type):
        token = Token(token_type, self.current_word)
        self.advance()
        return token

    def fetchReference(self, variableName):
        for reference in ast.scope.parent.references:
            if variableName == reference:
                return ast.scope.parent.references[reference]

    def parse_token(self):
        self.createToken()
        current_word = self.current_word
        peek = self.peek()
        if self.current_word in self.reservedWords:
            self.createObjectToken()
        elif self.current_word in self.brackets:
            self.mapBrackets()
        elif peek == ".":
            self.dotAccessor()
        elif peek == "=":
            self.equalityOperator()
        elif self.current_word in self.conditionals:
            self.createExpressionToken()
        elif self.current_word[0] in self.closingBrackets:
            return self.current_word[0]
        else:
            self.advance()


    def createObjectToken(self):
        self.token.type = self.current_word
        self.token.name = self.advance()
        tokenName = self.token.name
        token = self.token
        while self.current_word != ":":
            self.advance()
            if self.peek() == "=":
                assignment = self.createTerminator("None")
                self.token.args.append(assignment)
                self.advance()
            elif self.current_word.isalnum():
                token.args.append(self.current_word)
        self.advance()
        ast.scope.parent.references[token.name] = token

    def createExpressionToken(self):
        self.advance()
        while self.pos < self.text_length - 1:
            self.advance()
            current_word = self.text[self.pos]
            if self.token:
                self.token.args.append(current_word)

    def mapBrackets(self):
        args = []
        while self.current_word not in self.closingBrackets:
            current_word = self.current_word
            if (self.current_word in self.brackets) and (self.advance() in self.closingBrackets):
                self.advance()
                return []
            elif self.current_word.isalnum() or self.current_word.startswith('"'):
                args.append(self.current_word)
            self.advance()
        self.advance()
        return args

    def loop(self):
        self.current_word = self.text[self.pos]
        self.usedwords.append(self.current_word)
        while self.pos < len(self.text):
            current_word = self.current_word
            peek = self.peek()
            self.parse_token()
            current_token = self.token
            self.advance()

class mainLoop:

    def __init__(self, filelocation):
        self.tokens = []
        self.main(filelocation)

    def peek(self):
        if self.pos + 1 >= len(self.file):
            return '\0'
        return self.file[self.pos+1]

    def lookback(self):
        return self.tokens[-1]

    def nextChar(self):
        self.pos += 1
        if self.pos < len(self.file):
            self.char = self.file[self.pos]

    def main(self, filelocation):
        self.loopThroughFile(filelocation)

    def loopThroughFile(self, filelocation):
        self.char = ""
        self.quotations = ["'", '"']
        self.pos = 0
        lines = open(filelocation, 'r')
        file = self.cleanFile(lines)
        self.file = file
        self.createTokens(file)

    def createToken(self):
        tokens = self.tokens
        brackets = ["[", "(", "{", "}", "]", ")"]
        if self.char == '#':
            self.skipComment()
        elif self.char == "_":
            self.dunders()
        elif self.char == "\n":
            tokens.append(self.char)
        elif self.char in self.quotations:
            self.createString()
        elif self.char.isalnum():
            self.createWord()
        elif self.char.isspace():
            self.spaceHandler()
        elif self.char == "=":
            self.equation()
        elif self.char in brackets:
            self.mapFuncCall()
        elif self.char == ":":
            self.tokens.append(self.char)
        elif self.char == ",":
            self.tokens.append(self.char)
        elif self.char == ".":
            self.tokens.append(self.char)

    def createTokens(self, file):
        self.char = self.file[self.pos]
        while self.pos < len(self.file):
            self.createToken()
            self.nextChar()

    def dunders(self):
        startPos = self.pos

        while True:
            self.nextChar()
            if self.char.isspace():
                break
            if self.char == "(":
                break

        dunder = self.file[startPos: self.pos]
        self.tokens.append(dunder)

    def mapFuncCall(self):
        brackets = {"[": "]", "(":")", "{": "}"}
        try:
            closing_bracket = brackets[self.char]
            self.tokens.append(self.char)
            while self.char != closing_bracket:
                # We recurse until the bracket closes
                # We remove any newline characters found in brackets
                self.nextChar()
                if self.char == "\n":
                    self.char = ""
                    self.tokens.append(self.char)
                elif self.char.isspace():
                    # Removing unnecessary indents after newline characters.
                    self.skipSpaces()
                self.createToken()
        except KeyError:
            # We append the closing bracket to the stack
            # Then we exit the function
            self.tokens.append(self.char)

    def skipSpaces(self):
        while self.peek().isspace():
            self.nextChar()

    def equation(self):
        self.tokens.append(self.char)
        return self.char

    def spaceHandler(self):
        spaces = []
        while self.char.isspace():
            spaces.append(self.char)
            if self.peek().isspace():
                self.nextChar()
            else:
                break
        space = "".join(spaces)
        spaceLength = len(space)
        if spaceLength > 1:
            self.tokens.append(space)
        return space

    def createWord(self):
        startPos = self.pos
        while self.peek().isalnum():
            self.nextChar()
            if self.peek() == "_":
                self.nextChar()

        tokenText = self.file[startPos : self.pos + 1]
        self.tokens.append(tokenText)
        return tokenText

    def skipComment(self):
        while self.char != '\n':
            self.nextChar()
        return self.char

    def createString(self):
        # I need to fix this nonsense
        tripleQuote = self.file[self.pos:self.pos+3]
        quoteChar = self.char
        self.nextChar()
        if tripleQuote == "'''":
            startPos = self.pos
            nextTree = self.file[self.pos:self.pos + 3]
            while nextTree != tripleQuote:
                nextTree = self.file[self.pos:self.pos+3]
                self.nextChar()
            string = self.file[startPos+2: self.pos-1]
            for i in range(2):
                self.nextChar()
        else:
            startPos = self.pos
            while self.char != quoteChar:
                self.nextChar()
            string = self.file[startPos-1: self.pos+1]
            string = string.replace("'", '"')
        self.tokens.append(string)

    def findFirstLine(self, lines):
        for i in lines:
            leadingSpaces = len(i) - len(i.lstrip())
            if leadingSpaces == 0:
                break
            elif leadingSpaces > 1:
                raise Exception("Program starts without proper indentation")

    def cleanFile(self, lines):
        source = []
        for line in lines:
            source.append(line)
        lines = self.stripNewline(source)
        self.findFirstLine(lines)
        source = "".join(lines)
        return source

    def stripNewline(self, linesToMap):
        symbols = [i for i in linesToMap if i != "\n"]
        return symbols


def createMain():
    mainToken = Token()
    mainToken.name = "__main__"
    mainToken.indent = 0
    mainToken.type = "__main__"
    mainToken.parent = mainToken
    ast.root = mainToken
    ast.scope = mainToken
    callStack.append(mainToken)

createMain()
fileObj = mainLoop("pyParser.py")
scanner = Scanner(fileObj.tokens, fileObj.file)
scanner.token = ast.scope
result = scanner.loop()