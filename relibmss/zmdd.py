class ZmddNode:
    """A family of minimal path vectors (multi-state) as a ZMDD.

    Returned by :meth:`MddNode.minpath`. Supports the label-wise set operations as methods
    and operators: ``&`` intersection, ``-`` set difference. Both families must come from the
    **same** MDD context (they share one internal ZMDD forest); mixing families from
    different contexts raises ``ValueError``.

    ``count`` / ``extract`` take a ``values`` list of the terminal labels (performance
    values) to include, e.g. ``[1, 2]``.
    """

    def __init__(self, mdd, node):
        self.mdd = mdd      # owning ext MDD manager (identity = shared ZMDD forest)
        self.node = node    # PyZmddNode

    def __repr__(self):
        return 'ZmddNode({})'.format(self.node._get_id())

    __hash__ = object.__hash__

    def _op(self, other, name):
        if not isinstance(other, ZmddNode) or other.mdd is not self.mdd:
            raise ValueError(
                "set operations require ZmddNode families from the same MDD context")
        return ZmddNode(self.mdd, getattr(self.node, name)(other.node))

    def intersect(self, other):
        return self._op(other, "_intersect")

    def setdiff(self, other):
        return self._op(other, "_setdiff")

    __and__ = intersect
    __sub__ = setdiff

    def count(self, values):
        """Number of minimal path vectors whose performance label is in ``values``."""
        return self.node._count(values)

    def extract(self, values):
        """Enumerate the minimal path vectors (as ``{var: value}``, non-zero components only)
        whose performance label is in ``values``."""
        return self.node._extract(values)
