import itertools
import sys


def get_equivalence_class(number_of_inputs, truth_tables):
    def eval_function(truth_table, args):
        idx = int(args, 2)
        return truth_table[idx]

    def get_class(truth_table):
        class_representative = truth_table

        for perm in itertools.permutations(range(number_of_inputs)):
            assert isinstance(perm, tuple)

            candidate_table = ['?'] * (1 << number_of_inputs)
            for i in range(1 << number_of_inputs):
                args = format(i, f'0{number_of_inputs}b')
                permuted_args = ''.join(args[perm[j]] for j in range(number_of_inputs))
                candidate_table[i] = eval_function(truth_table, permuted_args)

            candidate_table = ''.join(candidate_table)
            if candidate_table[0] == '0' and candidate_table < class_representative:
                class_representative = candidate_table

        return class_representative

    return tuple(get_class(table) for table in truth_tables)


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
