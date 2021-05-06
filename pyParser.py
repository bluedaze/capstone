callStack = []
reservedWords = ["def", 'class', "if", "elif", "else", "while", "try", "except", "for", "import"]
quotations = ["'", '"']
indentCallStack = {}

class ast(object):
    def __init__(self):
        self.scope = None
        self.scope = None
        self.root = None

ast = ast()
x = ast

class Token(object):
    def __init__(self, tokenType=None, name=None):
        self.variables = []
        self.type = tokenType
        self.name = name
        self.args = {}
        self.members = []
        self.references = {}
        self.parent = None
        self.indent = None
        self.returnValue = None

    def __str__(self):
        return 'Token({type}, {value})'.format(type=self.type, value=repr(self.name))

    def __repr__(self):
        return self.__str__()

class Scanner(object):
    def __init__(self, text, file=None, count=None):
        self.usedwords = []
        self.file = file
        self.text = text
        self.pax = 100 + 100
        self.pos = 0
        self.current_word = self.text[self.pos]
        self.text_length = len(self.text)
        self.token = None
        self.conditionals = ["if", "elif", "else", "while", "try", "except", "for"]
        self.reservedWords = ["def", "class"]
        self.objects = ["def", "class"]
        self.closingBrackets = ["}", "]", ")"]
        self.brackets = ["{", "[", "("]
        self.quotations = ["'", '"']
        self.indents = [0]

    def noneToken(self):
        token = Token()
        return token

    def referenceCall(self, reference):
        token = Token("$functionCall", reference.name)
        token.members.append(reference)
        return token

    def advance(self):
        self.pos += 1
        if self.pos < len(self.text):
            self.current_word = self.text[self.pos]
        self.usedwords.append(self.current_word)
        current_word = self.current_word
        print(self.current_word)
        return self.current_word

    def peek(self):
        if self.pos < len(self.text) - 1:
            nextword = self.text[self.pos + 1]
            return nextword

    def createNode(self, token, assignment, tokenName, tokenType):
        ast.scope.references[tokenName] = assignment
        token.name = tokenName
        token.type = tokenType
        ast.scope = token
        token.members = assignment
        self.token = token

    def dotAccessor(self, token, variable):
        astScope = ast.scope
        firstArg = astScope.references.get(variable)
        if firstArg.type == "class":
            variable = self.current_word
            Class = firstArg
            self.advance()
            arg = Class.references.get(variable)
            if arg is None and self.current_word == "=":
                self.advance()
                assignment = self.equalityOperator(token)
                token.type = "Assignment"
                token.name = variable
                ast.scope = ast.scope.parent
                ast.scope.references[variable] = assignment
                ast.scope = astScope
            elif arg:
                self.advance()
                assignment = self.equalityOperator(token)
                token.type = "Assignment"
                token.name = variable
                ast.scope = ast.scope.parent
                ast.scope.references[variable] = assignment
                ast.scope = astScope

    def removeMember(self, token):
        for member in ast.scope.members:
            if member.name == token.name:
                ast.scope.members.remove(member)
                break

    def doMath(self):
        while self.current_word.isnumeric():
            self.advance()

    def equalityOperator(self, token):
        if self.current_word in self.brackets:
            assignment = self.mapBrackets(token)
            self.advance()
            return assignment
        elif self.current_word == "None":
            self.advance()
            assignment = self.noneToken()
            return assignment
        elif self.current_word.isnumeric():
            assignment = self.doMath()
            token.type = "Assignment"
            token.name = variableName
            token.members.append(assignment)
            ast.scope.references[token.name] = token
            self.token = token
        elif self.current_word in ast.scope.references:
            variable = self.current_word
            reference = self.fetchMember(self.current_word)
            self.advance()
            if reference and self.current_word == "$functionCall":
                token.references[variable] = reference
                self.advance()
                return reference
            elif reference and self.current_word != "$functionCall":
                assignment = self.referenceCall(reference)
                token.references[variable] = reference
                token.members.append(assignment)
            elif self.peek() == "$functionCall":
                self.advance()
                return reference
            elif self.peek() == "\n":
                return "$functionCall"
            else:
                self.advance()
                return reference

    def createTerminator(self, token_type):
        assignment = Token(token_type, self.current_word)
        self.advance()
        return assignment

    def fetchMember(self, variableName):
        scope = ast.scope
        reference = ast.scope.references.get(variableName)
        while not reference and scope.name != "__main__":
            scope = scope.parent
            reference = ast.scope.references.get(variableName)
            if reference:
                return reference
        return reference


    def returnHandler(self, token):
        returnValue = []
        self.advance()
        while self.current_word != "\n":
            returnValue.append(self.current_word)
            self.advance()
        token.name = "Return"
        token.type = "Return"

    def createIdentifier(self, token):
        variableName = self.current_word
        self.advance()
        if self.current_word == "=":
            self.advance()
            assignment = self.equalityOperator(token)
            self.createNode(token, assignment, variableName, "Assignment")
        if self.current_word == ".":
            self.advance()
            self.dotAccessor(token, variableName)

    def parse_token(self, token):
        current_word = self.current_word
        peek = self.peek()
        if self.current_word in self.reservedWords:
            self.createScope(token)
        elif self.current_word == "return":
            self.returnHandler(token)
        elif self.current_word in self.brackets:
            self.mapBrackets(token)
        elif self.current_word.isalnum():
            self.createIdentifier(token)
        elif self.current_word in self.conditionals:
            self.createExpressionToken()
        else:
            self.advance()

    def createClass(self, token):
        if self.advance() == "(":
            while self.current_word != "\n":
                self.advance()
                if self.current_word == "object":
                    token.args[self.current_word] = token
                elif self.current_word.isalnum():
                    self.createArgument(token)

    def createArgument(self, token):
        variableName = self.current_word
        self.advance()
        if self.current_word == "=":
            self.advance()
            assignment = self.equalityOperator(token)
            token.references[variableName] = assignment
        else:
            token.references[variableName] = self.noneToken()

    def createScope(self, token):
        token.type = self.current_word
        token.name = self.advance()
        if token.type == "def":
            if self.advance() == "(":
                self.createFunction(token)
            else:
                raise Exception("Invalid syntax. You are missing a parenthesis.")
        elif token.type == "class":
            self.createClass(token)
        ast.scope.references[token.name] = token
        ast.scope = token

    def createFunction(self, token):
            self.advance()
            current_word = self.current_word
            peek = self.peek()
            x = 1
            while self.current_word != ":":
                if ast.scope.type == "class" and len(token.references) < 1:
                    token.references[self.current_word] = token.parent
                    self.advance()
                elif self.current_word.isalnum():
                    self.createArgument(token)
                if self.current_word == ")" or self.current_word == ",":
                    self.advance()
                else:
                    raise Exception("You are missing a comma.")
                if self.peek() == "\n" and self.current_word != ":":
                    raise Exception("A function declaration needs a colon at the end.")
            self.advance()

    def createExpressionToken(self):
        self.advance()
        while self.pos < self.text_length - 1:
            self.advance()
            current_word = self.text[self.pos]
            if self.token:
                self.token.args.append(current_word)

    def mapBrackets(self, token):
        args = []
        while self.current_word not in self.closingBrackets:
            if self.current_word.isalnum() or self.current_word.startswith('"'):
                args.append(self.current_word)
            self.advance()
        return args

    def loop(self):
        self.current_word = self.text[self.pos]
        self.usedwords.append(self.current_word)
        while self.pos < len(self.text):
            token = self.createToken()
            self.parse_token(token)
            if self.current_word == "\n":
                self.advance()
            else:
                raise Exception("The parser could not find a new line character.")

    def createToken(self, tokenType=None, name=None):
        token = Token(tokenType, name)
        self.getIndent(token)
        return token

    def getIndent(self, token):
        if self.current_word.isspace():
            self.createIndent(token)
        else:
            self.returnToRoot(token)
        self.checkIndentation(token)

    def createIndent(self, token):
        token.indent = len(self.current_word)
        self.advance()

    def returnToRoot(self, token):
        token.indent = 0
        ast.scope = ast.root

    def checkIndentation(self, token):
        if token.indent < ast.scope.indent:
            self.createDedent(token)
        elif token.indent > ast.scope.indent:
            token.parent = ast.scope
        elif token.indent == ast.scope.indent:
            ast.scope = ast.scope.parent
            token.parent = ast.scope
        return token

    def createDedent(self, token):
        while ast.scope.indent > token.indent:
            ast.scope = ast.scope.parent
        token.parent = ast.scope.parent

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
            if self.char.isspace():
                break
            if self.peek() == "(":
                break
            self.nextChar()

        dunder = self.file[startPos: self.pos+1]
        self.tokens.append(dunder)

    def mapFuncCall(self):
        brackets = {"[": "]", "(":")", "{": "}"}
        try:
            closing_bracket = brackets[self.char]
            if self.char == "(" and self.peek() == closing_bracket:
                previousWord = self.tokens[-1]
                if previousWord.isalnum():
                    self.nextChar()
                    self.tokens.append("$functionCall")
            else:
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

createMain()
fileObj = mainLoop("pyParser.py")
scanner = Scanner(fileObj.tokens, fileObj.file)
scanner.token = ast.scope
result = scanner.loop()
