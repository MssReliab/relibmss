# relibmss

A Python package for binary/multi state systems with BDD/MDD.

## Installation

```bash
pip install relibmss
```

## Usage

The recommended workflow is **node-centric**: build an expression with the overloaded
operators, convert it to a decision diagram with `getbdd` (BSS) / `getmdd` (MSS), then call
the analysis methods on the resulting node:

```python
import relibmss as ms

bss = ms.BSS()
A, B, C = bss.defvar('A'), bss.defvar('B'), bss.defvar('C')
top = A & B | C                      # build an expression
node = bss.getbdd(top)               # convert to a BDD
print(node.prob({'A': 0.1, 'B': 0.2, 'C': 0.3}))
```

(A lower-level API — `ms.BDD()` / `ms.MDD()` / `ms.ZDD()` — lets you build directly on nodes
without the expression layer; see [Standalone (low-level) managers](docs/standalone-managers.md).)

### Calculate the probability of a fault tree

```python
import relibmss as ms

# Create a binary system (fault tree)
bss = ms.BSS()

# Define events (this version only supports repeated events)
A = bss.defvar('A')
B = bss.defvar('B')
C = bss.defvar('C')

# Make a tree (& is AND gate, | is OR gate)
top = A & B | C
node = bss.getbdd(top)

# Point probabilities
prob = {'A': 0.1, 'B': 0.2, 'C': 0.3}
print(node.prob(prob))

# Interval probabilities
probint = {'A': (0.1, 0.2), 'B': (0.2, 0.3), 'C': (0.3, 0.4)}
print(node.prob_interval(probint))
```

### Boolean operators

In addition to `&` (AND) and `|` (OR), events support `~` (NOT) and `^` (XOR).

```python
import relibmss as ms

bss = ms.BSS()
A = bss.defvar('A')
B = bss.defvar('B')

prob = {'A': 0.1, 'B': 0.2}

# NOT: `~A` and `bss.Not(A)` are equivalent
print(bss.getbdd(~A).prob(prob))         # 0.9
print(bss.getbdd(bss.Not(A)).prob(prob)) # 0.9

# XOR: exactly one of A and B occurs
print(bss.getbdd(A ^ B).prob(prob))      # 0.1*0.8 + 0.9*0.2 = 0.26
```

### Variable order

The variable order determines the size of the BDD/MDD, so it can matter a lot for large
models. `defvar` only declares a variable; the diagram variable itself is created when the
expression is first converted (`getbdd`/`getmdd`), **in order of first appearance in the
expression**. Variables that never appear are not created at all.

```python
import relibmss as ms

bss = ms.BSS()
A = bss.defvar('A')
B = bss.defvar('B')
C = bss.defvar('C')

# Default: first appearance wins, not declaration order
bss.getbdd(C & A | B)
print(bss.get_varorder())   # ['C', 'A', 'B']
```

Use `set_varorder` to pin the order explicitly. It must be called **before** the first
`getbdd`/`getmdd`, because the order is fixed once the variables are created (there is no
dynamic reordering); calling it afterwards raises an error. Variables you leave out are
still created on first appearance, after the ones you listed.

```python
bss = ms.BSS()
A = bss.defvar('A')
B = bss.defvar('B')
C = bss.defvar('C')

bss.set_varorder(['C', 'B', 'A'])
bss.getbdd(A & B | C)
print(bss.get_varorder())   # ['C', 'B', 'A']
```

Passing `vars=[...]` to the constructor does the same thing: `ms.BSS(vars=['C', 'B', 'A'])`.

`get_varorder` also lets you carry an order over to another manager. Note the two differ,
because MDD variables need their number of states:

```python
bss.get_varorder()   # ['C', 'B', 'A']                 -- BSS/BDD: names
mss.get_varorder()   # [('C', 3), ('B', 3), ('A', 2)]  -- MSS/MDD: (name, states)

bdd = ms.BDD(bss.get_varorder())   # reuse the order in a raw BDD
mdd = ms.MDD(mss.get_varorder())   # likewise for an MDD
```

### Obtain the minimal path / cut vectors

For a structure function `φ`, `minpath()` returns the **prime implicants of `φ`** and
`mincut()` returns the prime implicants of its dual `φ^D`. They are dual: `mincut()` is
`dual().minpath()`, where `dual()` is the dual structure function `φ^D(x) = ~φ(~x)`.

> **Which is "path" and which is "cut" depends on how you modeled `φ`.** The method names
> refer to `φ`'s own implicants; translate them to reliability "path/cut" through your
> framing:
>
> - **Success function** (`φ = 1` ⟺ the system functions, variable `= 1` ⟺ that component
>   functions): `minpath()` gives the minimal **path** sets, `mincut()` the minimal **cut**
>   sets — matching the method names.
> - **Fault tree / failure function** (`φ = 1` ⟺ the top event / system failure, variable
>   `= 1` ⟺ that component fails): the two readings **swap** — `minpath()` gives the system's
>   minimal **cut** sets (smallest failure combinations causing the top event), and
>   `mincut()` gives the minimal **path** sets.
>
> The fault-tree examples in this README are failure functions, so **their minimal cut sets
> are `minpath()`** — not `mincut()`.

```python
import relibmss as ms

bss = ms.BSS()
A = bss.defvar('A')
B = bss.defvar('B')
C = bss.defvar('C')

# Make a system (k-of-n gate)
top = bss.kofn(2, [A, B, C])
node = bss.getbdd(top)

# Enumerate the satisfying paths (as a list of sets)
print('All paths which evaluate to one')
for x in node.extract():
    print(x)

# Minimal path vectors of the structure function
min_path = node.minpath().extract()
print('The number of minimal path vectors:', len(min_path))
for x in min_path:
    print(x)

# Minimal cut vectors (= minimal path vectors of the dual)
min_cut = node.mincut().extract()
print('The number of minimal cut vectors:', len(min_cut))
for x in min_cut:
    print(x)
```

`minpath`/`mincut` require a **monotone (coherent)** structure function (fault trees built
from `&`/`|`/`kofn` always are). On a non-monotone function (e.g. one using `^` or `~`) they
return `None`:

```python
node = bss.getbdd(A ^ B)     # xor: not monotone
print(node.minpath())        # None
print(node.mincut())         # None
```

#### Set algebra on path/cut families

`minpath()` and `mincut()` return a **`ZddNode`** — a genuine ZDD set family — which supports
the set algebra as methods and operators: `|` union, `&` intersection, `-` set difference,
`*` product, `/` quotient, plus `count()`, `extract()`, `dot()`.

```python
bss = ms.BSS()
A, B, C = bss.defvar('A'), bss.defvar('B'), bss.defvar('C')

p = bss.getbdd(A & B | C).minpath()   # { {C}, {A,B} }
q = bss.getbdd(A | C).minpath()       # { {A}, {C} }

print((p | q).count())                # union
print(list((p & q).extract()))        # intersection -> [['C']]
print(list((p - q).extract()))        # difference   -> [['A', 'B']]
```

Set operations require both families to come from the **same** `BSS` context (they share one
internal ZDD forest); combining families from different contexts raises `ValueError`. To build
set families from scratch, use the standalone `ms.ZDD()` manager — see
[Standalone (low-level) managers](docs/standalone-managers.md).

### Draw a BDD

```python
import relibmss as ms

bss = ms.BSS()
A = bss.defvar('A')
B = bss.defvar('B')
C = bss.defvar('C')

top = A & B | C
bdd = bss.getbdd(top)
source = bdd.dot()   # a string in the DOT language
print(source)

# Example: display the BDD in a Jupyter notebook
from graphviz import Source
Source(source)
```

### An example of a large fault tree

`top` here is a **fault tree** (a failure function: `top = 1` is the top event, each `c[i] = 1`
is a component failure), so `minpath()` returns the system's **minimal cut sets** — see the
framing note under [Obtain the minimal path / cut vectors](#obtain-the-minimal-path--cut-vectors).

```python
## Computational time may be long (about 1 minute)

import relibmss as ms

bss = ms.BSS()
c = [bss.defvar("c" + str(i)) for i in range(61)]

g62 = c[0] & c[1]
g63 = c[0] & c[2]
g64 = c[0] & c[3]
g65 = c[0] & c[4]
g66 = c[0] & c[5]
g67 = c[0] & c[6]
g68 = c[0] & c[7]
g69 = c[0] & c[8]
g70 = g62 | c[9]
g71 = g63 | c[10]
g72 = g64 | c[11]
g73 = g65 | c[12]
g74 = g62 | c[13]
g75 = g63 | c[14]
g76 = g64 | c[15]
g77 = g65 | c[16]
g78 = g62 | c[17]
g79 = g63 | c[18]
g80 = g64 | c[19]
g81 = g65 | c[20]
g82 = g62 | c[21]
g83 = g63 | c[22]
g84 = g64 | c[23]
g85 = g65 | c[24]
g86 = g62 | c[25]
g87 = g63 | c[26]
g88 = g64 | c[27]
g89 = g65 | c[28]
g90 = g66 | c[29]
g91 = g68 | c[30]
g92 = g67 | c[31]
g93 = g69 | c[32]
g94 = g66 | c[33]
g95 = g68 | c[34]
g96 = g67 | c[35]
g97 = g69 | c[36]
g98 = g66 | c[37]
g99 = g68 | c[38]
g100 = g67 | c[39]
g101 = g69 | c[40]
g102 = g66 | c[41]
g103 = g68 | c[42]
g104 = g67 | c[43]
g105 = g69 | c[44]
g106 = bss.kofn(3, [g70, g71, g72, g73])
g107 = bss.kofn(3, [g74, g75, g76, g77])
g108 = bss.kofn(3, [g78, g79, g80, g81])
g109 = bss.kofn(3, [g82, g83, g84, g85])
g110 = bss.kofn(3, [g86, g87, g88, g89])
g111 = bss.kofn(3, [g94, g95, g96, g97])
g112 = bss.kofn(3, [g98, g99, g100, g101])
g113 = g90 & g92
g114 = g91 & g93
g115 = g102 & g104
g116 = g103 & g105
g117 = g113 | c[45]
g118 = g114 | c[46]
g119 = g107 | g108 | c[51]
g120 = g109 | g110
g121 = g66 | g117 | c[47]
g122 = g68 | g118 | c[48]
g123 = g67 | g117 | c[49]
g124 = g69 | g118 | c[50]
g125 = bss.kofn(2, [g121, g123, g122, g124])
g126 = g111 | g112 | g125 | c[52]
g127 = g115 & g120
g128 = g116 & g120
g129 = g62 | g127 | c[53]
g130 = g63 | g128 | c[54]
g131 = g64 | g127 | c[55]
g132 = g65 | g128 | c[56]
g133 = g62 | g129 | c[57]
g134 = g63 | g130 | c[58]
g135 = g64 | g131 | c[59]
g136 = g65 | g132 | c[60]
g137 = bss.kofn(3, [g133, g134, g135, g136])
g138 = g106 | g119 | g137
g139 = g62 | g66 | g117 | g129 | c[47]
g140 = g63 | g68 | g118 | g130 | c[48]
g141 = g64 | g67 | g117 | g131 | c[49]
g142 = g65 | g69 | g118 | g132 | c[50]
g143 = g139 & g140 & g141 & g142
g144 = g111 | g112 | g143 | c[52]
top = g126 & g138 & g144

bdd = bss.getbdd(top)
print(bdd.size())      # number of nodes in the BDD

s = bdd.minpath()      # this is a fault tree → minpath() = the system's minimal CUT sets
min_cut = s.extract()
print('The number of minimal cut sets:', len(min_cut))

print('Example: 100 minimal cut sets')
from itertools import islice
for x in islice(min_cut, 0, 100):
    print(x)
```

### Importance analysis

Compute the Birnbaum importance for each event as the first-order derivative of the top-event
probability with respect to the probability of the event (assuming independent occurrences).

```python
import relibmss as ms

bss = ms.BSS()
A = bss.defvar('A')
B = bss.defvar('B')
C = bss.defvar('C')

top = A & B | C
node = bss.getbdd(top)

prob = {'A': 0.1, 'B': 0.2, 'C': 0.3}
print(node.prob(prob))
print(node.bmeas(prob))

# top = 1-(1-pa*pb)*(1-pc) = pa*pb+pc-pa*pb*pc
# d top / d pa = pb - pb*pc = 0.2 - 0.2*0.3 = 0.14
# d top / d pb = pa - pa*pc = 0.1 - 0.1*0.3 = 0.07
# d top / d pc = 1 - pa*pb = 1 - 0.1*0.2 = 0.98

# Interval versions
interval_prob = {'A': (0.1, 0.2), 'B': (0.2, 0.3), 'C': (0.3, 0.4)}
print(node.prob_interval(interval_prob))
print(node.bmeas_interval(interval_prob))

# Structure importance measure (all probabilities = 0.5)
print(node.bmeas({'A': 0.5, 'B': 0.5, 'C': 0.5}))
```

### Low-level managers (advanced)

`ms.BDD()`, `ms.MDD()`, and `ms.ZDD()` build **directly on nodes**, skipping the `BSS`/`MSS`
expression layer. See [Standalone (low-level) managers](docs/standalone-managers.md).

### TODO for fault tree analysis

- FTA with MCS
- Importance analysis
- Sensitivity analysis
- Uncertainty analysis; etc.

## Multi-state system

### Definition of gates

MSS does not have default gates. Users define gates themselves. The operations available in a
gate definition are:

- Arithmetic operations: `+`, `-`, `*`, `/`
- Comparison operations: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Logical operations:
    - `mss.And`: AND gate
    - `mss.Or`: OR gate
    - `mss.Not`: NOT gate
    - `mss.switch`: switch-case structure
    - `mss.case`: case structure
- Value operations:
    - `mss.Min`: minimum of the given expressions (series-like structure)
    - `mss.Max`: maximum of the given expressions (parallel-like structure)

`Min`/`Max` take a list and are handy when a gate is simply the weakest or strongest of its
inputs:

```python
import relibmss as ms

mss = ms.MSS()
X = mss.defvar('X', 3)
Y = mss.defvar('Y', 3)
Z = mss.defvar('Z', 3)

# The system state is the worst (Min) / best (Max) of its components
weakest = mss.Min([X, Y, Z])
strongest = mss.Max([X, Y, Z])

prob = {'X': [0.2, 0.3, 0.5], 'Y': [0.2, 0.3, 0.5], 'Z': [0.2, 0.3, 0.5]}

# P(min == 0) = 1 - 0.8^3 = 0.488
print(mss.getmdd(weakest).prob(prob, [0]))
# P(max == 2) = 1 - 0.5^3 = 0.875
print(mss.getmdd(strongest).prob(prob, [2]))
```

A larger example using `switch`/`case`:

```python
import relibmss as ms

# Define gates
def gate1(mss, x, y):
    return mss.switch([
        mss.case(cond=mss.And([x == 0, y == 0]), then=0),
        mss.case(cond=mss.Or([x == 0, y == 0]), then=1),
        mss.case(cond=mss.Or([x == 2, y == 2]), then=3),
        mss.case(then=2)  # default
    ])

def gate2(mss, x, y):
    return mss.switch([
        mss.case(cond=x == 0, then=0),
        mss.case(then=y)
    ])

mss = ms.MSS()
A = mss.defvar('A', 2)   # 2 states
B = mss.defvar('B', 3)   # 3 states
C = mss.defvar('C', 3)   # 3 states

# Define a multi-state system
sx = gate1(mss, B, C)
ss = gate2(mss, A, sx)

prob = {'A': [0.1, 0.9], 'B': [0.2, 0.3, 0.5], 'C': [0.3, 0.4, 0.3]}

# P(system state in {0, 1, 2})
print(mss.getmdd(ss).prob(prob, [0, 1, 2]))
```

### Draw an MDD

```python
import relibmss as ms

def gate1(mss, x, y):
    return mss.switch([
        mss.case(cond=mss.And([x == 0, y == 0]), then=0),
        mss.case(cond=mss.Or([x == 0, y == 0]), then=1),
        mss.case(cond=mss.Or([x == 2, y == 2]), then=3),
        mss.case(then=2)  # default
    ])

def gate2(mss, x, y):
    return mss.switch([
        mss.case(cond=x == 0, then=0),
        mss.case(then=y)
    ])

mss = ms.MSS()
A = mss.defvar('A', 2)
B = mss.defvar('B', 3)
C = mss.defvar('C', 3)

# Fix the variable order before making the MDD -- see "Variable order" above.
mss.set_varorder(["C", "B", "A"])

sx = gate1(mss, B, C)
ss = gate2(mss, A, sx)

mdd = mss.getmdd(ss)
source = mdd.dot()
print(source)

from graphviz import Source
Source(source)
```

### Obtain the minimal vector sets

```python
import relibmss as ms

def gate1(mss, x, y):
    return mss.switch([
        mss.case(cond=mss.And([x == 0, y == 0]), then=0),
        mss.case(cond=mss.Or([x == 0, y == 0]), then=1),
        mss.case(cond=mss.Or([x == 2, y == 2]), then=3),
        mss.case(then=2)  # default
    ])

def gate2(mss, x, y):
    return mss.switch([
        mss.case(cond=x == 0, then=0),
        mss.case(then=y)
    ])

mss = ms.MSS()
A = mss.defvar('A', 2)
B = mss.defvar('B', 3)
C = mss.defvar('C', 3)

sx = gate1(mss, B, C)
ss = gate2(mss, A, sx)

s = mss.getmdd(ss).minpath()   # a ZmddNode: family of minimal path vectors
# extract(values) enumerates the vectors reaching a performance label in `values`
# (sparse: only non-zero components are listed)
for path in s.extract([1, 2, 3]):
    print(path)
```

`minpath` requires a **coherent (monotone)** structure function; it returns `None` when the
function is not coherent. The result is a **`ZmddNode`** — the multi-state analogue of the BSS
`ZddNode`: a family of minimal path **vectors** (each `{var: state}`, sparse, so only non-zero
components are listed) stratified by the performance label they reach. It supports label-wise
set operations — `&` intersection, `-` set difference — plus `count(values)` / `extract(values)`:

```python
mss = ms.MSS()
X = mss.defvar('X', 3)
Y = mss.defvar('Y', 3)
Z = mss.defvar('Z', 3)

# φ = max(min(X, Y), Z): minimal path vectors {Z=1}, {Z=2}, {X=1,Y=1}, {X=2,Y=2}
a = mss.getmdd(mss.Max([mss.Min([X, Y]), Z])).minpath()
# min(X, Y): minimal path vectors {X=1,Y=1}, {X=2,Y=2}
b = mss.getmdd(mss.Min([X, Y])).minpath()

print(list((a & b).extract([1, 2])))   # intersection -> [{'X': 1, 'Y': 1}, {'X': 2, 'Y': 2}]
print(list((a - b).extract([1, 2])))   # difference   -> [{'Z': 1}, {'Z': 2}]
print((a - b).count([1, 2]))           # size of the difference -> 2
```

Set operations require both families to come from the **same** `MSS` context (they share one
internal ZMDD forest); combining families from different contexts raises `ValueError`.

### Importance analysis

`bmeas(probability, values)` returns the **multi-state Birnbaum importance** of every variable
for the success set `values`. For a variable with `M` states it returns `M-1` numbers — one per
state boundary — where `D_j = P(φ∈values | var=j) − P(φ∈values | var=j−1)` is the importance of
raising that component across the `j−1 → j` boundary (the multi-state generalization of the BSS
Birnbaum measure, which is the binary case). Computed in one backward-differentiation pass.

```python
import relibmss as ms

mss = ms.MSS()
X = mss.defvar('X', 3)
Y = mss.defvar('Y', 3)
Z = mss.defvar('Z', 3)

node = mss.getmdd(mss.Max([mss.Min([X, Y]), Z]))   # φ = max(min(X, Y), Z)
prob = {'X': [0.2, 0.3, 0.5], 'Y': [0.5, 0.1, 0.4], 'Z': [0.25, 0.25, 0.5]}

# success = performance level >= 1
print(node.bmeas(prob, [1, 2]))
# X -> [0.125, 0.0],  Y -> [0.2, 0.0],  Z -> [0.6, 0.0]   (each is [D_1, D_2])
# e.g. D_{Y,1} = P(φ>=1 | Y=1) - P(φ>=1 | Y=0) = 0.95 - 0.75 = 0.20
#   (the second entry is 0.0 here because raising a component from state 1 to 2
#    never changes whether φ>=1)

# Interval version: each per-state probability is a (lo, hi) bound
interval_prob = {'X': [(0.2, 0.2), (0.3, 0.3), (0.5, 0.5)],
                 'Y': [(0.5, 0.5), (0.1, 0.1), (0.4, 0.4)],
                 'Z': [(0.25, 0.25), (0.25, 0.25), (0.5, 0.5)]}
print(node.bmeas_interval(interval_prob, [1, 2]))
```

`bmeas_interval` returns a **guaranteed but conservative enclosure**: for every point
probability inside the given `(lo, hi)` boxes the true importance lies within the returned
interval (a degenerate box `lo == hi` reproduces `bmeas` exactly). It is not the tightest
enclosure — interval arithmetic's dependency problem, together with the difference
`P(φ|var=j) − P(φ|var=j−1)` being evaluated as a worst-case interval subtraction, widens the
bounds (the interval can even straddle 0 when the true value has a definite sign). As with
`prob_interval`, the constraint `sum_j p[var][j] == 1` is **not** enforced — the per-state
bounds are treated independently.

## TODO

- Add more examples
- Add more functions for fault tree analysis
- Add more functions for multi-state system analysis

## License

MIT License
