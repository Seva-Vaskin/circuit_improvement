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
    basis = sys.argv[3].lower()
    source_dir = Path(sys.argv[4])
    dest_file = Path(sys.argv[5])

    assert basis == 'aig' or basis == 'bench'
    assert source_dir.is_dir()
    assert not dest_file.exists() or dest_file.is_file()

    with dest_file.open("w") as dest:
        for inputs, outputs in itertools.product(range(2, max_inputs + 1), range(1, max_outputs + 1)):
            print(f"Processing inputs={inputs} outputs={outputs}")
            for rep_func, group_func in BinaryFunction.all_functions_grouped_iterator(inputs, outputs, basis):
                representative_filepath = source_dir / ('_'.join(rep_func.truth_tables) + '.txt')
                assert representative_filepath.is_file(), f"Got: {representative_filepath}"
                with representative_filepath.open("r") as f:
                    rep_circuit = Circuit.read_from_str(f.read())
                rep_aig = AIGCircuit.from_circuit(rep_circuit)

                built_functions = set()
                db = []
                for inp_perm in itertools.permutations(range(len(rep_aig.inputs))):
                    for inp_neg in itertools.product(range(2), repeat=len(rep_aig.inputs)):
                        for out_neg in itertools.product(range(2), repeat=len(rep_aig.outputs)):
                            transformed_function = rep_func.transform(inp_perm, inp_neg, out_neg)
                            function_tables = str(transformed_function)
                            if function_tables in built_functions:
                                continue
                            built_functions.add(function_tables)

                            f_aig = copy.deepcopy(rep_aig)
                            f_aig.transform(FunctionTransformation(inp_perm, inp_neg, out_neg))
                            f_aig.sort_outputs()
                            f_aig.finalize()
                            tables = ' '.join(map(lambda x: ''.join(map(str, x)), f_aig.get_truth_tables()))
                            assert sorted(tables) == sorted(function_tables)

                            db.append(str(f_aig))

                db.sort(key=lambda x: list(map(lambda y: 0 if y in ('AND', 'NOT') else int(y), x.split())))

                dest.write('\n'.join(db))
                dest.write('\n')


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print('Usage:', sys.argv[0], 'max_inputs max_outputs basis source_dir dest_file')
    main()
