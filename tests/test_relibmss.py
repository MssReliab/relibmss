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


def test_mss_bmeas_matches_pinned_prob():
    # Multi-state Birnbaum importance: bmeas[var][d] == P(phi|var=d+1) - P(phi|var=d),
    # each conditional computed by pinning `var` to a unit probability vector.
    mss = ms.MSS()
    X = mss.defvar("X", 3)
    Y = mss.defvar("Y", 3)
    Z = mss.defvar("Z", 3)
    node = mss.getmdd(mss.Max([mss.Min([X, Y]), Z]))
    prob = {"X": [0.2, 0.3, 0.5], "Y": [0.5, 0.1, 0.4], "Z": [0.25, 0.25, 0.5]}
    ss = [1, 2]

    def cond(var, j):
        pinned = {k: v[:] for k, v in prob.items()}
        e = [0.0, 0.0, 0.0]
        e[j] = 1.0
        pinned[var] = e
        return node.prob(pinned, ss)

    bm = node.bmeas(prob, ss)
    assert set(bm) == {"X", "Y", "Z"}
    for var, vec in bm.items():
        assert len(vec) == 2  # M - 1 = 2 state boundaries
        for d, g in enumerate(vec):
            assert _close(g, cond(var, d + 1) - cond(var, d))
    # spot value: D_{Y,1} = P(phi|Y=1) - P(phi|Y=0) for max(min(X,Y),Z) = 0.2
    assert _close(bm["Y"][0], 0.2)


def test_mss_mincut():
    # Minimal cut vectors: mincut().extract([v]) lists components pushed below max (unlisted
    # component stays at max) that hold phi down to level v, in phi's own value scale.
    mss = ms.MSS()
    X = mss.defvar("X", 3)
    Y = mss.defvar("Y", 3)
    Z = mss.defvar("Z", 3)

    def cuts(node, v):
        return sorted(sorted(d.items()) for d in node.mincut().extract([v]))

    # phi = max(min(X, Y), Z): to fail (phi=0) need Z=0 AND (X=0 or Y=0)
    phi = mss.getmdd(mss.Max([mss.Min([X, Y]), Z]))
    assert cuts(phi, 0) == [[("X", 0), ("Z", 0)], [("Y", 0), ("Z", 0)]]
    assert cuts(phi, 1) == [[("X", 1), ("Z", 1)], [("Y", 1), ("Z", 1)]]

    # series min(X,Y,Z): any single component dropped is a cut
    series = mss.getmdd(mss.Min([X, Y, Z]))
    assert cuts(series, 0) == [[("X", 0)], [("Y", 0)], [("Z", 0)]]
    assert cuts(series, 1) == [[("X", 1)], [("Y", 1)], [("Z", 1)]]

    # parallel max(X,Y,Z): all components must drop together
    parallel = mss.getmdd(mss.Max([X, Y, Z]))
    assert cuts(parallel, 0) == [[("X", 0), ("Y", 0), ("Z", 0)]]

    # non-coherent -> None
    assert mss.getmdd(X - Y).mincut() is None


def test_zmdd_dot_and_extract_len():
    mss = ms.MSS()
    X = mss.defvar("X", 3)
    Y = mss.defvar("Y", 3)
    Z = mss.defvar("Z", 3)
    phi = mss.getmdd(mss.Max([mss.Min([X, Y]), Z]))

    paths = phi.minpath()
    # len(extract(values)) agrees with count(values) and with the enumeration
    assert len(paths.extract([1, 2])) == paths.count([1, 2]) == 4
    assert len(list(paths.extract([1, 2]))) == 4
    assert len(paths.extract([1])) == 2

    cuts = phi.mincut()
    assert len(cuts.extract([0])) == cuts.count([0])

    dot = paths.dot()
    assert dot.startswith("digraph {")
    # the empty family (Undet) and the edges into it are not drawn
    assert "Undet" not in dot
    assert dot.rstrip().endswith("}")
    for label in ("X", "Y", "Z"):
        assert 'label="%s"' % label in dot


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




def test_minpath_coherence():
    # BSS: monotone -> node, non-monotone -> None.
    b = ms.BSS()
    x, y = b.defvar("x"), b.defvar("y")
    assert b.getbdd(x & y).minpath() is not None
    assert b.getbdd(x | y).minpath() is not None
    assert b.getbdd(x ^ y).minpath() is None  # xor: non-monotone

    # MSS: coherent value / boolean -> node, non-coherent -> None.
    m = ms.MSS()
    u, v = m.defvar("u", 3), m.defvar("v", 3)
    assert m.getmdd(u + v).minpath() is not None   # coherent value
    assert m.getmdd(u - v).minpath() is None       # u - v decreases in v
    assert m.getmdd(u < v).minpath() is None       # [u<v] decreases in u


def test_mincut_dual():
    b = ms.BSS()
    x, y = b.defvar("x"), b.defvar("y")
    # Series x & y: min path = {x,y} (1); min cut = {x},{y} (2).
    series = b.getbdd(x & y)
    assert len(list(series.minpath().extract())) == 1
    assert len(list(series.mincut().extract())) == 2
    # Parallel x | y: min path = {x},{y} (2); min cut = {x,y} (1).
    parallel = b.getbdd(x | y)
    assert len(list(parallel.minpath().extract())) == 2
    assert len(list(parallel.mincut().extract())) == 1
    # dual is an involution and dual(x&y) == x|y.
    assert series.dual().dual().prob({"x": 0.3, "y": 0.4}) == series.prob({"x": 0.3, "y": 0.4})
    # Non-monotone -> mincut None.
    assert b.getbdd(x ^ y).mincut() is None


def test_zdd_set_algebra():
    b = ms.BSS()
    x, y, z = b.defvar("x"), b.defvar("y"), b.defvar("z")

    def sset(zn):
        return sorted(map(sorted, zn.extract()))

    # Regression for the minsol bug: minpath(x&y|z) is {x,y},{z} — the non-minimal
    # {y,z} that older versions produced must be gone.
    assert sset(b.getbdd(x & y | z).minpath()) == [["x", "y"], ["z"]]

    # dot(): the `0` terminal (the empty family) is not drawn, but the 0-edge is.
    dot = b.getbdd(x & y | z).minpath().dot()
    assert 'shape=square, label="0"' not in dot
    assert '[label="0"]' in dot

    a = b.getbdd(x & y | z).minpath()   # { {z}, {x,y} }
    c = b.getbdd(x | z).minpath()       # { {x}, {z} }
    assert isinstance(a, ms.ZddNode)
    assert sset(a | c) == [["x"], ["x", "y"], ["z"]]       # union
    assert sset(a & c) == [["z"]]                          # intersection
    assert sset(a - c) == [["x", "y"]]                     # set difference
    assert a.count() == 2 and (a | c).count() == 3

    fx, fy = b.getbdd(x).minpath(), b.getbdd(y).minpath()
    assert sset(fx * fy) == [["x", "y"]]                   # product
    assert sset((fx * fy) / fy) == [["x"]]                 # quotient

    # method forms agree with operators
    assert sset(a.union(c)) == sset(a | c)
    assert sset(a.intersect(c)) == sset(a & c)


def test_zdd_cross_context_error():
    b1 = ms.BSS(); x1 = b1.defvar("x")
    b2 = ms.BSS(); x2 = b2.defvar("x")
    a = b1.getbdd(x1).minpath()
    d = b2.getbdd(x2).minpath()
    with pytest.raises(ValueError):
        _ = a | d


def test_zdd_standalone():
    z = ms.ZDD()

    def sset(zn):
        return sorted(map(sorted, zn.extract()))

    assert z.empty().count() == 0
    assert z.base().count() == 1 and sset(z.base()) == [[]]

    a = z.from_sets([["x", "y"], ["z"]])          # { {x,y}, {z} }
    b = z.singleton("x") | z.singleton("z")       # { {x}, {z} }
    assert sset(a) == [["x", "y"], ["z"]]
    assert sset(b) == [["x"], ["z"]]
    assert sset(a | b) == [["x"], ["x", "y"], ["z"]]
    assert sset(a & b) == [["z"]] and (a & b).count() == 1
    assert sset(a - b) == [["x", "y"]]
    assert sset(z.singleton("x") * z.singleton("y")) == [["x", "y"]]
    assert isinstance(a, ms.ZddNode)


def test_zdd_standalone_isolated():
    # A standalone ZDD family and a minpath family live in different forests; combining
    # them must raise, not silently produce garbage.
    z = ms.ZDD()
    a = z.from_sets([["x"]])
    b = ms.BSS()
    p, q = b.defvar("p"), b.defvar("q")
    mp = b.getbdd(p & q).minpath()
    with pytest.raises(ValueError):
        _ = a | mp
    # two families from different ms.ZDD() managers are also isolated
    z2 = ms.ZDD()
    with pytest.raises(ValueError):
        _ = a | z2.singleton("x")


def test_zmdd_set_algebra():
    m = ms.MSS()
    X, Y, Z = m.defvar('X', 3), m.defvar('Y', 3), m.defvar('Z', 3)

    def sset(zn):
        return sorted(tuple(sorted(d.items())) for d in zn.extract([1, 2]))

    a = m.getmdd(m.Max([m.Min([X, Y]), Z])).minpath()   # {z=1},{z=2},{x=1,y=1},{x=2,y=2}
    b = m.getmdd(m.Min([X, Y])).minpath()                # {x=1,y=1},{x=2,y=2}
    assert isinstance(a, ms.ZmddNode)
    # label-wise intersection / difference
    assert sset(a & b) == [(('X', 1), ('Y', 1)), (('X', 2), ('Y', 2))]
    assert sset(a - b) == [(('Z', 1),), (('Z', 2),)]
    assert (a & b).count([1, 2]) == 2 and (a - b).count([1, 2]) == 2
    # method forms agree
    assert sset(a.intersect(b)) == sset(a & b)
    assert sset(a.setdiff(b)) == sset(a - b)


def test_zmdd_cross_context_error():
    m1 = ms.MSS(); X1 = m1.defvar('X', 3)
    m2 = ms.MSS(); X2 = m2.defvar('X', 3)
    a = m1.getmdd(X1).minpath()
    b = m2.getmdd(X2).minpath()
    with pytest.raises(ValueError):
        _ = a & b
