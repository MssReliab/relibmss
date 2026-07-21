# Standalone (low-level) managers

Besides the `BSS` / `MSS` expression layer, relibmss exposes the decision-diagram managers
directly: `ms.BDD()`, `ms.MDD()`, and `ms.ZDD()`. These build **directly on nodes**, skipping
the expression tree. `defvar` returns a node, operators combine nodes, and the analysis
methods are the same as on a node returned by `getbdd` / `getmdd`.

## Standalone BDD — `ms.BDD()`

A raw BDD manager for boolean structure functions. Every analysis method available on a
`bss.getbdd(top)` node (`prob`, `bmeas`, `minpath`, `mincut`, `extract`, `size`, `dot`, …) is
available here too.

```python
import relibmss as ms

bdd = ms.BDD()                 # optionally ms.BDD(varorder)
A = bdd.defvar('A')
B = bdd.defvar('B')
C = bdd.defvar('C')

top = A & B | C                # `top` is already a BDD node
print(top.prob({'A': 0.1, 'B': 0.2, 'C': 0.3}))
print(list(top.minpath().extract()))   # minimal path vectors, as a ZDD set family
```

## Standalone MDD — `ms.MDD()`

A raw multi-valued DD manager for multi-state structure functions. Variables are declared
with a number of states (`defvar(name, n)`); combine with `+`/`-`/`*`, comparisons, and
`Min`/`Max`.

```python
import relibmss as ms

mdd = ms.MDD()
X = mdd.defvar('X', 3)         # a 3-state component (states 0, 1, 2)
Y = mdd.defvar('Y', 3)

top = mdd.Min([X, Y])          # system state = the worse of the two components
# P(system state >= 1), given each component's state distribution
print(top.prob({'X': [0.2, 0.3, 0.5], 'Y': [0.1, 0.4, 0.5]}, [1, 2]))
```

## Standalone ZDD — `ms.ZDD()`

A ZDD manager for building and manipulating **set families** directly, independent of any
structure function. Build with `empty()` (`∅`), `base()` (`{∅}`), `singleton(label)`
(`{{label}}`) and `from_sets([...])`, then combine with the set algebra: `|` union, `&`
intersection, `-` set difference, `*` product, `/` quotient (plus `count()`, `extract()`,
`dot()`).

```python
import relibmss as ms

z = ms.ZDD()
a = z.from_sets([['x', 'y'], ['z']])          # { {x,y}, {z} }
b = z.singleton('x') | z.singleton('z')       # { {x}, {z} }

print(list((a & b).extract()))   # [['z']]
print((a | b).count())           # 3
```

A standalone `ms.ZDD()` is its own forest, so its families cannot be combined with the
`minpath()` / `mincut()` results of a `BSS` context (that raises `ValueError`). The same set
algebra is available on those results — see
[Set algebra on path/cut families](../README.md#set-algebra-on-pathcut-families).

## ZMDD (multi-state) — via `minpath()`, no standalone builder yet

There is deliberately **no** `ms.ZMDD()` here yet. The multi-state analogue of a ZDD family —
a **`ZmddNode`** (a family of minimal path vectors, stratified by performance value) — is
currently produced only from `MSS`/`MDD` `minpath()`. It supports the label-wise set
operations `&` (intersection) and `-` (set difference) plus `count(values)` / `extract(values)`
— see the MSS section of the [README](../README.md). A from-scratch `ms.ZMDD()` builder (and
`union` / arithmetic / threshold / relabel) is future work.
