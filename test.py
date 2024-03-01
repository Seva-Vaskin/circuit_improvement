from pathlib import Path

from core.circuit import Circuit
from core.aig_circuit import AIGCircuit, FunctionTransformation
from binary_function import BinaryFunction
import itertools
import copy

for circuit_file in Path('/home/vsevolod/sat/circuit_improvement/aig_db_files/').iterdir():
    # for circuit_file in [Path('/home/vsevolod/sat/circuit_improvement/00000110_00110011_00110011.txt')]:
    print(f"Process {circuit_file}")
    with open(circuit_file, "r") as f:
        string = f.read()
        circuit = Circuit.read_from_str(string)
        string2 = str(circuit)
        # print("String1:\n", string)
        # print("====")
        # print("String2:\n", string2)
        assert string == string2 + "\n"

    all_truth_tables = circuit.get_truth_tables()
    truth_tables = [''.join(map(str, all_truth_tables[i])) for i in circuit.outputs]
    assert '_'.join(truth_tables) + ".txt" == str(circuit_file).split('/')[-1]

    aig_circuit = AIGCircuit.from_circuit(circuit)
    truth_tables = list(map(lambda x: ''.join(map(str, x)), aig_circuit.get_truth_tables()))

    assert '_'.join(truth_tables) + ".txt" == str(circuit_file).split('/')[-1]
    function = BinaryFunction(truth_tables)

    function_variants = set()

    for inp_perm in itertools.permutations(range(function.inputs)):
        for inp_neg in itertools.product((False, True), repeat=function.inputs):
            for out_neg in itertools.product((False, True), repeat=function.outputs):
                transformed_function = function.transform(inp_perm, inp_neg, out_neg)
                function_tables = str(transformed_function)

                transformed_circuit = copy.deepcopy(aig_circuit)
                transformed_circuit.transform(FunctionTransformation(inp_perm, inp_neg, out_neg))
                transformed_circuit.sort_outputs()
                transformed_circuit.finalize()

                circuit_tables = ' '.join(map(lambda x: ''.join(map(str, x)), transformed_circuit.get_truth_tables()))

                assert circuit_tables == function_tables, f"Got:\n\tcircuit:\n\t\t{circuit_tables}\n\tfunction:\n\t\t{function_tables}"
