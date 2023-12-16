import pathlib
import sys

from core import CircuitFinder


def find_circuit(gates, dimension, tables, forbidden_operations):
    finder = CircuitFinder(dimension=dimension, number_of_gates=gates, output_truth_tables=tables,
                           forbidden_operations=forbidden_operations)
    return finder.solve_cnf_formula(solver=None)


def find_min_circuit(tables, dimension, gates_predict, forbidden_operations):
    best_circuit = False
    best_gates = int(1e5)

    gates = int(round(gates_predict))

    while True:
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


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print(f"Usage: {sys.argv[0]} n basis predictions_dir output_dir truthtable1 ... truthtablem")
        print('\tn is the number of inputs')
        print('\tbasis is BENCH/AIG')
        print('\tpredictions_dir is directory where gates number predictions are stored')
        print('\toutput_dir is directory where answer should be saved')
        sys.exit(-1)

    number_of_inputs = int(sys.argv[1])
    basis = sys.argv[2]
    predictions_dir = pathlib.Path(sys.argv[3])
    output_dir = pathlib.Path(sys.argv[4])
    truth_tables = sys.argv[5:]

    if basis.lower() == 'bench':
        forbidden_operations = ['0100', '1101', '0010', '1011']
    elif basis.lower() == 'aig':
        forbidden_operations = ['0110', '1001']
    else:
        print(f"Invalid basis: {basis}, expected BENCH/AIG")
        sys.exit(-1)

    if not output_dir.is_dir():
        print(f"Output directory ({output_dir}) is does not exist or not a directory")
        sys.exit(-1)

    if not predictions_dir.is_dir():
        print(f"Predictions directory ({predictions_dir}) is does not exist or not a directory")
        sys.exit(-1)


    def get_pred_file():
        # 2^k prediction files maximum
        k = 6
        return predictions_dir / f"pred_{truth_tables[-1][:k]}.pred"


    pred_file = get_pred_file()
    if pred_file.exists():
        with pred_file.open('r') as f:
            try:
                gates_prediction = int(f.read())
            except:
                gates_prediction = 1
    else:
        gates_prediction = 1

    _, gates_number, circuit = find_min_circuit(truth_tables, number_of_inputs, gates_prediction, forbidden_operations)

    with (output_dir / f"{'_'.join(truth_tables)}.txt").open('w') as f:
        print(circuit, file=f)

    with pred_file.open('w') as f:
        f.write(str(gates_number))
