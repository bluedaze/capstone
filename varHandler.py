from graphviz import Digraph

def mapAssignments(self, ct):
    for count, line in enumerate(ct.Module):
        if line["Type"] == "Assign":
            valueType = line["value"]["Type"]
            print(valueType)
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
            else:
                randomVariable(self, ct, line)

def constantVariable(self, ct, line):
    target, value = self.getConstant(line)
    pointer = self.chartPointer(ct, value)
    memory = chartMemory(self, ct, target, value)
    assignment = self.chartAssignment(ct, target, value)
    ct.Parent.edge(f"{value} {ct.mask}", f"{target} {value} {ct.mask}", style="invis")
    drawPointers(ct, target, value)
    subGraph(ct, assignment, memory, pointer)

def callVariable(self, ct, line):
    target, value = self.getCall(line)
    pointer = self.chartPointer(ct, value)
    memory = chartMemory(self, ct, target, value)
    assignment = self.chartAssignment(ct, target, value)
    drawPointers(ct, target, value)
    if memory:
        target = f"{target}"
        self.dot.edge(f"{value} {ct.mask}", f"{target} {value} {ct.mask}", style="invis")
    else:
        target = f"{target} FunctionDef"
        self.dot.edge(f"{value} {ct.mask}", f"{target}")
    subGraph(ct, assignment, memory, pointer)

def subGraph(ct, assignment, memory, pointer):
    assignment.subgraph(pointer)
    assignment.subgraph(memory)
    ct.Child.subgraph(assignment)

def dictionaryVariable(self, ct, line):
    target = line["targets"][0]["id"]
    pointer = self.chartPointer(ct, target)
    dictkeyvalue = line.get("value")
    value = self.getDict(dictkeyvalue, ct)
    assignment = Digraph(name=f'cluster {ct.mask} {target} dictionary')
    assignment.attr(label=f'Variable', fillcolor='white', style='filled, bold', fontcolor='black',
                    fontsize="16", concentrate="true")
    assignment.node(f"{ct.mask}{target} pointer", shape="point", width="0", height="0", style="invis",
                    color="navyblue")
    ct.Parent.edge(f"{ct.Pointer}", f"{ct.mask}{target} pointer", style="invis")
    ct.Parent.edge(f"{ct.mask}{target} pointer", f"{ct.Exit}", style="invis")
    ct.Parent.edge(f"{target} {ct.mask}", f"{ct.mask} dictionary", style="invis")
    assignment.subgraph(value)
    assignment.subgraph(pointer)
    ct.Child.subgraph(assignment)

def randomVariable(self, ct, line):
    value = line["targets"][0]["id"]
    target = ""
    pointer = self.chartPointer(ct, value)
    memory = chartMemory(self, ct, target, value)
    assignment = Digraph(name=f'cluster {ct.mask} {value} assignment')
    assignment.attr(label=f'Variable', fillcolor='white', style='filled, bold', fontcolor='black',
                    fontsize="16", concentrate="true", color="navyblue")
    assignment.node(f"{ct.mask}{value} pointer", width="0", height="0", shape="point")
    self.dot.edge(f"{value} {ct.mask}", f"{target} {value} {ct.mask}", style="invis")
    drawPointers(ct, target, value)
    subGraph(ct, assignment, memory, pointer)

def drawPointers(ct, target, value):
    ct.Parent.edge(f"{ct.mask}{target}{value} pointer", f"{ct.Exit}", style="invis")
    ct.Parent.edge(f"{ct.Pointer}", f"{ct.mask}{target}{value} pointer", style="invis")

def chartMemory(self, ct, target, value):
    if target not in self.functions:
        memory = Digraph(name=f'cluster {ct.mask} {target} memory')
        memory.attr(label=f'Memory', fillcolor='white', style='filled, dashed', fontcolor='black',
                    fontsize="16", concentrate="true", color="black")
        nodeValue = f"{target} {value} {ct.mask}"
        nodeMask = f"{target}"
        memory.node(nodeValue, nodeMask, shape="cylinder", style="filled", color="slategray", fontcolor="white")
        return memory