import math
import subprocess

import pytest

import relibmss as ms


PROB = {"A": 0.1, "B": 0.2, "C": 0.3}


def _close(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


# --- Characterization tests: variable ordering -------------------------------
# These pin the CURRENT ordering rules so the RPN-string bridge can be replaced by a
# direct node-API evaluator without changing DD size / get_varorder() for existing users.
# Rules: variables are created lazily in order of FIRST APPEARANCE in the expression tree
# (not declaration order); variables that never appear are not created; variables
# pre-declared via Context(vars=[...]) are created first, in list order.


def test_varorder_is_first_appearance_not_declaration():
    bss = ms.BSS()
    A = bss.defvar("A")
    B = bss.defvar("B")
    C = bss.defvar("C")
    bss.getbdd(C & A | B)
    assert bss.get_varorder() == ["C", "A", "B"]


def test_varorder_omits_unused_variables():
    bss = ms.BSS()
    A = bss.defvar("A")
    B = bss.defvar("B")
    C = bss.defvar("C")
    bss.getbdd(B)
    assert bss.get_varorder() == ["B"]


def test_varorder_kofn_and_ifelse():
    bss = ms.BSS()
    C = bss.defvar("C")
    A = bss.defvar("A")
    B = bss.defvar("B")
    bss.getbdd(bss.kofn(2, [C, A, B]))
    assert bss.get_varorder() == ["C", "A", "B"]

    bss2 = ms.BSS()
    C2 = bss2.defvar("C")
    A2 = bss2.defvar("A")
    B2 = bss2.defvar("B")
    bss2.getbdd(bss2.ifelse(C2, A2, B2))
    assert bss2.get_varorder() == ["C", "A", "B"]


def test_varorder_with_shared_subexpression():
    bss = ms.BSS()
    A = bss.defvar("A")
    B = bss.defvar("B")
    C = bss.defvar("C")
    sub = C & A
    bss.getbdd(sub | (sub & B))
    assert bss.get_varorder() == ["C", "A", "B"]


def test_varorder_predeclared_wins():
    bss = ms.BSS(vars=["X", "Y", "Z"])
    Z = bss.defvar("Z")
    X = bss.defvar("X")
    bss.getbdd(Z & X)
    assert bss.get_varorder() == ["X", "Y", "Z"]


def test_varorder_partial_predeclaration():
    bss = ms.BSS(vars=["B"])
    A = bss.defvar("A")
    B = bss.defvar("B")
    C = bss.defvar("C")
    bss.getbdd(C & A | B)
    # pre-declared first, the rest by first appearance
    assert bss.get_varorder() == ["B", "C", "A"]


def test_varorder_predeclared_unused_is_kept():
    bss = ms.BSS(vars=["P", "Q"])
    P = bss.defvar("P")
    bss.getbdd(P)
    assert bss.get_varorder() == ["P", "Q"]


def test_varorder_mss_first_appearance():
    mss = ms.MSS()
    X = mss.defvar("X", 3)
    Y = mss.defvar("Y", 3)
    Z = mss.defvar("Z", 3)
    mss.getmdd(mss.Min([Z, X]))
    # MDD.get_varorder() yields (name, domain) pairs; Y never appears so it is not created.
    assert mss.mdd.get_varorder() == [("Z", 3), ("X", 3)]


def test_set_varorder_pins_order():
    bss = ms.BSS()
    A = bss.defvar("A")
    B = bss.defvar("B")
    C = bss.defvar("C")
    bss.set_varorder(["C", "B", "A"])
    bss.getbdd(A & B | C)
    assert bss.get_varorder() == ["C", "B", "A"]

    mss = ms.MSS()
    X = mss.defvar("X", 3)
    Y = mss.defvar("Y", 3)
    Z = mss.defvar("Z", 3)
    mss.set_varorder(["Z", "Y", "X"])
    mss.getmdd(mss.Min([X, Y, Z]))
    assert [n for n, _ in mss.get_varorder()] == ["Z", "Y", "X"]


def test_set_varorder_partial_then_first_appearance():
    bss = ms.BSS()
    A = bss.defvar("A")
    B = bss.defvar("B")
    C = bss.defvar("C")
    bss.set_varorder(["B"])
    bss.getbdd(C & A | B)
    assert bss.get_varorder() == ["B", "C", "A"]


def test_set_varorder_rejects_bad_input():
    bss = ms.BSS()
    bss.defvar("A")
    with pytest.raises(ValueError):
        bss.set_varorder(["A", "nope"])          # undeclared

    bss2 = ms.BSS()
    A2 = bss2.defvar("A")
    bss2.getbdd(A2)                              # variables now created
    with pytest.raises(ValueError):
        bss2.set_varorder(["A"])                 # too late to reorder


# --- Variable names that the old RPN-string bridge corrupted -----------------
# Each of these used to fail silently or panic the Rust engine, because the token
# stream could not distinguish a variable name from an operator or a constant.


def test_variable_named_like_a_constant():
    # Used to stringify to the "True"/"0" constant tokens and return 1.0 / 0.0.
    bss = ms.BSS()
    T = bss.defvar("True")
    assert _close(bss.getbdd(T).prob({"True": 0.5}), 0.5)

    bss2 = ms.BSS()
    Z = bss2.defvar("0")
    X = bss2.defvar("X")
    assert _close(bss2.getbdd(Z & X).prob({"0": 0.5, "X": 0.5}), 0.25)


def test_variable_name_with_whitespace():
    # Used to split into two variables on the RPN whitespace boundary.
    bss = ms.BSS()
    V = bss.defvar("my var")
    assert _close(bss.getbdd(V).prob({"my var": 0.5}), 0.5)
    assert bss.get_varorder() == ["my var"]


def test_variable_named_like_an_operator():
    # Used to panic the Rust RPN parser (stack underflow on the '&' / 'min' arm).
    bss = ms.BSS()
    amp = bss.defvar("&")
    Y = bss.defvar("Y")
    assert _close(bss.getbdd(amp & Y).prob({"&": 0.5, "Y": 0.5}), 0.25)

    mss = ms.MSS()
    mn = mss.defvar("min", 2)
    W = mss.defvar("W", 2)
    top = mss.getmdd(mss.Min([mn, W]))
    assert _close(top.prob({"min": [0.5, 0.5], "W": [0.5, 0.5]}, [1]), 0.25)


def test_mss_unknown_variable_raises():
    mss = ms.MSS()
    mss.defvar("X", 2)
    with pytest.raises(ValueError):
        mss.getmdd(mss.const("undeclared"))


def test_deep_expression_does_not_hit_recursion_limit():
    # And([...]) builds a left-leaning tree; the evaluator uses an explicit stack.
    bss = ms.BSS()
    xs = [bss.defvar("x%d" % i) for i in range(2000)]
    top = bss.getbdd(bss.And(xs))
    assert _close(top.prob({"x%d" % i: 1.0 for i in range(2000)}), 1.0)


# -----------------------------------------------------------------------------


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




def test_minpath_checked_coherence():
    # BSS: monotone -> node, non-monotone -> None.
    b = ms.BSS()
    x, y = b.defvar("x"), b.defvar("y")
    assert b.getbdd(x & y).minpath_checked() is not None
    assert b.getbdd(x | y).minpath_checked() is not None
    assert b.getbdd(x ^ y).minpath_checked() is None  # xor: non-monotone

    # MSS: coherent value / boolean -> node, non-coherent -> None.
    m = ms.MSS()
    u, v = m.defvar("u", 3), m.defvar("v", 3)
    assert m.getmdd(u + v).minpath_checked() is not None   # coherent value
    assert m.getmdd(u - v).minpath_checked() is None       # u - v decreases in v
    assert m.getmdd(u < v).minpath_checked() is None       # [u<v] decreases in u
