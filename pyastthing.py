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
import copy
import uuid
# import elseScope
import varHandler

class Tree:
    def __init__(self):
        self.left = ""
        self.right = ""
        self.op = ""


class ClusterTree:
    def __init__(self):
        self.name = ""
        self.Parent = ""
        self.Child = ""
        self.Children = []
        self.siblings = []
        self.Module = ""
        self.cluster1 = ""
        self.currentLine = ""

    def createMap(self,  **kwargs):
        try:
            self.Parent = kwargs["Parent"]
            self.name = kwargs["name"]
            self.Module = kwargs["Module"]
            self.Child = kwargs["Child"]
        except KeyError:
            pass
        self.cluster1 = cluster1


cluster1 = ClusterTree()


class astParser:
    def __init__(self, file):
        myfile = file
        pyast = ast.parse(myfile)
        jsonTree = self.formatTree(pyast)
        tree = json.loads(jsonTree)
        body = tree['body']
        self.functions = []
        self.mainLoop(body)
        # print(self.dot)

    def vizdot(self):
        uniqueID = str(uuid.uuid1())
        self.dot.render(f'static/{uniqueID}', view=False)
        imgurl = "static/" + uniqueID+".webp"
        return imgurl

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

    def getImport(self, ct):
        self.getImportedFrom(ct)
        for line in ct.Module:
            if line["Type"] == "Import":
                value = line["names"][0]["name"]
                imported = self.chartImport(ct, value)
                ct.Child.subgraph(imported)
                ct.Child.edge("cluster_Module", f"{value} {ct.mask}", style="invis")

    def chartImport(self, ct, value):
        imported = Digraph(name=f'cluster {ct.mask} {value} import')
        imported.attr(label=f'Import', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="16", concentrate="true")
        imported.node(f"{value} {ct.mask}", f"{value}", shape="tab", color='lightseagreen', style="filled")
        return imported

    def getImportedFrom(self, ct):
        for line in ct.Module:
            if line["Type"] == "ImportFrom":
                value = line["names"][0]["name"]
                imported = self.chartImport(ct, value)
                ct.Child.edge("cluster_Module", f"{value} {ct.mask}", style="invis")
                ct.Child.subgraph(imported)
                links = line["module"].split(".")
                for count, i in enumerate(links):
                    firstLink = links[count]
                    try:
                        secondLink = links[count+1]
                        ct.Child.edge(firstLink, secondLink)
                    except Exception:
                        pass
                    finally:
                        ct.Child.node(firstLink, shape="tab", style='dotted')
                finalLink = links[-1]
                ct.Child.edge(finalLink, f"{value} {ct.mask}")

    def getLineMask(self, ct, line):
        if line["Type"] == "FunctionDef":
            ct.lineName = f"{line['name']} {line['Type']}"
            ct.mask = f"{line['name']}"
        else:
            ct.lineName = f"{line.name} {line['Type']}"
            ct.mask = f"{line.name} cluster"

    def chartFunction(self, ct):
        function = Digraph(name=f'cluster_{ct.lineName}')
        function.attr(label=f'{ct.mask}', fillcolor='lightsteelblue', style='filled, bold', fontcolor='black', fontsize="22")
        function.node(f"{ct.lineName} pointer", width="0", height="0", shape="point")
        exitNode = f"{ct.lineName} exit"
        function.node(exitNode, width="0", height="0", shape="point")
        return function

    def chartArguments(self, ct, line):
        input = self.chartInput(ct)
        args = line["args"]["args"]
        for arg in args:
            input.node(f"{ct.lineName} {arg['arg']}", f"{arg['arg']}", color='darksalmon', shape="note", style="filled")
            input.edge(f"{ct.lineName} {arg['arg']}", f"{ct.lineName} pointer", style="invis")
        return input

    def chartInput(self, ct):
        input = Digraph(name=f'cluster_{ct.mask}_args')
        input.node(ct.lineName, ct.mask, style="invis", color='lightcoral', shape="point", width="0", height="0")
        input.attr(label='Arguments / Input', style='filled, bold', fillcolor='white', fontsize="18", fontcolor='black')
        return input

    def createBoundary(self, ct):
        bounded = Digraph(name=f"cluster_{ct.lineName}_boundary", )
        bounded.attr(label='Function', style='filled, bold', fillcolor='lightslategray', fontsize="18", fontcolor='white')
        bounded.edge(ct.lineName, f"{ct.lineName} pointer", style="invis")
        bounded.node(f"{ct.mask} boundary exit", shape="point", width="0", height="0")
        bounded.edge(f"{ct.mask} boundary exit", f"{ct.mask} exit", minlen="0", style="invis")
        return bounded

    def mapFuncs(self, ct):
        self.getFuncs(ct)
        for line in ct.Module:
            if line["Type"] == "FunctionDef":
                self.functions.append(line["name"])
                self.getLineMask(ct, line)
                function = self.chartFunction(ct)
                arguments = self.chartArguments(ct, line)
                boundary = self.createBoundary(ct)
                newCT = copy.deepcopy(ct)
                newCT.Module = line["body"]
                newCT.Parent = boundary
                newCT.Child = function
                newCT.Pointer = f"{ct.lineName} pointer"
                newCT.Exit = f"{ct.lineName} exit"
                returnGraph = self.createReturnGraph(newCT, line)
                boundary.subgraph(returnGraph)
                self.createCluster(newCT)
                boundary.subgraph(function)
                boundary.subgraph(arguments)
                self.dot.subgraph(boundary)

    def createReturnGraph(self, ct, line):
        clusterName = f'cluster {ct.mask} return'
        returnGraph = Digraph(name=clusterName)
        returnGraph.attr(label=f'Return', fillcolor='cornflowerblue', style='filled, bold', fontcolor='black',
                         fontsize="16", concentrate="true")
        returnGraph.node(f"{ct.mask} exit", label=f"Exit", shape="point", color="cornflowerblue", style="filled, rounded", width="0", height="0")
        self.dot.edge(ct.Exit, f"{ct.mask} boundary exit", style="invis")
        lines = line.get("body")
        for item in lines:
            itemType = item.get("Type")
            if itemType == "Return":
                self.chartReturns(ct, returnGraph, item)
        return returnGraph

    def chartReturns(self, ct, returnGraph, item):
            value = item.get("value")
            valueType = value.get("Type")
            print(valueType)
            if valueType == "Name":
                name = self.getName(value)
                nodeValue = f"{name} {ct.mask} return"
                returnGraph.node(nodeValue, label=f"{name}", shape="rect", color="cornflowerblue", style="filled, rounded")
            if valueType == "Dict":
                node = self.getDict(value, ct)
                returnGraph.subgraph(node)


    def getDict(self, item, ct):
        clusterName = f'cluster {ct.mask} dict'
        dictionary = Digraph(name=clusterName)
        dictionary.attr(label=f'Dictionary', fillcolor='white', style='filled, bold', fontcolor='black',
                         fontsize="16", concentrate="true")
        dictionary.node(f"{ct.mask} dictionary", shape="point", width="0", height="0", style="invis")
        keys, values = self.getKeyValues(item)
        for key, value in zip(keys, values):
            keyValue = self.createKeyValue(ct, key, value)
            # dictionary.edge(f"{key} {ct.mask}", f"{value} {ct.mask}", constraint="false")
            dictionary.subgraph(keyValue)
            # dictionary.subgraph(dictKey)
        return dictionary

    def createKeyValue(self, ct, key, value):
        dictKey = self.chartKey(ct, key)
        dictValue = self.chartValue(ct, value)
        keyValueGraph = Digraph(name=f'cluster {ct.mask} {key}{value} keyValue')
        keyValueGraph.node(f"{ct.mask} {key}{value} keyvalue", shape="point", width="0", height="0", style="invis")
        keyValueGraph.attr(label='', fillcolor='white', style='filled, dashed', fontcolor='black', fontsize="16",
                 concentrate="true", color="black")
        keyValueGraph.subgraph(dictValue)
        keyValueGraph.subgraph(dictKey)
        return keyValueGraph

    def chartKey(self, ct, value):
        key = Digraph(name=f'cluster {ct.mask} {value} key')
        key.attr(label=f'Key', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="16", concentrate="true", color="dodgerblue")
        keyValue = f"{value} {ct.mask}"
        key.node(keyValue, f"{value}", shape="rect", color='plum', style="filled, rounded")
        self.dot.edge(f"{ct.mask} dictionary", keyValue, style="invis")
        return key

    def chartValue(self, ct, item):
        value = Digraph(name=f'cluster {ct.mask} {item} key')
        value.attr(label=f'Value', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="16", concentrate="true", color="indianred")
        keyValue = f"{item} {ct.mask}"
        value.node(keyValue, f"{item}", shape="rect", color='palevioletred', style="filled, rounded")
        self.dot.edge(f"{ct.mask} dictionary", keyValue, style="invis")
        return value

    def getKeyValues(self, item):
        keys = item.get("keys")
        values = item.get("values")
        keyList = []
        valueList = []
        for key, value in zip(keys, values):
            key = self.getItem(key)
            value = self.getItem(value)
            keyList.append(key)
            valueList.append(value)
        return keyList, valueList

    def getItem(self, item):
        type = item.get("Type")
        if type == "Constant":
            value = item.get("value")
        elif type == "Name":
            value = item.get("id")
        else:
            value = None
        return value
    def getName(self, line):
        return line["id"]

    def chartMemory(self, ct, target, value):
        if target not in self.functions:
            memory = Digraph(name=f'cluster {ct.mask} {target} memory')
            memory.attr(label=f'Memory', fillcolor='white', style='filled, dashed', fontcolor='black',
                        fontsize="16", concentrate="true", color="black")
            nodeValue = f"{target} {ct.mask}"
            memory.node(nodeValue, nodeValue, shape="cylinder", style="filled", color="slategray", fontcolor="white")
            return memory

    def chartPointer(self, ct, value):
        pointer = Digraph(name=f'cluster {ct.mask} {value} pointer')
        pointer.attr(label=f'Pointer', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="16", concentrate="true", color="black")
        pointerValue = f"{value} {ct.mask}"
        pointer.node(pointerValue, f"{value}", shape="tab", color='lightseagreen', style="filled")
        return pointer

    def chartAssignment(self, ct, target, value):
        assignment = Digraph(name=f'cluster {ct.mask} {target} {value} assignment')
        assignment.attr(label=f'Variable', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="16", concentrate="true", color="navyblue")
        assignmentPointer = f"{ct.mask}{target}{value} pointer"
        assignment.node(assignmentPointer, width="0", height="0", shape="point")
        return assignment

    def getCall(self, line):
        target = line["targets"][0]["id"]
        funcType = line["value"]["func"]["Type"]
        if funcType == "Name":
            value = f"{line['value']['func']['id']}"
        elif funcType == "Attribute":
            value = f"{line['value']['func']['attr']}"
        return value, target

    def getConstant(self, line):
        target = line["value"]["value"]
        value = line["targets"][0]["id"]
        return target, value

    def createCluster(self, ct):
        self.getImport(ct)
        # self.mapExpr(ct)
        self.mapFuncs(ct)
        varHandler.mapAssignments(self, ct)

    def mapExpr(self, ct):
        for count, line in enumerate(ct.Module):
            if line["Type"] == "Expr":
                try:
                    value = line["value"]["value"]
                    pointer = self.chartMemory(ct, value)
                    ct.Child.subgraph(pointer)
                except KeyError:
                    pass

    def getFuncs(self, ct):
        for line in ct.Module:
            if line["Type"] == "FunctionDef":
                self.functions.append(line["name"])

    def mainLoop(self, module):
        dot = Digraph(format="webp")
        dot.attr(concentrate="true", color="lightgrey", bgcolor="grey")
        self.dot = dot
        clusterName = f"cluster_Module"
        ct = cluster1
        c = Digraph(name='cluster1')
        self.dot.node(clusterName, shape="polygon", style='filled, invisible', fontcolor='white',
                      label=f'''Module''', color='black')
        ct.name = 'cluster1'
        ct.Module = module
        ct.Parent = self.dot
        ct.Child = self.dot
        ct.cluster1 = c
        ct.lineName = clusterName
        ct.mask = "cluster1"
        ct.Pointer = clusterName
        ct.Exit = clusterName
        self.createCluster(ct)
        self.dot.subgraph(ct.cluster1)