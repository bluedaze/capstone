from graphviz import Digraph
from graphviz import Graph

def mapAssignments(self, ct):
    for line in ct.Module:
        if line["Type"] == "Assign":
            valueType = line["value"]["Type"]
            if valueType == "Constant":
                constantVariable(self, ct, line)
            elif valueType == "Call":
                callVariable(self, ct, line)
            elif valueType == "Dict":
                dictionaryVariable(self, ct, line)
            elif valueType == "Subscript":
                randomVariable(self, ct, line)
            elif valueType == "ListComp":
                randomVariable(self, ct, line)
            elif valueType == "BinOp":
                randomVariable(self, ct, line)
            elif valueType == "GhostNode":
                chartGhostNode(self, ct, line)
            elif valueType == "List":
                chartList(self, ct, line)
            else:
                randomVariable(self, ct, line)
        if line["Type"] == "Expr":
            chartExpr(self, ct, line)

def chartList(self, ct, line):
    value = line["targets"][0]["id"]
    target = ""
    pointer = chartPointer(self, ct, "list", value)
    nodeValue = f"{ct.mask} list {value} pointer"
    listChart = Graph(name=f'cluster {ct.mask} {value} variable')
    listChart.attr(label=f'List', fillcolor='white', style='filled', fontcolor='black',
              fontsize="14", concentrate="true", color="black")
    listValues = getListValues(self, ct, line["value"]["elts"])
    indexes = []
    memoryList = []
    count = len(listValues) - 1
    for item in range(len(listValues)-1,-1,-1):
        index = chartIndex(self, ct, item, str(count))
        indexes.append(index)
        x = listValues[count-1]
        memory = chartListMemory(ct, listValues[count], item)
        memoryList.append(memory)
        count = count - 1
    indexItem(indexes, memoryList, listChart)
    listChart.subgraph(pointer)
    ct.Child.subgraph(listChart)

def indexItem(indexes, memoryList, listChart):
    graphs = []
    for key, value in zip(indexes, memoryList):
        listGraph = Graph(name=f'cluster {key} {value} pointer')
        listGraph.attr(label=f'', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="14",
                     concentrate="true", color="black")
        listGraph.subgraph(value)
        listGraph.subgraph(key)
        listChart.subgraph(listGraph)

def chartIndex(self, ct, target, value):
    pointer = Graph(name=f'cluster {ct.mask} {value} pointer')
    pointer.attr(label=f'Index', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="14", concentrate="true", color="black")
    nodeValue = f"{ct.mask} {target} {value} pointer"
    nodeMask = f"{value}"
    pointer.node(nodeValue, nodeMask, shape="rarrow", color='skyblue', style="filled")
    return pointer

def chartListMemory(ct, target, value):
    memory = Graph(name=f'cluster {ct.mask} {target} memory')
    memory.attr(label=f'Item', fillcolor='white', style='filled, dashed', fontcolor='black',
                fontsize="14", concentrate="true", color="black")
    nodeValue = f"{ct.mask} {target}{value}"
    nodeMask = f"{target}"
    memory.node(nodeValue, nodeMask, shape="box3d", style="filled", color="indianred", fontcolor="white")
    if ct.mask != "cluster1":
        memory.edge(nodeValue, f"{ct.mask} exit", style="invis")
    return memory

def dictionaryVariable(self, ct, line):
    clusterName = f'cluster {ct.mask} dict'
    item = self.getItem(line["targets"][0])
    pointer = chartPointer(self, ct, "dictionary", item)
    nodeValue = f"{ct.mask} dictionary {item} pointer"
    dictionary = Graph(name=clusterName)
    dictionary.attr(label=f'Dictionary', fillcolor='white', style='filled, bold', fontcolor='black',
                    fontsize="16", concentrate="true")
    keys, values = getKeyValues(self, line["value"])
    for key, value in zip(keys, values):
        keyValue = createKeyValue(self, ct, key, value, nodeValue)
        dictionary.subgraph(keyValue)
    dictionary.subgraph(pointer)
    ct.Child.subgraph(dictionary)
    return dictionary

def getListValues(self, ct, line):
    listValues = []
    for item in line:
        itemValue = item.get("value")
        listValues.append(itemValue)
    return listValues

def chartExpr(self, ct, line):
    self.getItem(line["value"])
    try:
        value = line["value"]["value"]
        expr = Graph(name=f'cluster {ct.mask} {value} variable')
        expr.attr(label=f'Memory', fillcolor='white', style='filled, dashed', fontcolor='black',
                    fontsize="14", concentrate="true", color="black")
        nodeValue = f"{ct.mask} {value}"
        nodeMask = f"{value}"
        expr.node(nodeValue, nodeMask, shape="cylinder", style="filled", color="slategray", fontcolor="white")
        ct.Child.subgraph(expr)
        return expr
    except Exception:
        pass

def chartGhostNode(self, ct, line):
    value = line["targets"][0]["id"]
    target = ""
    assignment = chartGhostAssignment(ct, target, value)
    pointer = chartGhostPointer(self, ct, target, value)
    memory = chartGhostMemory(ct, target, value)
    linkPoints(self, ct, target, value)
    parentGraph = createParentGraph(assignment, memory, pointer)
    ct.Child.subgraph(parentGraph)

def constantVariable(self, ct, line):
    target, value = getConstant(line)
    chartVariable(self, ct, target, value)


def callVariable(self, ct, line):
    target, value = self.getCall(line)
    chartVariable(self, ct, target, value)

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

def createKeyValue(self, ct, key, value, nodeValue):
    dictKey = chartKey(self, ct, key, nodeValue)
    dictValue = chartValue(self, ct, value, nodeValue)
    keyValueGraph = Graph(name=f'cluster {ct.mask} {key}{value} keyValue')
    keyValueGraph.node(f"{ct.mask} {key}{value} keyvalue", width="0", height="0", shape="point", style="invis")
    keyValueGraph.attr(label='', fillcolor='white', style='filled, dashed', fontcolor='black', fontsize="16",
                       concentrate="true", color="black")
    keyValueGraph.subgraph(dictValue)
    keyValueGraph.subgraph(dictKey)
    return keyValueGraph


def chartKey(self, ct, value, nodeValue):
    key = Graph(name=f'cluster {ct.mask} {value} key')
    key.attr(label=f'Key', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="16",
             concentrate="true", color="dodgerblue")
    keyValue = f"{value} {ct.mask}"
    key.node(keyValue, f"{value}", shape="rect", color='plum', style="filled, rounded")
    self.dot.edge(nodeValue, keyValue, style="invis")
    return key


def chartValue(self, ct, item, nodeValue):
    value = Graph(name=f'cluster {ct.mask} {item} key')
    value.attr(label=f'Value', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="16",
               concentrate="true", color="indianred")
    keyValue = f"{item} {ct.mask}"
    value.node(keyValue, f"{item}", shape="rect", color='palevioletred', style="filled, rounded")
    self.dot.edge(nodeValue, keyValue, style="invis")
    self.dot.edge(keyValue, f"{ct.mask} exit", style="invis")
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

def randomVariable(self, ct, line):
    value = line["targets"][0]["id"]
    target = ""
    chartVariable(self, ct, target, value)

def drawPointers(ct, target, value):
    pass

def getConstant(line):
    target = line["value"]["value"]
    value = line["targets"][0]["id"]
    return target, value

def chartVariable(self, ct, target, value):
    assignment = chartAssignment(ct, target, value)
    pointer = chartPointer(self, ct, target, value)
    if target in self.functions:
        self.dot.edge(f"{ct.mask} {target} {value} pointer", f"{target} FunctionDef")
        parentGraph = createParentGraph(assignment, pointer)
    else:
        memory = chartMemory(ct, target, value)
        linkPoints(self, ct, target, value)
        parentGraph = createParentGraph(assignment, memory, pointer)
    ct.Child.subgraph(parentGraph)
    drawPointers(ct, target, value)

def linkPoints(self, ct, target, value):
    a = f"{ct.mask} {target} {value} pointer"
    b = f"{ct.mask} {target}{value}"
    self.dot.edge(a, b, style="invis")

def chartAssignment(ct, target, value):
    assignment = Graph(name=f'cluster {ct.mask} {target} {value} variable')
    assignment.attr(label=f'Variable', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="16", concentrate="true", color="navyblue")
    return assignment

def chartPointer(self, ct, target, value):
    pointer = Graph(name=f'cluster {ct.mask} {value} pointer')
    pointer.attr(label=f'Pointer', fillcolor='white', style='filled, bold', fontcolor='black', fontsize="14", concentrate="true", color="black")
    nodeValue = f"{ct.mask} {target} {value} pointer"
    nodeMask = f"{value}"
    pointer.node(nodeValue, nodeMask, shape="tab", color='lightseagreen', style="filled")
    self.dot.edge(ct.lineName, nodeValue, style="invis")
    return pointer

def chartMemory(ct, target, value):
    memory = Graph(name=f'cluster {ct.mask} {target} memory')
    memory.attr(label=f'Memory', fillcolor='white', style='filled, dashed', fontcolor='black',
                fontsize="14", concentrate="true", color="black")
    nodeValue = f"{ct.mask} {target}{value}"
    nodeMask = f"{target}"
    memory.node(nodeValue, nodeMask, shape="cylinder", style="filled", color="slategray", fontcolor="white")
    if ct.mask != "cluster1":
        memory.edge(nodeValue, f"{ct.mask} exit", style="invis")
    return memory

def chartGhostAssignment(ct, target, value):
    assignment = Graph(name=f'cluster {ct.mask} {target} {value} variable')
    assignment.attr(label='variable', fontsize="16", concentrate="true", style="invisible")
    return assignment

def chartGhostPointer(self, ct, target, value):
    pointer = Graph(name=f'cluster {ct.mask} {value} pointer')
    pointer.attr(label=f'pointer', fontsize="14", concentrate="true", style="invisible")
    nodeValue = f"{ct.mask} {target} {value} pointer"
    nodeMask = f"{value}"
    pointer.node(nodeValue, nodeMask, shape="tab", style="invis")
    self.dot.edge(ct.lineName, nodeValue, style="invis")
    return pointer

def chartGhostMemory(ct, target, value):
    memory = Graph(name=f'cluster {ct.mask} {target} memory')
    memory.attr(label=f'memory', fontsize="14", concentrate="true", style="invisible")
    nodeValue = f"{ct.mask} {target}{value}"
    nodeMask = f"{target}"
    memory.node(nodeValue, nodeMask, shape="cylinder", style="invis")
    memory.edge(nodeValue, f"{ct.mask} exit", style="invis")
    return memory

def createParentGraph(parentGraph, *args):
    for arg in args:
        parentGraph.subgraph(arg)
    return parentGraph