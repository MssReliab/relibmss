"""Reverse Polish Notation (RPN) serialization for expression trees.

.. warning::

   This is **no longer how ``Context`` (BSS/MSS) builds decision diagrams** — see
   :mod:`relibmss._eval`, which walks the expression tree and calls the node API
   directly. The RPN string is kept for debugging (it is a readable dump of an
   expression) and because the Rust engine documents ``rpn()`` as an entry point.

   Prefer ``Context.getbdd`` / ``getmdd`` over ``BDD.rpn`` / ``MDD.rpn``. The string
   form is lossy and unsafe: everything is stringified, and the Rust parser treats any
   token it does not recognize as a *variable name*. So a variable named ``True`` or
   ``0`` silently becomes a constant (wrong probability, no error), a name containing
   whitespace splits into two variables, and a name like ``&`` or ``min`` can panic the
   parser. The evaluator has none of these problems because it dispatches on the
   operator's position in the tuple and on each leaf's Python type.

The traversal uses a ``save(id)`` / ``load(id)`` scheme keyed on ``id(node)`` so that
shared subexpressions (a DAG, not just a tree) are emitted once and referenced
afterwards, and only for nodes that are actually shared.
"""


def _ref_counts(expr):
    """Count how many times each compound (tuple-valued) node is reached.

    Returns a dict ``id(node) -> visit count``. Only compound nodes can be shared
    (leaves are re-emitted cheaply and deduplicated on the Rust side), so a node is
    worth a ``save``/``load`` round-trip only when its count is >= 2.
    """
    counts = {}
    stack = [expr]
    while stack:
        node = stack.pop()
        key = id(node)
        seen = key in counts
        counts[key] = counts.get(key, 0) + 1
        # Descend only on first encounter; a shared subtree is structurally identical
        # on every visit, so counting its interior once is enough.
        if not seen and isinstance(node.value, tuple):
            stack.extend(node.value)
    return counts


def to_rpn(expr):
    """Flatten an ``_Expression`` tree into a whitespace-separated RPN string.

    ``expr`` must expose a ``.value`` attribute that is either a leaf (stringified
    directly) or a tuple of child ``_Expression`` operands in operator order.

    Only genuinely shared compound nodes (reached >= 2 times) emit a ``save``/``load``
    pair; singly-referenced nodes are streamed out directly. This keeps the RPN — and
    the Rust-side cache HashMap — proportional to the number of *shared* nodes rather
    than to every internal node.
    """
    counts = _ref_counts(expr)
    stack = [expr]
    rpn = []
    saved = set([])
    while len(stack) > 0:
        node = stack.pop()
        if isinstance(node, tuple) and node[0] == "save":
            idnum = node[1]
            rpn.append('save({})'.format(idnum))
            saved.add(idnum)
        elif isinstance(node.value, tuple):
            idnum = id(node)
            if idnum in saved:
                rpn.append('load({})'.format(idnum))
            elif counts.get(idnum, 0) >= 2:
                stack.append(("save", idnum))
                for i in range(len(node.value) - 1, -1, -1):
                    stack.append(node.value[i])
            else:
                for i in range(len(node.value) - 1, -1, -1):
                    stack.append(node.value[i])
        else:
            rpn.append(str(node.value))
    return ' '.join(rpn)
