import re
import copy
import spacy
from spacy.tokenizer import Tokenizer
nlp = spacy.load("en_core_web_lg")
variables = []
def custom_tokenizer():
    prefix_re = re.compile(r'''^[\[\(]''')
    suffix_re = re.compile(r'''[\]\)]''')
    infix_re = re.compile(r'''[\[\(]''')
    return Tokenizer(nlp.vocab,
                     prefix_search=prefix_re.search,
                     suffix_search=suffix_re.search,
                     infix_finditer=infix_re.finditer)

nlp.tokenizer = custom_tokenizer()
suffixes = nlp.Defaults.suffixes + [r''',''']
suffix_regex = spacy.util.compile_suffix_regex(suffixes)
nlp.tokenizer.suffix_search = suffix_regex.search
suffixes = list(nlp.Defaults.suffixes)
suffixes.remove(r'"')
suffix_regex = spacy.util.compile_suffix_regex(suffixes)
nlp.tokenizer.suffix_search = suffix_regex.search


class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.name = value
        self.args = []
        self.members = []
        self.parent = None

    def __str__(self):
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.name)
        )

    def __repr__(self):
        return self.__str__()


class Interpreter(object):
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_word = None
        self.tokens = []

    def error(self):
        raise Exception('Error parsing input')

    def get_next_token(self):
        vars = variables
        reserved_tokens = ["def", "class"]
        text = self.text
        if self.pos > len(text) - 1:
            pass

        current_word = text[self.pos]

        if current_word in reserved_tokens:
            self.createObjectToken()
        if current_word in variables:
            x = 1
        else:
            self.pos += 1


    def createObjectToken(self):
        text = self.text
        current_word = text[self.pos]
        '''Create class object with class as type, and next_word as the name'''
        next_word = text[self.pos+1]
        token = Token(current_word, next_word)
        '''advance two positions because the next word has been consumed'''''
        self.pos += 2
        current_word = text[self.pos]
        if current_word == '(':
            while current_word != ")":
                self.pos += 1
                current_word = text[self.pos]
                if current_word == ",":
                    pass
                elif current_word != ")":
                    token.args.append(current_word)
                elif current_word == ")":
                    self.tokens.append(token)
        elif current_word == ":":
            self.tokens.append(token)

    def expr(self):
        while self.pos < len(self.text) - 1:
            self.current_token = self.get_next_token()
        if self.tokens:
            return self.tokens[0]


class symbolTable:
    symbolTable = {}
    fileMapping = {}

    class ast:
        def __init__(self):
            pass
    def __init__(self, filelocation):
        self.priorIndent = 0
        self.indentationLevel = 0
        self.numIndents = 0
        self.newScope = {}
        self.mainToken = self.token()
        self.mainToken.name = "__main__"
        self.mainToken.indent = 0
        self.symbolTable[self.mainToken.name] = self.mainToken
        self.scope = ""
        self.scopedTo = "__main__"
        self.symbols = []
        self.keywords = ["class", "def"]
        self.reservedWords = ["import"]
        self.variables = []
        self.graph = []
        self.references = {}
        self.main(filelocation)
    def main(self, filelocation):
        self.linesToMap(filelocation)


    class token:
        def __init__(self):
            self.indent = None
            self.indentLevel = 0
            self.references = []
            self.symbolType = ""
            self.name = ""
            self.start = ""
            self.end = ""
            self.members = []
            self.indentLevel = ""
            self.expressions = ""
            self.parent = None
            self.parentType = None
            self.endPoints = ""
            self.scope = None
            self.scopedTo = ""

        def myRepr(self):
            if self.members is None:
                return f'\n(nameOfSybol: {self.name}, symbolType: {self.symbolType}, ' \
                       f'lineStarts: {self.start}, lineEnds: {self.start})'
            else:
                return f'\n(nameOfSybol: {self.name}, symbolType: {self.symbolType}, ' \
                       f'lineStarts: {self.start}, lineEnds: {self.end}) \n"members" {self.members}'
        def __str__(self):
            return f'{self.symbolType} {self.name}'
        def __repr__(self):
            return f"{self.myRepr()}"



    def linesToMap(self, filelocation):
        currentScope = self.mainToken
        self.indent = 0
        self.dedent = 0
        lines =  open(filelocation, 'r')
        lines = self.stripComments(lines, "#")
        lines = self.stripNewline(lines)
        self.findFirstLine(lines)
        file = []
        for sentence in lines:
            file.append(sentence)
            indentation = re.split(r'(\S+)', sentence)[0]
        self.file = file
        indentationTypes = ["INDENT", "DEDENT"]
        for count, line in enumerate(file):
            print(count)
            tokens = self.tokenizeLine(line, count)
            indents = [token for token in tokens if token in indentationTypes]
            if "DEDENT" in indents:
                for dedent in indents:
                    currentScope = currentScope.parent
            isKeyWord = self.isKeyWord(line)
            if isKeyWord:
                interpreter = Interpreter(tokens)
                newToken = interpreter.expr()
                currentScope.members.append(newToken)
                newToken.parent = currentScope
                currentScope = newToken
                self.symbolTable[newToken.name] = newToken
                variables.append(newToken.name)
            else:
                interpreter = Interpreter(tokens)
                vars = interpreter.expr()
            # currentIndent = indents[count]
            # if currentIndent == 0:
            #     priorIndent = currentIndent
            #     isKeyWord = self.isKeyWord(line)
            #     if isKeyWord:
            #         interpreter = Interpreter(tokens)
            #         newToken = interpreter.expr()
            #         self.mainToken.members.append(newToken)
            #         newToken.parent = self.mainToken
            #         newToken.indent = priorIndent
            #         currentScope = newToken
            #         self.symbolTable[newToken.name] = newToken
            #         self.variables.append(newToken.name)
            # elif currentIndent == currentScope.indent:
            #     priorIndent = currentIndent
            #     isKeyWord = self.isKeyWord(line)
            #     if isKeyWord:
            #         interpreter = Interpreter(tokens)
            #         newToken = interpreter.expr()
            #         currentScope = currentScope.parent
            #         currentScope.members.append(newToken)
            #         newToken.parent = currentScope
            #         newToken.indent = priorIndent
            #         currentScope = newToken
            #         self.symbolTable[newToken.name] = newToken
            #         self.variables.append(newToken.name)
            # elif currentIndent < currentScope.indent:
            #     priorIndent = currentIndent
            #     isKeyWord = self.isKeyWord(line)
            #     if isKeyWord:
            #         currentScope = currentScope.parent
            #         interpreter = Interpreter(tokens)
            #         newToken = interpreter.expr()
            #         newToken.parent = currentScope
            #         newToken.parent.members.append(newToken)
            #         newToken.indent = priorIndent
            #         currentScope = newToken
            #         self.symbolTable[newToken.name] = newToken
            #         self.variables.append(newToken.name)
            # elif currentIndent > currentScope.indent:
            #     priorIndent = currentIndent
            #     isKeyWord = self.isKeyWord(line)
            #     if isKeyWord:
            #         interpreter = Interpreter(tokens)
            #         newToken = interpreter.expr()
            #         newToken.parent = currentScope
            #         newToken.parent.members.append(newToken)
            #         newToken.indent = priorIndent
            #         currentScope = newToken
            #         self.symbolTable[newToken.name] = newToken
            #         self.variables.append(newToken.name)
            # elif currentIndent == currentScope.indent:
            #     isKeyWord = self.isKeyWord(line)
            #     if isKeyWord:
            #         interpreter = Interpreter(tokens)
            #         newToken = interpreter.expr()
            #         newToken.parent = currentScope
            #         newToken.parent.members.append(newToken)
            #         currentScope = newToken
            #         self.symbolTable[newToken.name] = newToken
            #         self.variables.append(newToken.name)


    def tokenizeLine(self, line, count):
        priorIndent = self.indent
        string = nlp(line)
        tokens = []
        for token in string:
            token = token.text
            if token.isspace():
                pass
            else:
                tokens.append(token)
        currentIndent = (len(line) - len(line.lstrip())) / 4
        if currentIndent > priorIndent:
            tokens.insert(0, "INDENT")
        elif currentIndent < priorIndent:
            dedents = int(abs(currentIndent - priorIndent))
            for dendent in range(dedents):
               tokens.insert(0, "DEDENT")
        elif currentIndent == 0:
            pass
        self.indent = currentIndent
        return tokens

    def isKeyWord(self, line):
        linetoCheck = "".join(line)
        keyword = None
        for i in self.keywords:
            keywordSearch = linetoCheck.find(i)
            if keywordSearch > -1:
                keyword = True
                break
            else:
                keyword = False
        return keyword

            # for token in tokens:
            #     if token in self.keywords:
            #         self.somethingSomething(tokens)
            # currentIndent = self.getIndent(line)
            # if currentIndent == indent:
            #     x = 1
            # else:
            #     x =1
            #     indent = self.getIndent(line)
            # words = line.split()
            # for count, word in enumerate(words):
            #     context = self.getContext(word)
            #     if context == "keyword":
            #         # token = self.findTokens(line, word, count)
            #         # if token:
            #         #     self.findDefintion(token, file)
            #         #     self.getScope(token, file)
            #         #     self.getMembers(token, file)
            #     elif context == "newline":
            #         break
            #     elif context == "variable":
            #         break
            #     elif context == "space":
            #         break
            #     elif context == "equalityOperator":
            #         partitionedString = self.partitionAssignment(line)
            #         self.checkReassignment(partitionedString)

    def startingScope(self, firstLine):
        newToken = self.token()
        doc = nlp(firstLine)
        firstWord = doc[0].text
        secondWord = doc[1].text
        if firstWord not in self.keywords:
            newToken.name = "__main__"
            return newToken
        else:
            newToken.name = secondWord
            return newToken

    def somethingSomething(self, words):
        for count, word in enumerate(words):
            if word in self.keywords:
                ast = self.ast()
                ast.name = words[count + 1]
                ast.type = word
                self.symbolTable.append((ast))
                break

    def getIndent(self, line):
        indent = len(line) - len(line.lstrip())
        return indent

    def partitionAssignment(self, words):
        words = words.strip().split()
        eqFound = False
        wordIndexes = []
        for word in words:
            if word == "=":
                eqFound = True
            elif eqFound == False:
                wordIndexes.append(word)
            elif eqFound == True:
                wordIndexes.append(word)
                break
        return (wordIndexes[0], wordIndexes[1])


    def checkReassignment(self, partitionedString):
        for i in partitionedString:
            x = i.find("(")
            if x > -1:
                i = i.partition("(")

    def getContext(self, nextWord):
        leftParen = nextWord.find("(")
        if leftParen > -1:
            splitWord = nextWord.split("(")[0]
            if splitWord in self.variables:
                return "variable"
        if nextWord in self.variables:
            return "variable"
        if nextWord in self.keywords:
            return "keyword"
        if nextWord.isspace():
            return "space"
        if nextWord == "\n":
            "newline"
        if nextWord == "=":
            return "equalityOperator"
        elif nextWord in self.keywords:
            return "keyword"


    def findDefintion(self, token, lines):
        endofFile = len(lines)
        releventLines = lines[token.start:endofFile]
        offset = token.start
        for count, line in enumerate(releventLines):
            leadingSpaces = len(line) - len(line.lstrip())
            isToken =  line.find(token.name)
            if isToken > -1:
                line = line.split()
                isMatch = [i for i in line if i == token.name]
                if len(isMatch) <= 0:
                    continue
                else:
                    token.end = count + offset
                    token.references.append(count + offset)
                    token.expressions = lines[token.start:count + offset]
                    break
            if leadingSpaces <= token.indentLevel:
                token.end = count + offset
                token.expressions = lines[token.start:count+offset]
                break

    def getScope(self, token, lines):
        originalLines = lines
        offset = token.end
        end = token.end
        lines = lines[end::]
        parent = token.parent
        parentScope = None
        if parent:
            parentScope = parent.indentLevel
        for count, line in enumerate(lines):
            leadingSpaces = len(line) - len(line.lstrip())
            if count < 1:
                continue
            foundToken = line.find(token.name)
            if foundToken > -1:
                line = line.split()
                isReassigned = self.checkForReassignment(line, token.name)
                if token.name in self.variables and not isReassigned:
                    linetoCheck = "".join(line)
                    isReference = linetoCheck.find("(")
                    if isReference > -1:
                        linetoCheck.strip("(")
                        newScope = count + end
                        token.references.append(newScope)
                if not isReassigned:
                    self.newScope[count + offset].append(token)
                    offset = count+offset
                    lines = originalLines[token.end+1:count+offset]
                    token.scope = lines
                    break
            if parentScope and leadingSpaces <= parentScope:
                self.newScope[count + offset].append(token)
                lines = originalLines[token.end + 1:count + offset]
            elif count == len(lines)-1:
                self.newScope[count + offset].append(token)
                lines = originalLines[token.end + 1:count+offset]
                token.scope = lines
                break
            self.newScope[count+offset].append(token)

    def checkForReassignment(self, line, name):
        reassignmentOperators = ["def", "class"]
        eqoperator = line.index("=") if "=" in line else None
        if eqoperator:
            peekLeft = line[eqoperator - 1]
            checkEquality = peekLeft.find(name)
            isReassigned = True if checkEquality > -1 else False
            if isReassigned:
                return isReassigned

        firstWord = line[0]
        isReassigned = True if firstWord in reassignmentOperators else False
        if isReassigned:
            return True
        else:
            return False

    def getMembers(self, Class, linesWithoutComments):
        keywords = ["def", "class"]
        members = []
        offset = Class.start
        for count, line in enumerate(Class.expressions):
            indentLevel = len(line) - len(line.lstrip())
            line = line.split()
            isMember = [word for word in line if word in keywords]
            if isMember:
                newToken = self.token()
                name = line[1].split("(")[0]
                newToken.name = name
                newToken.start = count + offset
                newToken.parent = Class
                newToken.parentType = Class.symbolType
                newToken.scopedTo = Class
                newToken.symbolType = isMember[0]
                newToken.indentLevel = indentLevel
                self.variables.append(newToken.name)
                self.findDefintion(newToken, linesWithoutComments)
                self.getScope(newToken, linesWithoutComments)
                members.append(newToken)
                Class.members.append(newToken)
        graph = f"{Class.name} --"
        lengthOfList = len(members) - 1
        for count, token in enumerate(members):
            if count < lengthOfList:
                graph = graph + token.name + " -- "
            else:
                graph = graph + token.name
        self.graph.append(graph)

    def findTokens(self, line, keyword, count):
        tokens = []
        # words = string.split()
        # for count, line in enumerate(words):
        foundToken = line.find(keyword)
        if foundToken > -1:
            indentLevel = len(line) - len(line.lstrip())
            line = line.split()
            secondWord = line[1]
            leftParen = secondWord.find("(")
            if leftParen > -1:
                secondWord = secondWord.split("(")[0]
            alpha = [letter for letter in secondWord if letter.isalnum() is True or letter == "_"]
            globalVariables = self.variables
            if secondWord not in globalVariables:
                newToken = self.token()
                tokenName = "".join(alpha)
                newToken.start = count
                newToken.name = tokenName
                self.variables.append(newToken.name)
                newToken.indentLevel = indentLevel
                newToken.symbolType = keyword
                tokens.append(newToken)
                self.symbolTable.append(newToken)
                self.scopedTo = newToken
                self.keywords.append(newToken.name)
                return newToken

    def findFirstLine(self, lines):
        for i in lines:
            leadingSpaces = len(i) - len(i.lstrip())
            if leadingSpaces == 0:
                break
            elif leadingSpaces > 1:
                raise Exception("Program starts without proper indentation")

    def stripComments(self, linesToMap, symbol):
        symbols = [i for i in linesToMap if symbol not in i]
        return symbols

    def stripNewline(self, linesToMap):
        symbols = [i for i in linesToMap if i != "\n"]
        return symbols




fileObj = symbolTable("bunchafuncs.py")