#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from _ast import AST
import ast
import json
from graphviz import Digraph
import uuid


class tree():
    def __init__(self):
        self.left = ""
        self.right = ""
        self.op = ""

class astParser:
    def __init__(self, file):
        myfile = file
        pyast = ast.parse(myfile)
        jsonTree = self.formatTree(pyast)
        tree = json.loads(jsonTree)
        body = tree['body']
        self.functions = []
        self.mainLoop(body)

    def vizdot(self):
        uniqueID = str(uuid.uuid1())
        self.dot.render(f'static/{uniqueID}', view=False)
        imgur = "static/" + uniqueID+".webp"
        return imgur

    def iter_fields(self, node):

        for field in node._fields:
            try:
                yield field, getattr(node, field)
            except AttributeError:
                pass

    def formatTree(self, node):
        if isinstance(node, AST):
            fields = [('Type', self.formatTree(node.__class__.__name__))]
            fields += [(a, self.formatTree(b)) for a, b in self.iter_fields(node)]
            return '{ %s }' % ', '.join(('"%s": %s' % field for field in fields))

        if isinstance(node, list):
            return '[ %s ]' % ', '.join([self.formatTree(x) for x in node])

        return json.dumps(node)


    def getImport(self, clusterMap):
        cluster = clusterMap["Parent"]
        scopeName = clusterMap["name"]
        item = clusterMap["currentLine"]
        imported = item["names"][0]["name"]
        cluster.node(imported, imported, shape='tab', style='filled', color='lightseagreen')
        cluster.edge(f"{scopeName} Import", imported)

    def getImportedFrom(self, clusterMap):
        cluster = clusterMap["Parent"]
        scopeName = clusterMap["name"]
        item = clusterMap["currentLine"]
        importmodule = item["module"]
        imported = item["names"][0]["name"]
        links = item["module"].split(".")
        finalLink = links[-1]
        cluster.node(importmodule, links[0], shape="tab", style='dotted')
        cluster.node(imported, imported, shape="tab", style='filled', color='lightseagreen')
        cluster.edge(f"{scopeName} Import", imported)
        if len(links) > 1:
            links.pop(0)
            for link in links:
                cluster.node(link, link, shape="tab", style='dotted')
                cluster.edge(importmodule, link)
        cluster.edge(finalLink, imported)

    def createGraph(self, module, clusterMap, clusterName):
        self.findExpressions(module, clusterMap, clusterName)
        self.mapGraph(clusterMap)

    def createCondition(self, clusterMap):
        item = clusterMap["currentLine"]
        cluster = clusterMap["Parent"]
        scopeName = clusterMap["name"]
        if item["test"]["Type"] == "Compare":
            cluster.node(f"{scopeName} If", shape='rect', style='dotted',
                   label=f'''<<font POINT-SIZE="20">If</font>>''')
            parseTree = self.createParseTree(item)
            self.graphTree(clusterMap, parseTree)
            self.getElseCondition(clusterMap)

    def getElseCondition(self, clusterMap):
        item = clusterMap["currentLine"]
        cluster = clusterMap["Parent"]
        scopeName = clusterMap["name"]
        if item["orelse"][0]["Type"] == "Return":
            elseCondition = item["orelse"][0]["value"]["value"]
            cluster.node(f'{scopeName} {elseCondition}', shape='rect',
                         label=f'''{elseCondition}''', color='skyblue', style="filled, rounded")
            cluster.node(f"{scopeName} Else", shape='rect', style='dotted',
                         label=f'''<<font POINT-SIZE="20">Else</font>>''')
            cluster.edge(f"{scopeName} Else", f'{scopeName} {elseCondition}')

    def getOperator(self, item):
        itemType = item["test"]["comparators"][0]["Type"]
        if itemType == "Name":
            return item["test"]["comparators"][0]["id"]
        elif itemType == "Constant":
            return item["test"]["comparators"][0]["value"]

    def createParseTree(self, item):
        parseTree = tree()
        parseTree.left = item["test"]["left"]["id"]
        parseTree.op = item["test"]["ops"][0]["Type"]
        parseTree.right = self.getOperator(item)
        return parseTree

    def graphTree(self, clusterMap, parseTree):
        cluster = clusterMap["Parent"]
        scopeName = clusterMap["name"]
        cluster.node(f'{scopeName} {parseTree.op}', shape='doubleoctagon', label=f'''{parseTree.op}''', color='sandybrown', style="filled, rounded")
        cluster.node(f'{scopeName} {parseTree.left}', shape='rect', label=f'''{parseTree.left}''', color='wheat', style="filled, rounded")
        cluster.edge(f'{scopeName} If', f'{scopeName} Else')
        cluster.edge(f'{scopeName} If', f'{scopeName} {parseTree.op}')
        cluster.edge(f'{scopeName} {parseTree.op}', f'{scopeName} {parseTree.left}')
        cluster.node(f'{scopeName} {parseTree.right}', shape='rect', label=f'''{parseTree.right}''', color='wheat', style="filled, rounded")
        cluster.edge(f'{scopeName} {parseTree.op}', f'{scopeName} {parseTree.right}')

    def findExpressions(self, module, clusterMap, clusterName):
        module = clusterMap["Module"]
        cluster = clusterMap["Parent"]
        expressionTypes = []
        for object in module:
            lineType = object["Type"]
            if lineType == "FunctionDef":
                lineType = "Functions"
                self.functions.append(object['name'])
            if lineType == "Assign":
                lineType = "Assignments"
            if lineType == "ImportFrom":
                pass
            if lineType == "Return":
                pass
            elif lineType not in expressionTypes:
                expressionTypes.append(lineType)
                expressionName = f"{clusterName} {lineType}"
                cluster.node(expressionName, shape='rect', style='dotted',
                             label=f'''<<font POINT-SIZE="20">{lineType}</font>>''')
                cluster.edge(clusterName, expressionName)

    def mapGraph(self, clusterMap):
        for line in clusterMap["Module"]:
            clusterMap["currentLine"] = line
            if line["Type"] == "Import":
                self.getImport(clusterMap)
            elif line["Type"] == "ImportFrom":
                self.getImportedFrom(clusterMap)
            elif line["Type"] == "FunctionDef":
                self.mapFuncs(clusterMap)
            elif line["Type"] == "Assign":
                self.mapAssignments(clusterMap)
            elif line["Type"] == "If":
                self.createCondition(clusterMap)
            elif line["Type"] == "Expr":
                x = 1
            elif line["Type"] == "Return":
                self.mapReturns(clusterMap)

    def mapReturns(self, clusterMap):
        if clusterMap["currentLine"]["value"]["Type"] == "Name":
            target = clusterMap["currentLine"]["value"]["id"]
            returnObj = f"{clusterMap['name']} {target}"
            expressionName = f"{clusterMap['name']} {clusterMap['currentLine']['Type']}"
            with clusterMap["Child"].subgraph(name=f'cluster {expressionName}') as f:
                f.attr(style='dashed, filled', color='red')
                # f.node(f"{returnObj}", f"{returnObj} return", shape='tab', style='filled', color='red')
                f.node(expressionName, shape='square', style='dotted',
                             label=f'''<<font POINT-SIZE="15">Return</font>>''')
                f.node(f"{returnObj} returnobj", f"{target}", shape='square', style='dotted, filled, rounded', color="sandybrown")
                f.edge(expressionName, f"{returnObj} returnobj")
                clusterMap["Parent"].edge( f"{returnObj}", expressionName)

    def mapAssignments(self, clusterMap):
        line = clusterMap["currentLine"]
        clusterParent = clusterMap["Parent"]
        clusterChild = clusterMap["Child"]
        clusterName = clusterMap["name"]
        target = line["targets"][0]["id"]
        clusterParent.node(f"{clusterName} {target}", target, shape='tab', style='filled', color='lightseagreen')
        clusterParent.edge(f"{clusterName} Assignments", f"{clusterName} {target}")
        if line["value"]["Type"] == "Call":
            target = line["targets"][0]["id"]
            value = self.mapCall(line)
            if value:
                if value in self.functions:
                    clusterChild.edge(f"{clusterName} {target}", f"{value} FunctionDef")
                else:
                    clusterParent.node(f"{value} FunctionDef", value, shape='diamond', style='filled, rounded',
                           color='cornflowerblue')
                    clusterParent.edge(f"{clusterName} {target}", f"{value} FunctionDef")
        if line["value"]["Type"] == "Subscript":
            pass


    def mapCall(self, line):
        valueType = line["value"]["func"]["Type"]
        if valueType == "Name":
            value = line["value"]["func"]["id"]
            return value
        else:
            return None

    def mapFuncs(self, clusterMap):
        line = clusterMap["currentLine"]
        funcName = f"{line['name']} {line['Type']}"
        scopeName = clusterMap["name"]
        cluster = clusterMap["Parent"]
        with cluster.subgraph(name=f'cluster {line["name"]}') as f:
            newClusterMap = self.createCluster(f, clusterMap["Parent"], funcName, line["body"])
            f.attr(fillcolor='lightgrey', fontcolor='white', style='filled')
            f.node(f"{funcName}", f"{line['name']}", shape="component", style='filled', color='lightcoral')  # Defines what the nodes look like
            cluster.edge(f"{scopeName} Functions", f"{funcName}")
            self.createGraph(line["body"], newClusterMap, funcName)

    def createCluster(self, parent, child, name, module):
        newClusterMap = {}
        newClusterMap["Module"] = module
        newClusterMap["Parent"] = parent
        newClusterMap["Child"] = child
        newClusterMap["name"] = name
        return newClusterMap

    def mainLoop(self, module):
        dot = Digraph(format="webp")
        self.dot = dot
        clusterName = f"cluster_Module"
        self.dot.node(clusterName, shape="polygon",style='filled', fontcolor='white', label=f'''<<font POINT-SIZE="30">Module</font>>''', color='black')
        with self.dot.subgraph(name='cluster1') as c:
            clusterMap = {"Module": module, "name": clusterName, "Parent": c, "Child": c}
            self.createGraph(module, clusterMap, clusterName)