import itertools
import sys
from collections import defaultdict


def eval_functions(truth_tables, args):
    idx = int(args, 2)
    return tuple(t[idx] for t in truth_tables)


def get_transformed_function(number_of_inputs, truth_tables, permutation, input_negotiations, output_negotiations):
    assert number_of_inputs == len(input_negotiations)
    assert len(truth_tables) == len(output_negotiations)

    result_tables = tuple(list() for _ in range(len(truth_tables)))

    # Iterate over all possible arguments
    for i in range(1 << number_of_inputs):
        args = format(i, f'0{number_of_inputs}b')

        # Apply inputs permutation
        permuted_args = ''.join(args[permutation[j]] for j in range(number_of_inputs))

        # Apply inputs negotiations
        negotiated_args = ''.join('0' if (permuted_args[j] == '0') ^ input_negotiations[j] else '1'
                                  for j in range(number_of_inputs))

        # Iterate over functions values
        for j, (table, val) in enumerate(zip(result_tables, eval_functions(truth_tables, negotiated_args))):
            # Apply output negotiation
            if output_negotiations[j]:
                val = '1' if val == '0' else '0'

            # Save value
            table.append(val)

    return tuple(sorted(''.join(table) for table in result_tables))


def normalize_function(number_of_inputs, truth_tables, basis):
    class_representative = truth_tables

    def normalize_outputs(tables):
        new_tables = []
        for table in tables:
            if table[0] == '0':
                new_tables.append(table)
            else:
                new_tables.append(''.join('1' if x == '0' else '0' for x in table))
        return tuple(new_tables)

    # Iterate over input permutations
    for permutation in itertools.permutations(range(number_of_inputs)):
        assert isinstance(permutation, tuple)

        if basis == 'bench':
            # Find candidate for bench without input negotiations
            candidate = get_transformed_function(number_of_inputs, truth_tables, permutation,
                                                 [False] * number_of_inputs, [False] * len(truth_tables))

            class_representative = min(class_representative, normalize_outputs(candidate))
        else:
            assert basis == 'aig'
            # Iterate over all input negotiations (for AIG)
            for input_negotiations in itertools.product([False, True], repeat=number_of_inputs):
                candidate = get_transformed_function(number_of_inputs, truth_tables, permutation,
                                                     input_negotiations, [False] * len(truth_tables))
                class_representative = min(class_representative, normalize_outputs(candidate))

    return class_representative


def get_all_functions(inputs, outputs):
    for tables in itertools.combinations(itertools.product('01', repeat=2 ** inputs - 1), outputs):
        tables = tuple(map(lambda x: '0' + ''.join(x), tables))
        yield tables


def normalized_truth_tables(inputs, outputs, basis):
    for tables in get_all_functions(inputs, outputs):
        normalized = normalize_function(inputs, tables, basis)
        if normalized == tables:
            yield tables


def get_grouped_functions(inputs, outputs, basis):
    grouped_functions = defaultdict(list)

    for truth_table in get_all_functions(inputs, outputs):
        normalized = normalize_function(inputs, truth_table, basis)
        grouped_functions[normalized].append(truth_table)

    return grouped_functions


def main():
    number_of_inputs = int(sys.argv[1])
    number_of_outputs = int(sys.argv[2])
    basis = sys.argv[3].lower()

    assert basis == 'aig' or basis == 'bench'

    for truth_tables in normalized_truth_tables(number_of_inputs, number_of_outputs, basis):
        print(*truth_tables)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage:', sys.argv[0], 'n m basis')
        print('(n is the number of inputs, m is the number of outputs, basis: BENCH/AIG)')
        sys.exit(-1)

    main()
