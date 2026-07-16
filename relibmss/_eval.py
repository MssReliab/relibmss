"""Shared evaluator that turns an `_Expression` tree directly into DD nodes.

This replaces the old "serialize to an RPN string, let Rust re-parse it" bridge for the
`Context` (BSS/MSS) path. Building nodes directly removes a whole class of bugs that the
stringly-typed bridge made possible, because the Rust parser treats any token it does not
recognize as a *variable name*:

- an operator token that does not match the parser (BSS once emitted `!` for NOT, which
  the BDD parser does not handle) silently became a variable, producing a wrong DD;
- a variable named `True`/`0` collided with constant tokens and silently became a
  constant, returning a wrong probability with no error;
- a variable containing whitespace split into two variables;
- a variable named like an operator (`&`, `min`) drove the Rust parser into a panic.

Here operators are identified **positionally** (the last element of the tuple) and leaves
are classified by their **Python type**, so none of the above can happen.

Variable ordering is preserved bit-for-bit: leaves are visited in the same left-to-right
post-order the RPN serializer used, and variables are created lazily on first encounter.
"""


def evaluate(root, leaf, apply_op):
    """Evaluate an `_Expression` tree into a DD node.

    ``leaf(value)`` builds a node for a leaf's raw Python value (a variable name, or a
    constant). ``apply_op(op, args)`` applies the operator token ``op`` to already-built
    operand nodes.

    An explicit stack is used rather than recursion: expression trees are left-leaning
    (``And([x1, ..., xN])`` nests N deep), so recursion would raise RecursionError on
    large models. Shared subtrees are evaluated once and reused via an ``id()`` memo,
    which is what the old `save`/`load` scheme did.
    """
    memo = {}
    # Each entry is (node, children_evaluated).
    stack = [(root, False)]
    while stack:
        node, done = stack.pop()
        key = id(node)
        if key in memo:
            continue
        value = node.value
        if not isinstance(value, tuple):
            memo[key] = leaf(value)
            continue
        # A compound node is (operand, ..., operator); the operator is an _Expression
        # holding the token string and must never be evaluated as an operand.
        if done:
            memo[key] = apply_op(value[-1].value, [memo[id(x)] for x in value[:-1]])
        else:
            stack.append((node, True))
            # Push operands reversed so they pop left-to-right — this is what makes the
            # variable creation order match the old RPN traversal.
            for child in reversed(value[:-1]):
                stack.append((child, False))
    return memo[id(root)]
