import re
import spacy
from spacy.tokenizer import Tokenizer

nlp = spacy.load("en_core_web_lg")
callStack = []
reservedWords = ["def", "class", "if", "elif", "else", "while", "try", "except", "for", "import"]

def custom_tokenizer():
    custom_infixes = ['[\[\(]', '[.]']
    infix_re = spacy.util.compile_infix_regex(tuple(list(nlp.Defaults.infixes) + custom_infixes))
    prefix_re = re.compile(r'''^[\[\(]''')
    suffix_re = re.compile(r'''[\]\)]''')
    return Tokenizer(nlp.vocab, prefix_search=prefix_re.search, suffix_search=suffix_re.search, infix_finditer=infix_re.finditer)


nlp.tokenizer = custom_tokenizer()
suffixes = nlp.Defaults.suffixes + [r''',''']
suffix_regex = spacy.util.compile_suffix_regex(suffixes)
nlp.tokenizer.suffix_search = suffix_regex.search
suffixes = list(nlp.Defaults.suffixes)
suffixes.remove(r'"')
suffix_regex = spacy.util.compile_suffix_regex(suffixes)
nlp.tokenizer.suffix_search = suffix_regex.search

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
        self.reservedWords = ["def", "class", "if", "elif", "else", "while", "try", "except", "for", "import"]
        self.objects = ["def", "class"]
        self.closingBrackets = [")", "]"]
        self.brackets = ["(", "["]
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

    def advance(self):
        self.pos += 1
        if self.pos < len(self.text):
            self.current_word = self.text[self.pos]

    def peek(self):
        next_word = self.text[self.pos + 1]
        return next_word

    def parse_token(self):
        text = self.text
        if self.current_word in reservedWords:
            next_word = text[self.pos + 1]
            self.token = Token(self.current_word, next_word)
            variables.append(next_word)
            self.advance()
        if self.current_word[0] in self.quotations:
            self.createString()
        elif self.current_word in self.brackets:
            self.mapBrackets()
        elif self.current_word == "=":
            self.checkAssignmentOperator()
        elif self.current_word in self.conditionals:
            self.createExpressionToken()
        elif self.current_word in self.closingBrackets:
            self.token = Token(self.current_word)
            return self.token, self.pos
        return self.token, self.pos

    def createString(self):
        string = []
        while self.current_word[-1] not in self.quotations:
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
            self.token.args.append(current_word)

    def mapBrackets(self):
        current_token = self.current_word
        current_word = ""
        args = []
        while current_word not in self.closingBrackets:
            self.pos += 1
            text = self.text[self.pos::]
            tokenizer = Scanner(text)
            tokenizer.reservedToken = current_token
            token = tokenizer.parse_token()
            current_word = token[0].type
            newToken = token[0]
            if current_word not in self.closingBrackets:
                args.append(newToken)
            self.pos = token[1]
            self.token = newToken
        self.token = Token(current_token, "bracket")
        self.token.args = args

class Lexer(object):
    def __init__(self, text, file=None):
        self.file = file
        self.pos = 0
        self.text = text
        self.token = None

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
        if self.pos < len(self.text) - 1:
            self.current_word = self.text[self.pos]

    def expr(self):
        while self.pos < len(self.text):
            self.current_word = self.text[self.pos]
            tokenizer = Scanner(self.text)
            token = tokenizer.parse_token()
            if token[1] != self.pos:
                self.pos = token[1]
            self.token = token[0]
            if self.token:
                self.checkIndentation()
            self.advance()

class mainLoop:

    def __init__(self, filelocation):
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
        callStack.append(self.mainToken)

    def main(self, filelocation):
        self.loopThroughFile(filelocation)

    def loopThroughFile(self, filelocation):
        lines = open(filelocation, 'r')
        file = self.cleanFile(lines)
        self.file = file
        for count, line in enumerate(file):
            tokens = self.tokenizeLine(count, line)
            lexer = Lexer(tokens, file)
            lexer.expr()
        while True:
            x = 1

    def cleanFile(self, lines):
        lines = self.stripComments(lines, "#")
        lines = self.stripNewline(lines)
        strings = []
        for line in lines:
            line = self.stripNewlineCharacter(line)
            strings.append(line)
        self.findFirstLine(lines)
        file = []
        for sentence in strings:
            file.append(sentence)
        return strings

    def tokenizeLine(self, count, line):
        string = nlp(line)
        tokens = []
        for token in string:
            token = token.text
            tokens.append(token)
        return tokens

    def findFirstLine(self, lines):
        for i in lines:
            leadingSpaces = len(i) - len(i.lstrip())
            if leadingSpaces == 0:
                break
            elif leadingSpaces > 1:
                raise Exception("Program starts without proper indentation")

    def stripComments(self, linesToMap, symbol):
        lines = []
        for i in linesToMap:
            if symbol not in i:
                lines.append(i)
        # symbols = [i for i in linesToMap if symbol not in i]
        return lines

    def stripNewline(self, linesToMap):
        symbols = [i for i in linesToMap if i != "\n"]
        return symbols

    def stripNewlineCharacter(self, line):
        symbols = [i for i in line if i != "\n"]
        line = "".join(symbols)
        return line


fileObj = mainLoop("pyParser.py")
