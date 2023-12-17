import itertools
import sys


def eval_functions(truth_tables, args):
    idx = int(args, 2)
    return tuple(t[idx] for t in truth_tables)


def get_permuted_functions(number_of_inputs, truth_tables, permutation):
    result_tables = tuple(list() for _ in range(len(truth_tables)))
    for i in range(1 << number_of_inputs):
        args = format(i, f'0{number_of_inputs}b')
        permuted_args = ''.join(args[permutation[j]] for j in range(number_of_inputs))
        for table, val in zip(result_tables, eval_functions(truth_tables, permuted_args)):
            table.append(val)
    return tuple(''.join(table) for table in result_tables)


def get_equivalence_class(number_of_inputs, truth_tables):
    class_representative = truth_tables

    for permutation in itertools.permutations(range(number_of_inputs)):
        assert isinstance(permutation, tuple)
        candidate = get_permuted_functions(number_of_inputs, truth_tables, permutation)
        class_representative = min(class_representative, candidate)

    return class_representative


def all_truth_tables(inputs, outputs):
    for tables in itertools.combinations(itertools.product('01', repeat=2 ** inputs - 1), outputs):
        tables = tuple(map(lambda x: '0' + ''.join(x), tables))
        if get_equivalence_class(inputs, tables) == tables:
            yield tables


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage:', sys.argv[0], 'n m')
        print('(n is the number of inputs, m is the number of outputs)')
        sys.exit(-1)

    number_of_inputs = int(sys.argv[1])
    number_of_outputs = int(sys.argv[2])

    for truth_tables in all_truth_tables(number_of_inputs, number_of_outputs):
        print(*truth_tables)
