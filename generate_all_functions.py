import itertools
import sys
from binary_function import BinaryFunction


def is_normalized(function: BinaryFunction) -> bool:
    return all(tt[0] == '0' for tt in function.truth_tables)


def main():
    number_of_inputs = int(sys.argv[1])
    number_of_outputs = int(sys.argv[2])

    # groups = BinaryFunction.all_functions_grouped(number_of_inputs, number_of_outputs, basis)
    groups = BinaryFunction.all_functions(number_of_inputs, number_of_outputs)
    groups = filter(is_normalized, groups)
    print(*groups, sep='\n')

    # Tests
    # for function in BinaryFunction.all_functions(number_of_inputs, number_of_outputs):
    #     eq_class = function.get_equivalence_class(basis)
    #     rep = BinaryFunction.get_representative(eq_class)
    #     assert function in eq_class
    #     assert eq_class == groups[rep]


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage:', sys.argv[0], 'n m basis')
        print('(n is the number of inputs, m is the number of outputs)')
        sys.exit(-1)

    main()
