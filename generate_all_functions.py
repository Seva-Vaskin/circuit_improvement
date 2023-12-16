import itertools
import sys


def all_truth_tables(inputs, outputs):
    for tables in itertools.combinations(itertools.product('01', repeat=2 ** inputs - 1), outputs):
        tables = tuple(map(lambda x: '0' + ''.join(x), tables))
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
