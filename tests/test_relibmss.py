import math
import subprocess

import relibmss as ms


PROB = {"A": 0.1, "B": 0.2, "C": 0.3}


def _close(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


def test_bss_and_or_prob():
    bss = ms.BSS()
    A = bss.defvar("A")
    B = bss.defvar("B")
    C = bss.defvar("C")
    # P(A&B|C) = P(C) + (1-P(C)) * P(A)P(B) = 0.3 + 0.7*0.02 = 0.314
    top = bss.getbdd(A & B | C)
    assert _close(top.prob(PROB), 0.314)


def test_bss_not_prob():
    # Regression: Context.Not previously emitted an unsupported '!' token,
    # which the Rust RPN parser silently turned into a variable named '!'.
    bss = ms.BSS()
    A = bss.defvar("A")
    assert _close(bss.getbdd(bss.Not(A)).prob(PROB), 0.9)
    assert _close(bss.getbdd(~A).prob(PROB), 0.9)
    # The bogus '!' variable must not appear in the variable order.
    assert "!" not in bss.get_varorder()


def test_bss_xor_prob():
    bss = ms.BSS()
    A = bss.defvar("A")
    B = bss.defvar("B")
    # P(A^B) = P(A)(1-P(B)) + (1-P(A))P(B) = 0.1*0.8 + 0.9*0.2 = 0.26
    assert _close(bss.getbdd(A ^ B).prob(PROB), 0.26)


def test_bss_and_or_do_not_mutate_args():
    # Regression: Context.And/Or used to replace args[0] in place when it was
    # not already an _Expression, corrupting the caller's list.
    bss = ms.BSS()
    A = bss.defvar("A")
    args = [True, A]
    bss.And(args)
    assert args == [True, A]
    bss.Or(args)
    assert args == [True, A]


def test_bss_prob_keyword_names():
    # Unified signature: probability dict + optional state selector `values`.
    bss = ms.BSS()
    A = bss.defvar("A")
    B = bss.defvar("B")
    top = A & B | bss.defvar("C")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert _close(bss.prob(top, probability=PROB), 0.314)
        assert _close(bss.prob(top, probability=PROB, values=[True]), 0.314)


def test_rpn_no_save_when_unshared():
    # E2: singly-referenced compound nodes must NOT emit save()/load().
    bss = ms.BSS()
    A = bss.defvar("A")
    B = bss.defvar("B")
    C = bss.defvar("C")
    D = bss.defvar("D")
    rpn = ((A & B) | (C & D)).to_rpn()
    assert rpn.count("save(") == 0
    assert rpn.count("load(") == 0


def test_rpn_shared_emits_save_load_and_keeps_value():
    # E2: a genuinely shared subexpression still round-trips through save/load
    # and computes the same probability.
    bss = ms.BSS()
    A = bss.defvar("A")
    B = bss.defvar("B")
    sub = A & B
    top = sub | (sub & A)
    rpn = top.to_rpn()
    assert rpn.count("save(") == 1
    assert rpn.count("load(") == 1
    assert _close(bss.getbdd(top).prob({"A": 0.1, "B": 0.2}), 0.02)


def _binom_tail(k, n, p):
    # P(X >= k) for X ~ Binomial(n, p)
    total = 0.0
    for j in range(k, n + 1):
        total += math.comb(n, j) * (p ** j) * ((1 - p) ** (n - j))
    return total


def test_bss_kofn_correctness():
    # E1: memoized kofn must produce the same DD -> matches the binomial tail.
    for k, n in [(2, 4), (3, 6), (4, 8)]:
        bss = ms.BSS()
        xs = [bss.defvar("x%d" % i) for i in range(n)]
        expr = bss.kofn(k, xs)
        pv = {"x%d" % i: 0.3 for i in range(n)}
        assert _close(bss.getbdd(expr).prob(pv), _binom_tail(k, n, 0.3))


def test_bss_kofn_polynomial_size():
    # E1 regression guard: the RPN must stay polynomial. The old exponential
    # expansion produced hundreds of tokens by n=8 and blew up beyond; the
    # memoized version keeps kofn(8, 16) well under this bound.
    bss = ms.BSS()
    xs = [bss.defvar("x%d" % i) for i in range(16)]
    tokens = len(bss.kofn(8, xs).to_rpn().split())
    assert tokens < 500


def test_mss_min_max_dsl_matches_native():
    # B2: MSS Context now exposes Min/Max; results must match the native MDD ops.
    pv = {v: [0.2, 0.3, 0.5] for v in ("X", "Y", "Z")}
    states = [0, 1, 2]

    mss = ms.MSS()
    X = mss.defvar("X", 3)
    Y = mss.defvar("Y", 3)
    Z = mss.defvar("Z", 3)
    gmin = mss.getmdd(mss.Min([X, Y, Z]))
    gmax = mss.getmdd(mss.Max([X, Y, Z]))

    mdd = ms.MDD()
    Xn = mdd.defvar("X", 3)
    Yn = mdd.defvar("Y", 3)
    Zn = mdd.defvar("Z", 3)
    nmin = mdd.Min([Xn, Yn, Zn])
    nmax = mdd.Max([Xn, Yn, Zn])

    for s in states:
        assert _close(gmin.prob(pv, [s]), nmin.prob(pv, [s]))
        assert _close(gmax.prob(pv, [s]), nmax.prob(pv, [s]))
    # sanity anchors: P(min=0)=1-0.8^3=0.488, P(max=2)=1-0.5^3=0.875
    assert _close(gmin.prob(pv, [0]), 0.488)
    assert _close(gmax.prob(pv, [2]), 0.875)


def test_expressions_and_nodes_are_hashable():
    # C2: __eq__ is overloaded for the DSL; instances must stay hashable.
    bss = ms.BSS()
    mss = ms.MSS()
    bdd = ms.BDD()
    mdd = ms.MDD()
    assert len({mss.defvar("X", 2)}) == 1  # mss _Expression
    assert isinstance(hash(bdd.defvar("n")), int)
    assert isinstance(hash(mdd.defvar("v", 2)), int)
    # bss _Expression has no __eq__ override but must remain hashable too
    assert isinstance(hash(bss.defvar("A")), int)


def test_default_vars_do_not_leak_between_instances():
    # C1: `vars` default must not be a shared mutable list.
    a = ms.BSS()
    a.defvar("z")
    b = ms.BSS()
    assert b.vars == set()
    m = ms.MDD()
    m.defvar("q", 2)
    assert ms.MDD().vars == {}


def test_run_ex1():
    result = subprocess.run(["python", "./examples/ex1.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0

def test_run_ex2():
    result = subprocess.run(["python", "./examples/ex2.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0

def test_run_ex3():
    result = subprocess.run(["python", "./examples/ex3.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0

def test_run_ex4():
    result = subprocess.run(["python", "./examples/ex4.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0

def test_run_ex5():
    result = subprocess.run(["python", "./examples/ex5.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0

def test_run_ex6():
    result = subprocess.run(["python", "./examples/ex6.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0

def test_run_ex7():
    result = subprocess.run(["python", "./examples/ex7.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0

def test_run_ex8():
    result = subprocess.run(["python", "./examples/ex8.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0

def test_run_ex9():
    result = subprocess.run(["python", "./examples/ex9.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0

def test_run_ex10():
    result = subprocess.run(["python", "./examples/ex10.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0

def test_run_ex11():
    result = subprocess.run(["python", "./examples/ex11.py"], capture_output=True, text=True)
    print("Standard Output:", result.stdout)
    print("Standard Error:", result.stderr)
    assert result.returncode == 0


