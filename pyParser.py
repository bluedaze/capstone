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
        self.classScope = False
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
        if ast.scope.type == 'Assignment':
            ast.scope = ast.scope.parent
        x = 1

    def createToken(self, tokenType=None, name=None):
        token = Token(tokenType, name)
        self.token = token
        self.getIndent()
        return token

    def getIndent(self):
        line = self.text[self.pos-1]
        linelength = len(line)
        if self.pos > 0 and len(line) > 1:
            self.token.indent = len(line)
        else:
            self.token.indent = 0
        if self.token.indent == 0:
            ast.scope = ast.root

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

    def checkAssignmentOperator(self):
        self.advance()
        if self.current_word in self.brackets:
            return self.mapBrackets()
        elif self.peek() == "(":
            self.advance()
            return self.mapBrackets()
        else:
            return Token()

    def dotAccessor(self):
        firstArg = ast.scope.args[0]
        variableName = self.current_word
        token = self.createToken()
        parentType = ast.scope.parent.type
        if variableName == firstArg and parentType == "class":
            self.advance()
            Class = ast.scope.parent
            if self.current_word == ".":
                self.advance()
                self.equalityOperator(token)
                Class.members.append(self.token)
            self.advance()

    def equalityOperator(self, token):
        variableName = self.current_word
        self.advance()
        if self.peek() in self.brackets:
            self.advance()
            assignment = self.mapBrackets()
            token.type = "Assignment"
            token.name = variableName
            token.members.append(assignment)
            self.token = token
        elif self.peek() == "None":
            self.advance()
            token.type = "Assignment"
            token.name = variableName
        self.advance()

    def createIdentifiers(self):
        if self.peek() == "=":
            token = self.createToken()
            self.equalityOperator(token)
        if self.peek() == ".":
            self.dotAccessor()

    def parse_token(self):
        if self.current_word.isspace():
            self.advance()
        if self.current_word in self.reservedWords:
            self.createObjectToken()
        elif self.current_word in self.brackets:
            self.mapBrackets()
        elif self.current_word == "=":
            self.checkAssignmentOperator()
        elif self.current_word in self.conditionals:
            self.createExpressionToken()
        elif self.current_word[0] in self.closingBrackets:
            return self.current_word[0]
        elif self.current_word.isalnum():
            self.createIdentifiers()
        else:
            self.advance()


    def createObjectToken(self):
        token = self.createToken(self.current_word, self.peek())
        self.advance()
        self.token = token
        while self.current_word != "\n":
            self.advance()
            if self.current_word == ",":
                pass
            elif self.current_word == "(":
                pass
            elif self.current_word == "\n":
                pass
            elif self.current_word == ")":
                self.token = token
            elif self.current_word != ":":
                token.args.append(self.current_word)
        self.advance()

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
            nextWord = self.peek()
            if (self.current_word in self.brackets) and (nextWord in self.closingBrackets):
                token = self.createToken(self.current_word, nextWord)
                return token
            elif nextWord in self.closingBrackets:
                self.advance()
                break
            elif nextWord == ",":
                self.advance()
            else:
                self.advance()
                args.append(self.current_word)
        return args

    def expr(self):
        self.current_word = self.text[self.pos]
        self.usedwords.append(self.current_word)
        while self.pos < len(self.text):
            current_word = self.current_word
            self.parse_token()
            current_token = self.token
            self.checkIndentation()
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
result = scanner.expr()