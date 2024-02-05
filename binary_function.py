import itertools
from collections import defaultdict


class BinaryFunction:
    def __init__(self, truth_tables):
        assert all(len(table) == len(truth_tables[0]) for table in truth_tables)
        self.truth_tables = truth_tables

    @property
    def inputs(self):
        return len(self.truth_tables[0]).bit_length() - 1

    @property
    def outputs(self):
        return len(self.truth_tables)

    def __call__(self, args: str) -> str:
        assert len(args) == self.inputs
        idx = int(args, 2)
        return ''.join(t[idx] for t in self.truth_tables)

    def __hash__(self):
        return hash(self.truth_tables)

    def __eq__(self, other):
        assert isinstance(other, BinaryFunction)
        return self.truth_tables == other.truth_tables

    def __repr__(self):
        return ' '.join(self.truth_tables)

    def __lt__(self, other):
        assert isinstance(other, BinaryFunction)
        return self.truth_tables < other.truth_tables

    def has_equal_outputs(self):
        return len(set(self.truth_tables)) != len(self.truth_tables)

    def transform(self, input_permutation=None, input_negotiations=None, output_negotiations=None):

        assert input_permutation is None or self.inputs == len(input_permutation)
        assert input_negotiations is None or self.inputs == len(input_negotiations)
        assert output_negotiations is None or self.outputs == len(output_negotiations)

        result_tables = tuple(list() for _ in range(len(self.truth_tables)))

        # Iterate over all possible arguments
        for i in range(1 << self.inputs):
            args = format(i, f'0{self.inputs}b')

            # Apply inputs permutation
            if input_permutation is None:
                permuted_args = args
            else:
                permuted_args = ''.join(args[input_permutation[j]] for j in range(self.inputs))

            # Apply inputs negotiations
            if input_negotiations is None:
                negotiated_args = permuted_args
            else:
                negotiated_args = ''.join('0' if (permuted_args[j] == '0') ^ input_negotiations[j] else '1'
                                          for j in range(self.inputs))

            # Iterate over functions values
            for j, (table, val) in enumerate(zip(result_tables, self(negotiated_args))):
                # Apply output negotiation
                if output_negotiations is not None and output_negotiations[j]:
                    val = '1' if val == '0' else '0'

                # Save value
                table.append(val)

        return BinaryFunction(tuple(sorted(''.join(table) for table in result_tables)))

    def normalized(self):
        new_truth_tables = []
        for truth_table in self.truth_tables:
            if truth_table[0] == '0':
                new_truth_tables.append(truth_table)
            else:
                new_truth_tables.append(''.join('1' if x == '0' else '0' for x in truth_table))
        return BinaryFunction(tuple(sorted(new_truth_tables)))

    def get_equivalence_class(self, basis):
        assert basis == 'aig' or basis == 'bench'

        function_class = set()

        # Iterate over input permutations
        for input_permutation, output_negotiations in itertools.product(
                itertools.permutations(range(self.inputs)), itertools.product([False, True], repeat=self.outputs)):
            assert isinstance(input_permutation, tuple)

            if basis == 'bench':
                # Find candidate for bench without input negotiations
                candidate = self.transform(input_permutation=input_permutation,
                                           output_negotiations=output_negotiations)
                function_class.add(candidate)
            else:
                assert basis == 'aig'
                # Iterate over all input negotiations (for AIG)
                for input_negotiations in itertools.product([False, True], repeat=self.inputs):
                    candidate = self.transform(input_permutation=input_permutation,
                                               input_negotiations=input_negotiations,
                                               output_negotiations=output_negotiations)
                    function_class.add(candidate)

        return function_class

    @staticmethod
    def all_functions(inputs, outputs):
        for tables in itertools.combinations(itertools.product('01', repeat=2 ** inputs), outputs):
            tables = tuple(map(lambda x: ''.join(x), tables))
            yield BinaryFunction(tables)

    @staticmethod
    def get_representative(functions):
        return min(functions)

    @staticmethod
    def all_functions_grouped(inputs, outputs, basis):
        groups = defaultdict(set)
        functions_to_be_enumerated = set(BinaryFunction.all_functions(inputs, outputs))
        for function in BinaryFunction.all_functions(inputs, outputs):
            if function not in functions_to_be_enumerated:
                continue
            function_group = function.get_equivalence_class(basis)
            representative = BinaryFunction.get_representative(function_group)
            groups[representative] = function_group
            for f in function_group:
                assert len(set(f.truth_tables)) != f.truth_tables or f in functions_to_be_enumerated
            # assert all(f in functions_to_be_enumerated for f in function_group)
            functions_to_be_enumerated.difference_update(function_group)
        assert not functions_to_be_enumerated
        return groups

    @staticmethod
    def all_normalized_functions(inputs, outputs):
        raise NotImplementedError()
