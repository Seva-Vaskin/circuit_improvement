from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict
from core.circuit import Circuit


@dataclass
class AIGCircuit:
    allowed_functions = {"0001", "1110", "0111", "1000",
                         "0010", "0100", "1011", "1101"}
    out_negotiate_functions = {"0111", "1110", "1011", "1101"}  # OR NAND >= <=
    l_arg_negotiate_functions = {"0111", "1000", "0100", "1011"}  # OR NOR < >=
    r_arg_negotiate_functions = {"0111", "1000", "0010", "1101"}  # OR NOR > <=

    @dataclass
    class Edge:
        source: str
        dest: str
        negotiation: bool = False

    @dataclass
    class Gate:
        outputs: List[AIGCircuit.Edge]
        l_input: Optional[AIGCircuit.Edge] = None
        r_input: Optional[AIGCircuit.Edge] = None
        func_out_negotiation: bool = False
        out_neg_label: Optional[str] = None

        def __init__(self):
            self.outputs = list()

    gates: Optional[Dict[str, Gate]] = None
    inputs: Optional[List[str]] = None
    outputs: Optional[List[str]] = None
    edges: Optional[List[Edge]] = None
    truth_tables: Optional[List[int]] = None
    edge_labels: int = 0

    def __gen_out_negotiation_label(self):
        ans = str(len(self.gates) + self.edge_labels)
        self.edge_labels += 1
        return ans

    @staticmethod
    def from_circuit(circuit: Circuit) -> AIGCircuit:
        result = AIGCircuit()
        result.inputs = circuit.input_labels
        result.outputs = circuit.outputs
        result.gates = dict()
        result.edges = list()

        for gate_label in list(circuit.gates.keys()) + circuit.input_labels:
            gate = AIGCircuit.Gate()
            result.gates[gate_label] = gate

        for gate_label, (l_arg, r_arg, function) in circuit.gates.items():
            l_edge = AIGCircuit.Edge(l_arg, gate_label)
            r_edge = AIGCircuit.Edge(r_arg, gate_label)
            result.edges.append(l_edge)
            result.edges.append(r_edge)

            gate = result.gates[gate_label]

            gate.l_input = l_edge
            gate.r_input = r_edge
            result.gates[l_arg].outputs.append(l_edge)
            result.gates[r_arg].outputs.append(r_edge)

            if function in AIGCircuit.out_negotiate_functions:
                gate.func_out_negotiation = True
            if function in AIGCircuit.l_arg_negotiate_functions:
                l_edge.negotiation = True
            if function in AIGCircuit.r_arg_negotiate_functions:
                r_edge.negotiation = True

        result.__assign_edge_labels()

        all_truth_tables = circuit.get_truth_tables()
        out_truth_tables = [''.join(map(str, all_truth_tables[i])) for i in result.outputs]
        result.truth_tables = out_truth_tables

        return result

    def __assign_edge_labels(self):
        assert set(map(int, self.gates.keys())) == set(range(len(self.gates)))

        for edge in self.edges:
            source = self.gates[edge.source]
            if source.out_neg_label is None and edge.negotiation ^ source.func_out_negotiation:
                source.out_neg_label = self.__gen_out_negotiation_label()

        for output_gate_label in self.outputs:
            gate = self.gates[output_gate_label]
            if gate.out_neg_label is None and gate.func_out_negotiation:
                gate.out_neg_label = self.__gen_out_negotiation_label()

    def __str__(self):
        assert list(self.inputs) == list(map(str, range(len(self.inputs))))

        res = []
        res += [f'{len(self.inputs)} {len(self.outputs)}']  # number of inputs and outputs
        res += [
            ' '.join(map(lambda x: str(2 ** len(self.truth_tables) - 1 - int(x, 2)),
                         self.truth_tables))]  # output codes
        res += [' '.join(out
                         if self.gates[out].out_neg_label is None
                         else self.gates[out].out_neg_label
                         for out in self.outputs)]  # output labels

        gates = dict()

        for gate_label, gate in self.gates.items():
            assert (gate.l_input is None) == (gate.r_input is None)
            if gate.l_input is None or gate.r_input is None:
                continue
            l_arg = gate.l_input.source
            l_gate = self.gates[l_arg]
            if gate.l_input.negotiation ^ l_gate.func_out_negotiation:
                l_arg = l_gate.out_neg_label

            r_arg = gate.r_input.source
            r_gate = self.gates[r_arg]
            if gate.r_input.negotiation ^ r_gate.func_out_negotiation:
                r_arg = r_gate.out_neg_label

            gates[int(gate_label)] = ('AND', l_arg, r_arg)

            if gate.out_neg_label is not None:
                gates[int(gate.out_neg_label)] = ('NOT', gate_label)

        for gate_label in sorted(gates.keys()):
            res += [' '.join(gates[gate_label])]

        return ' '.join(res)
