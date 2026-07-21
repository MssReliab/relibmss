import relibmss as ms


class ZDD:
    """A standalone ZDD manager for building and manipulating set families directly.

    Build families with :meth:`empty` (``∅``), :meth:`base` (``{∅}``),
    :meth:`singleton` (``{{label}}``) and :meth:`from_sets`, then combine them with the
    :class:`ZddNode` set algebra. Families built here are **independent** of those returned
    by :meth:`BddNode.minpath` / :meth:`BddNode.mincut` (a different forest); combining the
    two raises ``ValueError``.
    """

    def __init__(self):
        self.zdd = ms.PyZDD()

    def __repr__(self):
        return 'ZDD()'

    def info(self):
        (nvars, nnodes, ncache) = self.zdd._size()
        return {"vars": nvars, "nodes": nnodes, "cache": ncache}

    def clear_cache(self):
        self.zdd._clear_cache()

    def empty(self):
        """The empty family ``∅`` (no sets)."""
        return ZddNode(self.zdd, self.zdd._empty())

    def base(self):
        """The unit family ``{∅}`` (just the empty set) — identity for ``*`` (product)."""
        return ZddNode(self.zdd, self.zdd._base())

    def singleton(self, label):
        """The singleton family ``{{label}}``."""
        return ZddNode(self.zdd, self.zdd._singleton(label))

    def from_sets(self, sets):
        """Build a family from a list of sets, e.g. ``[["x", "y"], ["z"], []]`` →
        ``{ {x,y}, {z}, ∅ }``."""
        sets = [list(s) for s in sets]
        return ZddNode(self.zdd, self.zdd._from_sets(sets))


class ZddNode:
    """A set family as a genuine ZDD.

    Returned by :meth:`BddNode.minpath` / :meth:`BddNode.mincut`, or built from scratch via
    :class:`ZDD`. Supports the set algebra as methods and operators: ``|`` union, ``&``
    intersection, ``-`` set difference, ``*`` product, ``/`` quotient. Set operations
    require both families to come from the **same** manager (they share one ZDD forest);
    mixing families from different managers raises ``ValueError``.
    """

    def __init__(self, bdd, node):
        self.bdd = bdd      # owning Python BDD manager (identity = shared ZDD forest)
        self.node = node    # PyZddNode

    def __repr__(self):
        return 'ZddNode({})'.format(self.get_id())

    # `__eq__` is not overloaded (families are compared by identity); keep hashable.
    __hash__ = object.__hash__

    def get_id(self):
        return self.node._get_id()

    def get_label(self):
        return self.node._get_label()

    def get_children(self):
        c = self.node._get_children()
        return None if c is None else [ZddNode(self.bdd, c[0]), ZddNode(self.bdd, c[1])]

    def _op(self, other, name):
        if not isinstance(other, ZddNode) or other.bdd is not self.bdd:
            raise ValueError(
                "set operations require ZddNode families from the same BSS/BDD context")
        return ZddNode(self.bdd, getattr(self.node, name)(other.node))

    def union(self, other):
        return self._op(other, "_union")

    def intersect(self, other):
        return self._op(other, "_intersect")

    def setdiff(self, other):
        return self._op(other, "_setdiff")

    def product(self, other):
        return self._op(other, "_product")

    def divide(self, other):
        return self._op(other, "_divide")

    __or__ = union
    __and__ = intersect
    __sub__ = setdiff
    __mul__ = product
    __truediv__ = divide

    def count(self, values=None):
        if values is None:
            values = [True]
        return self.node._count(values)

    def extract(self, values=None):
        if values is None:
            values = [True]
        return self.node._extract(values)

    def dot(self):
        """Graphviz source for the ZDD diagram. The ``0`` terminal (the empty family) and the
        edges into it are omitted; the 0-edge is still drawn wherever it leads somewhere."""
        return self.node._dot()

    def size(self):
        return self.node._size()
