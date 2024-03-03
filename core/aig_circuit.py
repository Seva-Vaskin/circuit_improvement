from __future__ import annotations

import copy
import itertools
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Set
import networkx as nx

from core.circuit import Circuit
from binary_function import FunctionTransformation


def inv_perm(perm):
    res = [0] * len(perm)
    for i, v in enumerate(perm):
        res[v] = i
    return res


@dataclass
class AIGCircuit:
    allowed_functions = {"0001", "1110", "0111", "1000",
                         "0010", "0100", "1011", "1101"}
    out_negotiate_functions = {"0111", "1110", "1011", "1101"}  # OR NAND >= <=
    l_arg_negotiate_functions = {"0111", "1000", "0100", "1011"}  # OR NOR < >=
    r_arg_negotiate_functions = {"0111", "1000", "0010", "1101"}  # OR NOR > <=

    @dataclass
    class Edge:
        source: AIGCircuit.Gate
        dest: Optional[AIGCircuit.Gate] = None
        negotiation: bool = False

        def is_negotiation_edge(self):
            return self.negotiation ^ self.source.output_negotiation

    @dataclass
    class Gate:
        label: str
        outputs: List[AIGCircuit.Edge]
        l_input: Optional[AIGCircuit.Edge] = None
        r_input: Optional[AIGCircuit.Edge] = None
        output_negotiation: bool = False
        out_neg_label: Optional[str] = None
        val: Optional[bool] = None

        def __init__(self, label=''):
            self.label = label
            self.outputs = list()

        def __hash__(self):
            return hash(self.label)

    gates: Optional[List[Gate]] = None
    inputs: Optional[List[Gate]] = None
    outputs: Optional[List[Edge]] = None
    edges: Optional[List[Edge]] = None
    edge_labels: int = 0
    finalized: bool = False

    def __gen_out_negotiation_label(self):
        assert not self.finalized
        ans = str(len(self.gates) + self.edge_labels)
        self.edge_labels += 1
        return ans

    @staticmethod
    def from_circuit(circuit: Circuit) -> AIGCircuit:
        result = AIGCircuit()
        result.inputs = list()
        result.outputs = list()
        result.edges = list()

        labeled_gates = dict()

        for gate_label in list(circuit.gates.keys()):
            gate = AIGCircuit.Gate(gate_label)
            labeled_gates[gate_label] = (gate, False)

        for input_label in circuit.input_labels:
            gate = AIGCircuit.Gate(input_label)
            labeled_gates[input_label] = (gate, False)
            result.inputs.append(gate)

        for gate_label, (l_arg, r_arg, function) in circuit.gates.items():
            if function in ('1100', '1010'):  # function is not(x) or not(y)
                arg_label = l_arg if function == '1100' else r_arg
                arg_gate, arg_is_neg = labeled_gates[arg_label]
                # assert not arg_is_neg, "Doubled negotiation"
                labeled_gates[gate_label] = (arg_gate, not arg_is_neg)
            else:
                assert function in AIGCircuit.allowed_functions
                gate, is_neg = labeled_gates[gate_label]
                assert not is_neg
                l_arg_gate, l_is_neg = labeled_gates[l_arg]
                r_arg_gate, r_is_neg = labeled_gates[r_arg]

                l_edge = AIGCircuit.Edge(l_arg_gate, gate, l_is_neg)
                r_edge = AIGCircuit.Edge(r_arg_gate, gate, r_is_neg)
                result.edges.append(l_edge)
                result.edges.append(r_edge)

                gate.l_input = l_edge
                gate.r_input = r_edge
                l_arg_gate.outputs.append(l_edge)
                r_arg_gate.outputs.append(r_edge)

                if function in AIGCircuit.out_negotiate_functions:
                    gate.output_negotiation ^= True
                if function in AIGCircuit.l_arg_negotiate_functions:
                    l_edge.negotiation ^= True
                if function in AIGCircuit.r_arg_negotiate_functions:
                    r_edge.negotiation ^= True

        for output_label in circuit.outputs:
            out_gate, is_neg = labeled_gates[output_label]
            out_edge = AIGCircuit.Edge(out_gate, None, is_neg)
            result.edges.append(out_edge)
            result.outputs.append(out_edge)

        result.gates = list(map(lambda x: x[0], filter(lambda x: not x[1], set(labeled_gates.values()))))

        all_truth_tables = circuit.get_truth_tables()
        out_truth_tables = [all_truth_tables[i] for i in circuit.outputs]
        assert result.get_truth_tables() == out_truth_tables, f"Got:\n\t{result.get_truth_tables()}\n\t{out_truth_tables}"

        return result

    def negotiate_inputs(self, input_negotiations: Tuple[bool]):
        assert len(input_negotiations) == len(self.inputs)
        assert not self.finalized
        for inp, neg in zip(self.inputs, input_negotiations):
            inp.output_negotiation ^= neg

    def negotiate_outputs(self, output_negotiations: Tuple[bool]):
        assert len(output_negotiations) == len(self.outputs)
        assert not self.finalized
        for i, (out, neg) in enumerate(zip(self.outputs, output_negotiations)):
            assert id(out) == id(self.outputs[i]), f"Got: {id(out)} != {id(self.outputs[i])}"
            out.negotiation ^= neg

    def permute_inputs(self, input_permutation: Tuple[int]):
        assert len(input_permutation) == len(self.inputs)
        assert not self.finalized
        permuted_inputs = []
        input_permutation = inv_perm(input_permutation)
        for i in range(len(self.inputs)):
            permuted_inputs.append(self.inputs[input_permutation[i]])
        self.inputs = permuted_inputs

    def permute_outputs(self, output_permutation: Tuple[int]):
        assert len(output_permutation) == len(self.outputs)
        assert not self.finalized
        permuted_outputs = []
        for i in range(len(self.outputs)):
            permuted_outputs.append(self.outputs[output_permutation[i]])
        self.outputs = permuted_outputs

    def transform(self, transformation: Optional[FunctionTransformation]):
        if transformation is None:
            return
        if transformation.output_negotiations is not None:
            self.negotiate_outputs(transformation.output_negotiations)
        if transformation.input_negotiations is not None:
            self.negotiate_inputs(transformation.input_negotiations)
        if transformation.input_permutation is not None:
            self.permute_inputs(transformation.input_permutation)

    def get_output_codes(self):
        codes = [0] * len(self.outputs)
        for i in range(1 << len(self.inputs)):
            args = [bool(i >> j & 1) for j in range(len(self.inputs))[::-1]]
            for j, val in enumerate(self(args)):
                codes[j] |= int(val) << i

        return codes

    def sort_outputs(self, reverse=False):
        assert not self.finalized
        perm = list(range(len(self.outputs)))
        out_codes = self.get_output_codes()
        perm.sort(key=lambda x: out_codes[x], reverse=reverse)
        self.permute_outputs(perm)

    def __clear_labels(self):
        assert not self.finalized
        self.edge_labels = 0
        for gate in self.gates:
            gate.label = None
            gate.out_neg_label = None

    def __find_cycle(self, current: AIGCircuit.Gate, visited: Dict[int, int]):
        if visited[id(current)] == 2:
            return False
        if visited[id(current)] == 1:
            return True
        visited[id(current)] = 1
        if current.l_input is not None:
            assert current.r_input is not None
            for nxt in [current.l_input.source, current.r_input.source]:
                if self.__find_cycle(nxt, visited):
                    return True
        visited[id(current)] = 2
        return False

    def is_acyclic(self):
        visited = dict((id(i), 0) for i in self.gates)
        for gate in self.gates:
            if visited[id(gate)] != 0:
                assert visited[id(gate)] == 2
                continue
            if self.__find_cycle(gate, visited):
                return False
        return True

    def __assign_labels(self):
        assert not self.finalized
        self.__clear_labels()
        free_name = 0
        for inp in self.inputs:
            inp.label = str(free_name)
            free_name += 1
        for gate in self.gates:
            if gate.label is not None:
                continue
            gate.label = str(free_name)
            free_name += 1

        for edge in self.edges:
            source = edge.source
            if source.out_neg_label is None and (edge.is_negotiation_edge()):
                source.out_neg_label = self.__gen_out_negotiation_label()

        for output in self.outputs:
            source = output.source
            if source.out_neg_label is None and (output.is_negotiation_edge()):
                source.out_neg_label = self.__gen_out_negotiation_label()

    def finalize(self):
        assert not self.finalized
        self.__assign_labels()
        self.finalized = True

    def __str__(self):
        assert list(map(lambda x: x.label, self.inputs)) == list(map(str, range(len(self.inputs))))
        assert self.finalized

        res = []
        res += [f'{len(self.inputs)} {len(self.outputs)}']  # number of inputs and outputs
        res += [' '.join(map(str, self.get_output_codes()))]  # output codes
        assert '-' not in res[-1], f"Got: {res[-1]}"

        for output in self.outputs:  # output labels
            source = output.source
            if output.is_negotiation_edge():
                assert source.out_neg_label is not None
                res.append(source.out_neg_label)
            else:
                res.append(source.label)

        gates = dict()

        for gate in self.gates:
            assert (gate.l_input is None) == (gate.r_input is None)

            if gate.out_neg_label is not None:
                gates[int(gate.out_neg_label)] = ('NOT', gate.label)

            if gate.l_input is None or gate.r_input is None:
                continue
            l_gate = gate.l_input.source
            if gate.l_input.is_negotiation_edge():
                assert l_gate.out_neg_label is not None
                l_arg = l_gate.out_neg_label
            else:
                l_arg = l_gate.label

            r_gate = gate.r_input.source
            if gate.r_input.is_negotiation_edge():
                assert r_gate.out_neg_label is not None
                r_arg = r_gate.out_neg_label
            else:
                r_arg = r_gate.label

            gates[int(gate.label)] = ('AND', l_arg, r_arg)

        for gate_label in sorted(gates.keys()):
            res += [' '.join(gates[gate_label])]

        return ' '.join(res)

    def __clean_values(self):
        for gate in self.gates:
            gate.val = None

    def __get_val(self, gate):
        if gate.val is not None:
            return gate.val
        l_gate = gate.l_input.source
        r_gate = gate.r_input.source
        assert gate.l_input is not gate.r_input
        assert l_gate is not self
        assert r_gate is not self

        l_val = self.__get_val(l_gate) ^ gate.l_input.is_negotiation_edge()
        r_val = self.__get_val(r_gate) ^ gate.r_input.is_negotiation_edge()
        gate.val = l_val and r_val
        return gate.val

    def __call__(self, args: Tuple[bool]):
        assert len(self.inputs) == len(args)

        for i, inp in enumerate(self.inputs):
            inp.val = args[i]

        res = []
        for output in self.outputs:
            res.append(self.__get_val(output.source) ^ output.is_negotiation_edge())
        self.__clean_values()
        return tuple(res)

    def get_truth_tables(self):
        tables = [list() for _ in self.outputs]
        for args in itertools.product(range(2), repeat=len(self.inputs)):
            values = self(args)
            for t, v in zip(tables, values):
                t.append(int(v))
        return tables

    def construct_draw_graph(self):
        assert self.finalized
        circuit_graph = nx.DiGraph()

        for gate in self.gates:
            circuit_graph.add_node(gate.label)

        for edge in self.edges:
            if edge.dest is None:
                continue
            source = edge.source.label
            dest = edge.dest.label
            if dest is None:
                continue
            circuit_graph.add_edge(source, dest)

        for i, edge in enumerate(self.outputs):
            source = edge.source.label
            dest = f"o{i}"
            circuit_graph.add_node(dest)
            circuit_graph.add_edge(source, dest)

        return circuit_graph

    def draw(self, file_name: str):
        graph = self.construct_draw_graph()
        agraph = nx.nx_agraph.to_agraph(graph)
        for gate in self.inputs:
            agraph.get_node(gate.label).attr['shape'] = 'box'
        for i, edge in enumerate(self.outputs):
            agraph.get_node(f"o{i}").attr['shape'] = 'box'
            if edge.is_negotiation_edge():
                agraph.get_edge(edge.source.label, f'o{i}').attr['style'] = 'dashed'
        for i, edge in enumerate(self.edges):
            if edge.dest is not None and edge.is_negotiation_edge():
                agraph.get_edge(edge.source.label, edge.dest.label).attr['style'] = 'dashed'

        agraph.layout(prog='dot')
        agraph.draw(file_name)
        print(f'Circuit image: {file_name}')

