class ZmddNode:
    """A family of minimal path vectors (multi-state) as a ZMDD.

    Returned by :meth:`MddNode.minpath`. Supports the label-wise set operations as methods
    and operators: ``&`` intersection, ``-`` set difference. Both families must come from the
    **same** MDD context (they share one internal ZMDD forest); mixing families from
    different contexts raises ``ValueError``.

    ``count`` / ``extract`` take a ``values`` list of the terminal labels (performance
    values) to include, e.g. ``[1, 2]``.

    **Strata vs levels.** Each vector is filed under the label equal to **its own** performance
    ``phi(x)``, so ``extract([v])`` is the ``phi(x) == v`` stratum — *not* the classical
    minimal path / cut vectors at level ``v`` (``minimal{x: phi(x) >= v}`` /
    ``maximal{x: phi(x) <= v}``), which :meth:`extract_level` returns. The two agree at the
    lowest and highest labels but differ in between: a cut vector with ``phi(x) < v`` can still
    be maximal within ``{x: phi(x) <= v}`` while living in a lower stratum.
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
        """Number of minimal path vectors whose performance label is in ``values`` (this counts
        the baseline member too — see :meth:`extract`)."""
        return self.node._count(values)

    def labels(self):
        """The performance labels this family stratifies over, ascending."""
        return self.node._labels()

    def is_cut(self):
        """``True`` for a cut family (from :meth:`MddNode.mincut`), ``False`` for a path family
        (from :meth:`MddNode.minpath`). This decides the baseline of the unrecorded components:
        the max state for cuts, ``0`` for paths."""
        return self.node._is_cut()

    def extract_level(self, level):
        """The **classical** minimal path / cut vectors at ``level``:
        ``minimal{x: phi(x) >= level}`` for a path family, ``maximal{x: phi(x) <= level}`` for a
        cut family. Returns a list of dense ``{var: value}`` dicts.

        This differs from ``extract([level])``, which returns only the stratum whose ``phi(x)``
        is exactly ``level``. See the class docstring."""
        return self.node._extract_level(level)

    def extract(self, values):
        """Enumerate the minimal path/cut vectors whose performance label is in ``values``.

        Each vector is a **dense** ``{var: value}`` dict: every variable of the structure
        function is present, with the components the diagram does not record filled in at their
        baseline — ``0`` for a path family, the max state for a cut family (see
        :meth:`is_cut`). The returned iterator also supports ``len()`` (same value as
        :meth:`count`).

        ``values`` selects strata by exact performance value; for the classical "at level v"
        sets use :meth:`extract_level`. The family always contains the **baseline member** (the
        all-0 vector for paths, the all-max vector for cuts) at the label of ``phi`` at that
        point; it is a correct but trivial vector, so callers usually skip it."""
        return self.node._extract(values)

    def dot(self):
        """Graphviz source for the ZMDD diagram. Edge labels are the raw edge indices; for a
        cut family (from :meth:`MddNode.mincut`) ``extract`` reports states as
        ``edge_num-1 - d``, but the diagram shown here is the raw one. The ``Undet`` terminal
        (the empty family) and the edges into it are omitted."""
        return self.node._dot()
