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
    def __init__(self, tokenType=None, value=None):
        self.type = tokenType
        self.name = value
        self.args = []
        self.members = []
        self.parent = None
        self.indent = None

    def __str__(self):
        return 'Token({type}, {value})'.format(type=self.type, value=repr(self.name))

    def __repr__(self):
        return self.__str__()


class Scanner(object):
    def __init__(self, text, file=None, count=None):
        self.count = count
        self.file = file
        self.text = text
        self.pos = 0
        self.current_word = self.text[self.pos]
        self.text_length = len(self.text)
        self.token = None
        self.reservedToken = ""
        self.conditionals = ["if", "elif", "else", "while", "try", "except", "for"]
        self.reservedWords = ["def", "class", "import"]
        self.objects = ["def", "class"]
        self.closingBrackets = ["}", "]"]
        self.brackets = ["{", "["]
        self.quotations = ["'", '"']

    def checkAssignmentOperator(self):
        token = self.token
        text = self.text
        eq = text.index("=")
        left = text[eq - 1]
        right = text[eq + 1]
        line = "".join(text)
        sides = line.split("=")
        x = 1

    def peek(self):
        if self.pos < len(self.text) - 1:
            nextword = self.text[self.pos + 1]
            return nextword

    def parse_token(self):
        if self.current_word[0] in self.quotations:
            self.createString()
        elif self.current_word in self.reservedWords:
            self.createObjectToken()
        elif self.current_word in self.brackets:
            self.mapBrackets()
        elif self.current_word == "=":
            self.checkAssignmentOperator()
        elif self.current_word in self.conditionals:
            self.createExpressionToken()
        elif self.current_word[0] in self.closingBrackets:
            return self.current_word[0]
        return self.token


    def createObjectToken(self):
        text = self.text
        self.peek()
        token = Token(self.current_word, self.peek())
        self.advance()
        peek = self.peek()
        if peek == '(':
            self.advance()
            while self.current_word != ":":
                self.advance()
                current_word = self.current_word
                if self.current_word == ",":
                    pass
                elif self.current_word == ")":
                    self.token = token
                elif self.current_word != ":":
                    token.args.append(self.current_word)
        else:
            self.token = token
        self.advance()

    def createString(self):
        current_word = self.current_word
        text = self.text
        if current_word[0] in self.quotations and current_word[-1] in self.quotations:
            x = 1
        string = "".join(text)
        splitString = string.split(",")
        string = []
        lastCharacter = self.current_word[-1]
        while lastCharacter not in self.quotations:
            string.append(self.current_word)
            self.advance()
        string.append(self.current_word)
        self.advance()
        string = " ".join(string)
        self.token = Token("string", string)

    def createExpressionToken(self):
        self.advance()
        while self.pos < self.text_length - 1:
            self.pos += 1
            current_word = self.text[self.pos]
            if self.token:
                self.token.args.append(current_word)

    def mapBrackets(self):
        current_token = self.current_word
        args = []
        self.token = Token("bracket", current_token)
        while self.current_word not in self.closingBrackets:
            text = self.text[self.pos + 1::]
            tokenizer = Scanner(text)
            token = tokenizer.parse_token()
            nextWord = self.peek()
            if (self.current_word in self.brackets) and (nextWord in self.closingBrackets):
                self.token = Token("bracket", "empty")
            elif token in self.closingBrackets:
                break
            elif token:
                args.append(token)
            self.pos += 1
            self.current_word = self.text[self.pos]
            self.token.args = args
        self.advance()
        x = 1

    def checkIndentation(self):
        # Some of the dumbest code I've ever written.
        token = self.token
        token.indent = self.getIndent(self.text)
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

    def getIndent(self, line):
        line = "".join(line)
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            ast.scope = ast.root
        return indent

    def advance(self):
        self.pos += 1
        if self.pos < len(self.text):
            self.current_word = self.text[self.pos]

    def expr(self):
        text = self.text
        while self.pos < len(self.text):
            self.current_word = self.text[self.pos]
            self.parse_token()
            if self.token:
                self.checkIndentation()
            self.advance()
        x = 1

class mainLoop:

    def __init__(self, filelocation):
        self.quotations = ["'", '"']
        self.tokens = []
        self.pos = 0
        self.createMain()
        self.main(filelocation)

    def createMain(self):
        self.mainToken = Token()
        self.mainToken.name = "__main__"
        self.mainToken.indent = 0
        self.mainToken.type = "__main__"
        self.mainToken.parent = self.mainToken
        ast.root = self.mainToken
        ast.scope = self.mainToken
        self.scope = self.mainToken
        self.char = ""
        callStack.append(self.mainToken)

    def peek(self):
        if self.pos + 1 >= len(self.file):
            return '\0'
        return self.file[self.pos+1]

    def lookback(self):
        return self.tokens[-1]

    def nextChar(self):
        self.pos += 1
        if self.pos >= len(self.file):
            self.char = '\0'
        else:
            self.char = self.file[self.pos]

    def main(self, filelocation):
        self.loopThroughFile(filelocation)

    def loopThroughFile(self, filelocation):
        lines = open(filelocation, 'r')
        file = self.cleanFile(lines)
        self.file = file
        tokens = self.tokenizeLine(file)
        for token in self.tokens:
            scanner = Scanner(tokens, file)
            scanner.expr()
        while True:
            x = 1

    def cleanFile(self, lines):
        lines = self.stripNewline(lines)
        self.findFirstLine(lines)
        source = "".join(lines)
        return source

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

    def tokenizeLine(self, file):
        self.char = self.file[self.pos]
        while self.pos < len(self.file):
            self.createToken()
            self.nextChar()
        x = 1

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
                self.nextChar()
                char = self.char
                if self.char == "\n":
                    self.char = ""
                    self.tokens.append(self.char)
                elif self.char.isspace():
                    self.skipSpaces()
                self.createToken()
        except KeyError:
            self.tokens.append(self.char)

    def skipSpaces(self):
        while self.peek().isspace():
            self.nextChar()

    def equation(self):
        self.tokens.append(self.char)
        return self.char

    def spaceHandler(self):
        spaces = []
        spaces.append(self.char)
        while self.peek().isspace():
            self.nextChar()
            spaces.append(self.char)
        space = " ".join(spaces)
        spaceLength = len(space)
        if spaceLength > 2:
            self.tokens.append(space)
        return space

    def createWord(self):
        startPos = self.pos
        while self.peek().isalnum():
            self.nextChar()
            if self.peek() == ".":
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

    def stripNewline(self, linesToMap):
        symbols = [i for i in linesToMap if i != "\n"]
        return symbols

fileObj = mainLoop("pyParser.py")
