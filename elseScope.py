class tree():
    def __init__(self):
        self.left = ""
        self.right = ""
        self.op = ""

def getExpressionName(clusterMap):
    expressionName = f"{clusterMap['name']} {clusterMap['currentLine']['Type']}"
    return expressionName

def createCondition(self, clusterMap):
    expressionName = getExpressionName(clusterMap)
    item = clusterMap["currentLine"]
    parseTree = createParseTree(self, item)
    clusterName = parseTree.op + parseTree.left + parseTree.right
    with clusterMap["Parent"].subgraph(name=f'cluster if {clusterName}') as f:
        f.attr(fillcolor="aliceblue", color='brown2', label="Condition")
        parent, child, name, module = f, clusterMap["Parent"], expressionName, clusterMap["Module"]
        newClusterMap = self.createMap(parent, child, name, module)
        newClusterMap["currentLine"] = clusterMap["currentLine"]
        item = newClusterMap["currentLine"]
        cluster = newClusterMap["Parent"]
        if item["test"]["Type"] == "Compare":
            cluster.node(f"{newClusterMap['name']}", shape='rect', style='dotted',
                         label=f'''<<font POINT-SIZE="20">If</font>>''')
            parseTree = createParseTree(self, item)
            graphTree(self, newClusterMap, parseTree, f, clusterMap["name"])
        if item["test"]["Type"] == "Name":
            pass
        # cluster.node(f"{scopeName} If", shape='rect', style='dotted',
        #              label=f'''<<font POINT-SIZE="20">If</font>>''')
        # target = f"{scopeName} {item['test']['id']}"
        # parseTree = createParseTree(self, item)
        # graphTree(self, clusterMap, parseTree)
        # getElseCondition(self, clusterMap)
        
def createParseTree(self, item):
    parseTree = tree()
    if item["test"]["Type"] ==  "Compare":
        parseTree.left = item["test"]["left"]["id"]
        parseTree.op = item["test"]["ops"][0]["Type"]
        parseTree.right = getOperator(self, item)
    if item["test"]["Type"] == "Name":
        parseTree.op = item["test"]["id"]
        parseTree.left = item["body"][0]["Type"]
        # parseTree.right = getOperator(self, item)
    return parseTree

def getOperator(self, item):
    if item["test"]["Type"] == "Compare":
        itemType = item["test"]["comparators"][0]["Type"]
        if itemType == "Name":
            return item["test"]["comparators"][0]["id"]
        elif itemType == "Constant":
            return item["test"]["comparators"][0]["value"]
    elif item["test"]["Type"] == "Name":
        if item["orelse"][0]["Type"] == "Return":
            return item["orelse"][0]["value"]["id"]

def graphTree(self, clusterMap, parseTree, cluster, parentScope):
    clusterName = clusterMap["name"]
    ifScope = f'{clusterName}'
    cluster.node(f'{clusterName} {parseTree.op}', shape='doubleoctagon', label=f'''{parseTree.op}''', color='sandybrown', style="filled, rounded")
    cluster.edge(f'{clusterName}', f'{clusterName} {parseTree.op}')
    if parseTree.left:
        cluster.node(f'{clusterName} {parseTree.left}', shape='rect', label=f'''{parseTree.left}''', color='wheat', style="filled, rounded")
        cluster.edge(f'{clusterName} {parseTree.op}', f'{clusterName} {parseTree.left}')
    if parseTree.right:
        cluster.node(f'{clusterName} {parseTree.right}', shape='rect', label=f'''{parseTree.right}''', color='wheat', style="filled, rounded")
        cluster.edge(f'{clusterName} {parseTree.op}', f'{clusterName} {parseTree.right}')
    cluster.edge(f'{clusterName} {parseTree.right}', f'{clusterName} {parseTree.left}', constraint="false", dir="none", style="invis")
    clusterMap["Child"].edge(parentScope, clusterName, style="invis")
    getElseCondition(self, clusterMap)


def getElseCondition(self, clusterMap):
    item = clusterMap["currentLine"]
    cluster = clusterMap["Parent"]
    clusterName = clusterMap["name"]
    if item["orelse"]:
        if item["orelse"][0]["Type"] == "Return" or "Assign":
            elseType = item["orelse"][0]["value"]["Type"]
            if elseType == "Constant":
                elseType = item["orelse"][0]["Type"]
                if elseType == "Return":
                    clusterMap["currentLine"] = item["orelse"][0]
                    elseCondition = item["orelse"][0]["value"]["value"]
                    clusterMap["Child"].node(f'{clusterName} {elseCondition}', shape='rect', style='dotted',
                          label=f'''<<font POINT-SIZE="20">Else</font>>''')
                    cluster.edge(f'{clusterName}', f'{clusterName} {elseCondition}', constraint="false", dir="none",
                                 ordering="out")
                    self.mapReturns(clusterMap)
                elif elseType == "Assign":
                    cluster.node(f"{clusterName} Else", shape='rect', style='dotted',
                                 label=f'''<<font POINT-SIZE="20">Else</font>>''')
                    elseCondition = item["orelse"][0]["value"]["value"]
                    elseTarget = item["orelse"][0]["targets"][0]["id"]
                    cluster.node(f'{clusterName} {elseCondition}', shape='rect', label=f'''{elseCondition}''',
                                 color='skyblue', style="filled, rounded")
                    cluster.node(f'{clusterName} {elseTarget}', shape='rect', label=f'''{elseTarget}''',
                                 color='skyblue', style="filled, rounded")
                    cluster.edge(f'{clusterName} {elseTarget}', f'{clusterName} {elseCondition}')
                    cluster.edge(f"{clusterName} Else", f'{clusterName} {elseTarget}')
            if elseType == "Name":
                elseCondition = f"{clusterMap['name']} {item['orelse'][0]['value']['id']}"
                cluster.node(f'{elseCondition}', shape='rect', label=f'''{item['orelse'][0]['value']['id']}''', color='skyblue', style="filled, rounded")
                cluster.edge(f"{clusterName} Else", f'{elseCondition}')
        # if item["orelse"][0]["Type"] == "Assign":
        #     cluster.node(f"{clusterName} Else", shape='rect', style='dotted',
        #                  label=f'''<<font POINT-SIZE="20">Else</font>>''')
        #     cluster.edge(f'{clusterName} If', f'{clusterName} Else')
        #     elseType = item["orelse"][0]["value"]["Type"]
        #     if elseType == "Constant":
        #         elseCondition = item["orelse"][0]["value"]["value"]
        #         cluster.node(f'{clusterName} {elseCondition}', shape='rect', label=f'''{elseCondition}''', color='skyblue', style="filled, rounded")
        #         cluster.edge(f"{clusterName} Else", f'{clusterName} {elseCondition}')
        #     x = 1