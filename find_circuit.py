import pathlib
import sys
import argparse

from core import CircuitFinder
from basis import Basis


def find_circuit(gates, dimension, tables, forbidden_operations):
    finder = CircuitFinder(dimension=dimension, number_of_gates=gates, output_truth_tables=tables,
                           forbidden_operations=forbidden_operations)
    return finder.solve_cnf_formula(solver=None)


def find_min_circuit(tables, dimension, gates_predict, forbidden_operations):
    best_circuit = False
    best_gates = int(1e5)

    gates = int(round(gates_predict))

    while gates > 0:
        circuit = find_circuit(gates, dimension, tables, forbidden_operations)
        if circuit:
            best_gates = gates
            best_circuit = circuit
            gates -= 1
        else:
            gates += 1
            break

    while not best_circuit:
        circuit = find_circuit(gates, dimension, tables, forbidden_operations)
        if circuit:
            best_circuit = circuit
            best_gates = gates
        else:
            gates += 1

    return tables, best_gates, best_circuit


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process some integers.")

    parser.add_argument('inputs', type=int, help='An integer representing the number of inputs')
    parser.add_argument('basis', choices=[b.value for b in Basis],
                        help=f'Basis one of: {" ".join(b.value for b in Basis)}')
    parser.add_argument('predictions_dir', type=pathlib.Path,
                        help='Directory where gates number predictions are stored')
    parser.add_argument('output_dir', type=pathlib.Path, help='Directory where answer should be saved')
    parser.add_argument('truth_tables', nargs='+', help='truthtable1 ... truthtablem')

    parser.add_argument('--circuit_size', type=int,
                        help='Optional argument to specify the circuit size. '
                             'If not specified, the minimal circuit will be found',
                        default=0)

    return parser.parse_args()


def main():
    args = parse_arguments()

    inputs = args.inputs
    basis = Basis(args.basis)
    predictions_dir = args.predictions_dir
    output_dir = args.output_dir
    truth_tables = args.truth_tables
    circuit_size = args.circuit_size

    match basis:
        case Basis.BENCH:
            forbidden_operations = ['0100', '1101', '0010', '1011']
        case Basis.AIG:
            forbidden_operations = ['0110', '1001']
        case Basis.XAIG:
            forbidden_operations = []
        case _:
            assert False, "Undefined basis type"

    if not output_dir.is_dir():
        print(f"Output directory ({output_dir}) is does not exist or not a directory")
        sys.exit(-1)

    if not predictions_dir.is_dir():
        print(f"Predictions directory ({predictions_dir}) is does not exist or not a directory")
        sys.exit(-1)

    circuit_file = output_dir / f"{'_'.join(truth_tables)}.txt"

    if circuit_file.exists():
        sys.exit(0)

    pred_file = predictions_dir / f"pred_{truth_tables[-1]}.pred"
    if pred_file.exists():
        with pred_file.open('r') as f:
            try:
                gates_prediction = int(f.read())
            except:
                gates_prediction = 1
    else:
        gates_prediction = 1

    if circuit_size == 0:
        _, gates_number, circuit = find_min_circuit(truth_tables, inputs, gates_prediction, forbidden_operations)
    else:
        gates_number = circuit_size
        circuit = find_circuit(gates_number, inputs, truth_tables, forbidden_operations)

    if circuit:
        with circuit_file.open('w') as f:
            print(circuit, file=f)

        with pred_file.open('w') as f:
            f.write(str(gates_number))
    else:
        assert circuit_size != 0
        print(f"Circuit of size {circuit_size} not found for function {truth_tables}", file=sys.stderr)
        exit(-1)


if __name__ == "__main__":
    main()
