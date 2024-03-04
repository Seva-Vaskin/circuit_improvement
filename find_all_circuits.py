import argparse
import sys
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm
from binary_function import BinaryFunction


def run_find_circuit(inputs, basis, pred_dir, result_dir, tables):
    """
    Execute the find_circuit.py script with the provided arguments.
    """
    command = ["python", "./find_circuit.py", str(inputs), basis, pred_dir, result_dir] + list(map(str, tables))
    subprocess.run(command)


def main(args):
    print("Generating functions:")
    truth_tables = list(BinaryFunction.all_functions(args.number_of_inputs, args.number_of_outputs))
    pbar = tqdm(total=len(truth_tables))
    Path(args.result_directory).mkdir(parents=True, exist_ok=True)
    Path(args.pred_directory).mkdir(parents=True, exist_ok=True)

    bucket = 100000
    for i in range(0, len(truth_tables), bucket):
        lft = i
        rgt = min(len(truth_tables), i + bucket)
        print(f"Start processing: [{lft}, {rgt})")
        with ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(run_find_circuit, args.number_of_inputs, args.basis, args.pred_directory,
                                args.result_directory,
                                tables.truth_tables) for tables in truth_tables[lft:rgt]]

            for future in as_completed(futures):
                future.result()
                pbar.update(1)

    pbar.close()


def parse_arguments():
    arg_parser = argparse.ArgumentParser(description="Script to process circuit parameters.")
    arg_parser.add_argument("number_of_inputs", type=int, help="An integer representing the number of inputs")
    arg_parser.add_argument("number_of_outputs", type=int, help="An integer representing the number of outputs")
    arg_parser.add_argument("basis", choices=['BENCH', 'AIG'], help="BENCH/AIG")
    arg_parser.add_argument("result_directory", type=str, help="The directory to store the results")
    arg_parser.add_argument("pred_directory", type=str, help="The directory to store number of gates predictions")

    return arg_parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
