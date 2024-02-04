import itertools
import sys
from binary_function import BinaryFunction


def main():
    number_of_inputs = int(sys.argv[1])
    number_of_outputs = int(sys.argv[2])
    basis = sys.argv[3].lower()

    assert basis == 'aig' or basis == 'bench'

    groups = BinaryFunction.all_functions_grouped(number_of_inputs, number_of_outputs, basis)
    print(*groups.keys(), sep='\n')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage:', sys.argv[0], 'n m basis')
        print('(n is the number of inputs, m is the number of outputs, basis: BENCH/AIG)')
        sys.exit(-1)

    main()
