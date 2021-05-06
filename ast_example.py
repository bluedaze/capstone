from _ast import AST
import ast
import json


filename = "pyParser.py"
tree = ast.parse(open(filename).read())

def iter_fields(node):

    for field in node._fields:
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass

def formatTree(node):
    if isinstance(node, AST):
        fields = [('Type', formatTree(node.__class__.__name__))]
        fields += [(a, formatTree(b)) for a, b in iter_fields(node)]

        return '{ %s }' % ', '.join(('"%s": %s' % field for field in fields))

    if isinstance(node, list):
        return '[ %s ]' % ', '.join([formatTree(x) for x in node])

    return json.dumps(node)

jsonTree = formatTree(tree)
mytree = json.loads(jsonTree)
x = 1