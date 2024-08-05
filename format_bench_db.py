import copy
import sys
from pathlib import Path
import itertools
from binary_function import BinaryFunction, FunctionTransformation
from core.aig_circuit import AIGCircuit
from core.circuit import Circuit


def main():
    max_inputs = int(sys.argv[1])
    max_outputs = int(sys.argv[2])
    source_dir = Path(sys.argv[3])
    dest_file = Path(sys.argv[4])

    assert source_dir.is_dir()
    assert not dest_file.exists() or dest_file.is_file()

    with dest_file.open("w") as dest:

        # for inputs, outputs in itertools.product(range(2, max_inputs + 1), range(1, max_outputs + 1)):
        #     print(f"Processing inputs={inputs} outputs={outputs}")
        for i, filepath in enumerate(source_dir.glob("*.txt")):
            with filepath.open('r') as f:
                circuit = Circuit.from_str(f.read())
            dest.write(f"{circuit.to_one_line_str()}\n")
            if i > 0 and i % 10000 == 0:
                print(f"Processed {i}")

            # for func in BinaryFunction.all_functions(inputs, outputs):
            #     out_negations = [tt[0] == '1' for tt in func.truth_tables]
            #     norm_func = func.transform(output_negotiations=out_negations)
            #
            #     if len(set(norm_func.truth_tables)) < len(norm_func.truth_tables):
            #         continue
            #     filepath = source_dir / ('_'.join(norm_func.truth_tables) + '.txt')
            #     assert filepath.is_file(), f"Got: {filepath}"
            #     with filepath.open('r') as f:
            #         norm_circuit = Circuit.from_str(f.read())
            #     circuit = copy.deepcopy(norm_circuit)
            #     circuit.outputs = []
            #     for out, neg in zip(norm_circuit.outputs, out_negations):
            #         if not neg:
            #             circuit.outputs.append(out)
            #             continue
            #         gate = circuit.gates[out]
            #         neg_gate = (out, out, "1100")
            #         neg_gate_id = len(circuit.gates) + len(circuit.input_labels)
            #         circuit.gates[neg_gate_id] = neg_gate
            #         circuit.outputs.append(neg_gate_id)
            #     dest.write(f"{circuit.to_one_line_str()}\n")
            #     circuit_tt = circuit.get_truth_tables()
            #     # out_tt = [circuit_tt[out] for out in circuit.outputs]
            #     # assert out_tt == list(list(map(int, tt)) for tt in
            #     #                       func.truth_tables), f"\nout_tt:\n\t{out_tt}\nfunc.truth_tables:\n\t{func.truth_tables}"


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print('Usage:', sys.argv[0], 'max_inputs max_outputs source_dir dest_file')
    main()
