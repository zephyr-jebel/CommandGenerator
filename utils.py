# written by Sunan Zou in Feb 2021

import stack
import copy


class Node:
    def __init__(self, name, isconst, input, type=-1, depth=0, group=0):
        self.name = name
        self.isConst = isconst
        self.input = input  # an edge object
        self.output = []  # list of names
        self.type = type
        self._depth = depth
        self._group = group

    def add_output(self, output):
        self.output.append(output)

    def get_input(self):
        return [self.input.node1, self.input.node2]

    def set_depth(self, depth):
        if self._depth < depth:
            self._depth = depth
            return True
        else:
            return False

    def get_depth(self):
        return self._depth

    def __eq__(self, other):
        return self.name == other.name


class Edge:
    def __init__(self, function, node1=None, node2=None):
        self.node1 = node1  # node name
        self.node2 = node2
        self.function = function  # refer to the function described in blif file


class Graph:
    def __init__(self, node_num=0, input_check=None, nodes=None, I=None, O=None, M=None, annotation=None, model=None):
        self.node_num = node_num  # ignore input nodes
        self.input_check = copy.deepcopy([]) if input_check is None else copy.deepcopy(input_check)
        self.nodes = copy.deepcopy({}) if nodes is None else copy.deepcopy(
            nodes)  # containing nodes dictionary, <name, obj>
        self.I = copy.deepcopy([]) if I is None else copy.deepcopy(I)
        self.O = copy.deepcopy([]) if O is None else copy.deepcopy(O)
        self.M = copy.deepcopy([]) if M is None else copy.deepcopy(M)
        self.annotation = str() if annotation is None else copy.deepcopy(annotation)
        self.model = str() if model is None else copy.deepcopy(model)
        self.aig_num = [0 for i in
                        range(14)]  # 00 1; 00 0; 01 1; 01 0; 10 1; 10 0; 11 1; 11 0; 0 1; 0 0; 1 1; 1 0; 1; 0
        self.depth_out = [0 for i in range(3)]  # depth of outputs max; min; average
        self.aig_out = [0 for i in range(12)]
        self.aig_dic = {'00 1': 0, '00 0': 1, '01 1': 2, '01 0': 3, '10 1': 4, '10 0': 5, '11 1': 6, '11 0': 7,
                        '0 1': 8, '0 0': 9, '1 1': 10, '1 0': 11, ' 1': 12, ' 0': 13}

    def add_node(self, name, is_const, edge):
        if self.get(name) is None:  # line[2] has existed in node dictionary
            self.nodes[name] = Node(name, is_const, edge)
            self.input_check.append(1 if name in self.I else 0)
            self.node_num += 1
        else:
            self.get(name).input = edge
            self.input_check[(self.find(name))] = 1 if name in self.I else 0
        if edge is not None:
            aig = edge.function.split("\n")[1]
            self.get(name).type = self.aig_dic[aig]
            self.aig_num[self.aig_dic[aig]] += 1

    def is_io(self, name):
        for n in self.I:
            if n == name:
                return True
        for n in self.O:
            if n == name:
                return True
        return False

    def finish(self):
        judge = 0
        for i in range(self.node_num):
            judge += self.input_check[i]
        return judge == self.node_num

    def find(self, name):  # return location of a Node in nodes list
        i = 0
        for node in self.nodes.keys():
            if name == node:
                return i
            i += 1
        return -1

    def get(self, name):  # return an Node obj by its name
        return self.nodes.get(name, None)

    def output(self, file):
        fp = open(file, 'w')
        fp.write(self.annotation)
        fp.write(self.model)
        fp.write(".inputs")
        for i in range(len(self.I)):
            fp.write(' ' + self.I[i])
            if i % 10 == 0 and i != 0 and i != len(self.I) - 1:
                fp.write(' \\' + '\n')
        fp.write("\n.outputs")
        for i in range(len(self.O)):
            fp.write(' ' + self.O[i])
            if i % 10 == 0 and i != 0 and i != len(self.O) - 1:
                fp.write(' \\' + '\n')
        fp.write('\n')
        for name in self.nodes.keys():
            if self.nodes[name].input is not None:
                fp.write(self.nodes[name].input.function)
        fp.write('.end\n')
        fp.close()


# read the graph and return the number of nodes;
def parser(filename, G):
    try:
        file = open(filename, 'r')
        lines = file.readlines()
        len_ = len(lines)
    except OSError:
        print("file input failed")
        assert False
    for i in range(len_):
        if lines[i][0] == '#':
            G.annotation += lines[i]
        elif lines[i].find(".model") != -1:
            G.model += lines[i]
        elif lines[i].find(".inputs") != -1:
            while True:
                flag = True  # judge whether input line hs ended
                for n in lines[i].split():
                    if n == ".inputs":
                        continue
                    elif n == "\\":
                        i += 1
                        flag = False
                        continue
                    else:
                        G.I.append(n)
                if flag:
                    break
        elif lines[i].find(".outputs") != -1:
            while True:
                flag = True  # judge whether input line hs ended
                for n in lines[i].split():
                    if n == ".outputs":
                        continue
                    elif n == "\\":
                        i += 1
                        flag = False
                        continue
                    else:
                        G.O.append(n)
                if flag:
                    break
        elif lines[i].find(".names") != -1:
            line = lines[i].split()
            i += 1
            if len(line) == 2:  # assuming each const node only appear once
                G.add_node(line[1], True, Edge(lines[i - 1] + lines[i]))
            elif len(line) == 3:  # 1 input 1 output
                if G.is_io(line[2]) is False:
                    G.M.append(line[2])
                G.add_node(line[2], False, Edge(lines[i - 1] + lines[i], line[1]))
                if G.get(line[1]) is None:  # line[1] is not in node list now
                    G.add_node(line[1], False, None)
                G.get(line[1]).add_output(line[2])
            elif len(line) == 4:  # 2 input 1 output
                if G.is_io(line[3]) is False:
                    G.M.append(line[3])
                G.add_node(line[3], False, Edge(lines[i - 1] + lines[i], line[1], line[2]))
                if G.get(line[1]) is None:  # line[1] is not in node list now
                    G.add_node(line[1], False, None)
                G.get(line[1]).add_output(line[3])
                if G.get(line[2]) is None:  # line[2] is not in node list now
                    G.add_node(line[2], False, None)
                G.get(line[2]).add_output(line[3])
        elif lines[i].find('.end') != -1:
            break
        i += 1
    file.close()
    return G.nodeNum


# calculate output depth feature of a graph
def get_depth(G):
    output_nodes = G.O
    total = 0
    o_max = -1
    o_min = 0x7FFFFFFF
    for node in output_nodes:
        depth = G.nodes[node].get_depth()
        total += depth
        if o_max < depth:
            o_max = depth
        if o_min > depth:
            o_min = depth
    G.depth_out[0] = o_max
    G.depth_out[1] = o_min
    G.depth_out[2] = total // len(G.O)


# calculate depth, and number of outputs of a certain aig in a graph
def cal_dgo(G):
    out_trans = [[0 for i in range(14)] for j in range(14)]
    check = []

    def cal_out(node_in):
        if node_in.type == -1 or node_in.name in check:
            return
        check.append(node_in.name)
        for node in node_in.output:
            node_out = G.nodes[node]
            if node_out.type == -1:
                continue
            out_trans[node_in.type][node_out.type] += 1
        G.aigout[node_in.type] += len(node_in.output)

    output_nodes = stack.Stack()
    for node in G.I:
        if node not in G.nodes.keys():
            continue
        output_nodes.push(node)
    while not output_nodes.is_empty():
        temp = G.nodes[output_nodes.pop()]
        cal_out(temp)
        depth = temp.getdepth() + 1
        for node in temp.output:
            if G.nodes[node].set_depth(depth):
                output_nodes.push(node)

    aig_num_sort = sorted(G.aignum, reverse=True)
    aig_num = copy.deepcopy(G.aignum)
    trans_list = []
    for i in range(4):
        loc = aig_num.index(aig_num_sort[i])
        aig_num[loc] = -1
        trans_list.append(loc)
    for i in range(4):
        if G.aigout[trans_list[i]] == 0:
            continue
        for j in range(4):
            G.trans[i * 4 + j] = out_trans[trans_list[i]][trans_list[j]] / G.aigout[trans_list[i]]
    for i in range(12):
        if G.aignum[i] != 0:
            G.aigout[i] = G.aigout[i] / G.aignum[i]
