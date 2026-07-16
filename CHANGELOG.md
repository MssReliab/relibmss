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
