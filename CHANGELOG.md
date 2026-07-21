# v0.15.0

- **Added `BddNode.dual()` and `BddNode.mincut()`** (engine relib-bss 0.8.0). `dual()` is the
  dual structure function `φ^D(x) = ~φ(~x)`; `mincut()` returns the minimal **cut** vectors of
  the structure function (`= dual().minpath()`), or `None` when the function is not monotone
  (coherent). `minpath()` gives the minimal **path** vectors; the two are dual (series `x&y`:
  path `{x,y}`, cut `{x},{y}`; parallel is the reverse). BSS/BDD only — the multi-state (MDD)
  dual is not yet implemented.
- Docs: `minpath`/`mincut`/`dual` are described in terms of the **structure function** (whether
  they coincide with reliability "path sets" / "cut sets" depends only on success vs fault-tree
  framing). README gains a combined minimal path/cut example.

# v0.14.0

- **`minpath()` now returns `None`** when the structure function is not monotone
  (coherent), instead of raising. This replaces the v0.13.0 pair
  `minpath()` (raised) + `minpath_checked()` (returned `None`): there is now a
  single `minpath()` that returns the minimal path/cut sets or `None`
  (`minpath_checked` is removed). Engine bumped to relib-bss/relib-mss 0.7.0.
- Docs: the README is standardized on the node-centric style
  (`bss.getbdd(top).prob(...)` / `mss.getmdd(top)...`); the obsolete
  `Context`-centric calls and the duplicated low-level examples were consolidated.

# v0.13.0

- Add `BddNode.minpath_checked()` / `MddNode.minpath_checked()` (engine
  relib-bss/relib-mss 0.6.0): returns the minimal path/cut sets if the structure
  function is monotone (coherent), else `None`. `minpath()` requires a monotone
  function; use the checked variant to detect a non-monotone input instead of
  raising. Coherence is detected inside the minsol recursion (local invariant on
  the canonical diagram), aborting early on the first violation.

# v0.12.0

- **abi3 (Stable ABI) wheels.** The extension now builds against pyo3's
  `abi3-py311`, so a **single wheel per (OS, arch) works on CPython 3.11–3.14+**
  instead of one wheel per Python minor version. This removes the per-Python
  build matrix and the need to re-release for each new Python.
- **Requires Python >= 3.11** (drops 3.9/3.10; those users stay on 0.11.x).
- Upgraded pyo3 0.18 -> 0.29. No user-facing Python API change (39 tests pass on
  3.11/3.12).
- Wheels: Linux x86_64/aarch64, **macOS arm64** (Apple Silicon), Windows x86_64,
  plus sdist. Intel macOS (x86_64) wheels are dropped — Intel Macs use the sdist.

# v0.11.2

- Packaging: the release CI now also builds **macOS wheels** (arm64 + x86_64) and
  **Windows wheels** (x86_64) in addition to the existing Linux manylinux wheels and
  sdist. macOS/Apple-Silicon and Windows users no longer need a source build. No code
  change (same 0.5.1 engine as 0.11.1).

# v0.11.1

- Perf: upgrade the engine to `relib-bss`/`relib-mss` 0.5.1, which narrows MDD
  node ids/children to `u32` (~28% lower peak memory on large multi-state
  diagrams). No user-facing API change and all results are unchanged.

# v0.11.0

- Perf: upgrade the decision-diagram engine to `relib-bss`/`relib-mss` 0.5, which
  replaces the composite `ite` (BDD, boolean MDD, and value-side MtMdd2) with native
  single-pass recursions and adds commutative operand ordering to the apply caches.
  Faster construction of `ifelse`/`switch`/`kofn`/`@match`-style diagrams and MSS
  arithmetic; the user-facing Python API and all results are unchanged.

# v0.10.0

- Change: `Context` (BSS/MSS) now builds decision diagrams by walking the expression tree
  and calling the node API directly, instead of serializing it to an RPN string for Rust
  to re-parse. The user-facing API is unchanged and the variable order is identical.
- Bug fix: a variable named like a constant (`True`, `0`) silently became that constant
  and returned a wrong probability with no error
- Bug fix: a variable name containing whitespace silently split into two variables
- Bug fix: a variable named like an operator (`&` in BSS, `min` in MSS) panicked the Rust
  RPN parser
- Add: `set_varorder(names)` for BSS/MSS, to fix the variable order before the diagram is
  built (previously only possible via `Context(vars=[...])`); `MSS.get_varorder()`
- Note: `to_rpn()` / `BDD.rpn()` / `MDD.rpn()` still exist but are only for debugging and
  the raw Rust DSL; they retain the string-encoding hazards listed above

# v0.9.0

- Bug fix: `BSS.Not` emitted an invalid `!` token, which the RPN parser silently turned
  into a variable named `!` and built a wrong BDD; it now emits `~`
- Add: `~` (NOT) and `^` (XOR) operators for BSS expressions
- Add: `Min` and `Max` for MSS
- Perf: memoize `Context.kofn` so the generated RPN is polynomial instead of exponential
- Perf: emit `save`/`load` only for shared nodes; RPN generation unified in `relibmss/_rpn.py`
- Fix: remove mutable default arguments; restore hashability of nodes/expressions that
  overload `__eq__`
- Change: unify the argument names of `prob`/`prob_interval`/`bmeas` to `probability` and
  `values`
- Change: depend on the `relib-bss`/`relib-mss` 0.4 crates from crates.io instead of a git
  branch

# v0.8.2

- add info and clear_cache for BDD/MDD

# v0.8.1

- bug fix: Min, Max for MDD
- Add test codes based on examples

# v0.8.0

- Change a lot of interfaces to use BDD/MDD directly

# v0.7.1

- Bug fix: comparation operator for BddNode/MddNode

# v0.7.0

- Change the dependencies for Rust packages

# v0.6.5

- Change the algorithm to create RPN

# v0.6.4

- Add ite for BddNode/MddNode

# v0.6.3

- Chage the interface to compute the probability for MSS

# v0.6.1-0.6.2

- Add get_varorder for BSS

# v0.6.0

- Change the method 'extranct' as an Iterator in BSS

# v0.5.2

- Add b-measure for BDD

# v0.5.1

- Python 3.10 support

# v0.5.0

- Change interface

# v0.4.4

- add aarch64 support

# v0.4.3

- Add the function to calculate the prob for Bool-type MDD

# v0.4.1

- Bug fix: the bug of without 

# v0.4.0

- Add the function to draw the MDD

# v0.3.0

- First release

# v0.2.0

- change to use python codes to reduce the complexity
- change the interface for FT and MSS
- add MSS for the first time

# v0.1.0-0.1.1

- old version
