from random import randint

circuit = []


def gen_name():
    return f"x{randint(100, 100000000)}"


def gen_sum_3(x1, x2, x3, carry, sum):
    a, c, d = [gen_name() for _ in range(3)]
    b = sum
    e = carry
    ans = [
        (a, x1, x2, "0110"),
        (b, x3, a, "0110"),
        (c, a, x3, "0001"),
        (d, x1, x2, "0001"),
        (e, d, c, "0110")
    ]
    return ans


def gen_or(inputs, output):
    ans = [(gen_name(), inputs[0], inputs[1], "0111")]
    for i in range(2, len(inputs)):
        ans += [
            (gen_name() if i + 1 < len(inputs) else output, ans[-1][0], inputs[i], "0111")
        ]
    return ans


for i in range(4):
    circuit += gen_sum_3(f"x{3 * i + 1}", f"x{3 * i + 2}", f"x{3 * i + 3}", f"c{i + 1}", f"s{i + 1}")

circuit += gen_sum_3("s1", "s2", "s3", "c5", "s5")
assert len(circuit) == 25

circuit += [("a1", "s5", "s4", "0001")]
assert len(circuit) == 26

circuit += gen_or(["c1", "c2", "c3", "c4", "c5", "a1"], "r")
assert len(circuit) == 26 + 5

print(12, 31, 1)
print(' '.join(f"x{i}" for i in range(1, 13)))
for gate, inL, inR, f in circuit:
    print(gate, inL, inR, f)
print("r")

print("====================")
assert len(circuit) == 31, f"{len(circuit)}"
