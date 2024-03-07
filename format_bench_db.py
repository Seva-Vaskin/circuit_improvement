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
        for inputs, outputs in itertools.product(range(2, max_inputs + 1), range(1, max_outputs + 1)):
            print(f"Processing inputs={inputs} outputs={outputs}")
            for func in BinaryFunction.all_functions(inputs, outputs):
                filepath = source_dir / ('_'.join(func.truth_tables) + '.txt')
                assert filepath.is_file(), f"Got: {filepath}"
                with filepath.open('r') as f:
                    circuit = Circuit.read_from_str(f.read())
                dest.write(f"{circuit.to_one_line_str()}\n")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print('Usage:', sys.argv[0], 'max_inputs max_outputs source_dir dest_file')
    main()
