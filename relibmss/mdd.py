import relibmss as ms
from .zmdd import ZmddNode

def _to_mddnode(mdd, value):
    if isinstance(value, MddNode):
        return value
    elif isinstance(value, int):
        return MddNode(mdd, mdd._value(value))
    elif isinstance(value, bool):
        return MddNode(mdd, mdd._boolean(value))
    else:
        raise ValueError("Invalid value")

class _Case:
    def __init__(self, cond, then):
        self.cond = cond
        self.then = then

class MDD:
    def __init__(self, vars=None):
        self.mdd = ms.PyMDD()
        self.vars = {}
        for name, n in (vars or []):
            self.defvar(name, n)
    
    def __repr__(self):
        return 'MDD(vars={})'.format(self.get_varorder())

    def info(self):
        (nvars, nnodes, nterminals, ncache) = self.mdd._size()
        return {
            "vars": nvars,
            "nodes": nnodes,
            "terminals": nterminals,
            "cache": ncache
        }
    
    def clear_cache(self):
        self.mdd._clear_cache()

    def defvar(self, name, n):
        self.vars[name] = n
        return MddNode(self.mdd, self.mdd._defvar(name, n))
    
    def create_node(self, header, nodes):
        return MddNode(self.mdd, self.mdd._create_node(header, nodes))

    def get_varorder(self):
        return self.mdd._get_varorder()
    
    def const(self, value):
        return _to_mddnode(self.mdd, value)
    
    def And(self, values):
        nodes = [_to_mddnode(self.mdd, x) for x in values]
        nodes = [x.node for x in nodes]
        return MddNode(self.mdd, self.mdd._and(nodes))
    
    def Or(self, values):
        nodes = [_to_mddnode(self.mdd, x) for x in values]
        nodes = [x.node for x in nodes]
        return MddNode(self.mdd, self.mdd._or(nodes))
    
    def Not(self, value):
        node = _to_mddnode(self.mdd, value)
        return MddNode(self.mdd, node.node._not())
    
    def Min(self, values):
        nodes = [_to_mddnode(self.mdd, x) for x in values]
        nodes = [x.node for x in nodes]
        return MddNode(self.mdd, self.mdd._min(nodes))
    
    def Max(self, values):
        nodes = [_to_mddnode(self.mdd, x) for x in values]
        nodes = [x.node for x in nodes]
        return MddNode(self.mdd, self.mdd._max(nodes))
    
    def case(self, then, cond = True):
        cond_node = _to_mddnode(self.mdd, cond)
        then_node = _to_mddnode(self.mdd, then)
        return _Case(cond=cond_node, then=then_node)
    
    def switch(self, conds: list):
        assert len(conds) >= 2
        if len(conds) == 2:
            assert isinstance(conds[0], _Case) and isinstance(conds[1], _Case)
            return conds[0].cond.ifelse(conds[0].then, conds[1].then)
        else:
            x = conds[0]
            if not isinstance(x, _Case):
                raise ValueError("The element must be a Case object")
            return x.cond.ifelse(x.then, self.switch(conds[1:]))
    
    def rpn(self, expr, vars):
        return MddNode(self.mdd, self.mdd._rpn(expr, vars))

class MddNode:
    def __init__(self, mdd, node):
        self.mdd = mdd
        self.node = node

    def __repr__(self):
        return 'MddNode({})'.format(self.get_id())
    
    def __str__(self):
        return 'MddNode({})'.format(self.get_id())
    
    def get_id(self):
        return self.node._get_id()
    
    def get_header(self):
        return self.node._get_header()

    def get_level(self):
        return self.node._get_level()
    
    def get_label(self):
        return self.node._get_label()
    
    def get_children(self):
        return [MddNode(self.mdd, x) for x in self.node._get_children()]
    
    def __add__(self, other):
        other_node = _to_mddnode(self.mdd, other)
        return MddNode(self.mdd, self.node._add(other_node.node))

    def __sub__(self, other):
        other_node = _to_mddnode(self.mdd, other)
        return MddNode(self.mdd, self.node._sub(other_node.node))
    
    def __mul__(self, other):
        other_node = _to_mddnode(self.mdd, other)
        return MddNode(self.mdd, self.node._mul(other_node.node))
    
    def __truediv__(self, other):
        other_node = _to_mddnode(self.mdd, other)
        return MddNode(self.mdd, self.node._div(other_node.node))
    
    # `__eq__` builds an MDD (not a bool), which nulls `__hash__`. Restore identity
    # hashing so nodes stay usable as set members / dict keys.
    __hash__ = object.__hash__

    def __eq__(self, other):
        other_node = _to_mddnode(self.mdd, other)
        return MddNode(self.mdd, self.node._eq(other_node.node))
    
    def __ne__(self, other):
        other_node = _to_mddnode(self.mdd, other)
        return MddNode(self.mdd, self.node._ne(other_node.node))
    
    def __lt__(self, other):
        other_node = _to_mddnode(self.mdd, other)
        return MddNode(self.mdd, self.node._lt(other_node.node))
    
    def __le__(self, other):
        other_node = _to_mddnode(self.mdd, other)
        return MddNode(self.mdd, self.node._le(other_node.node))
    
    def __gt__(self, other):
        other_node = _to_mddnode(self.mdd, other)
        return MddNode(self.mdd, self.node._gt(other_node.node))
    
    def __ge__(self, other):
        other_node = _to_mddnode(self.mdd, other)
        return MddNode(self.mdd, self.node._ge(other_node.node))
    
    def size(self):
        return self.node._size()
    
    def is_boolean(self):
        return self.node._is_boolean()
    
    def ifelse(self, then, els):
        then_node = _to_mddnode(self.mdd, then)
        els_node = _to_mddnode(self.mdd, els)
        return MddNode(self.mdd, self.node._ifelse(then_node.node, els_node.node))
    
    def count(self, values=None):
        if (not self.is_boolean()) and values is None:
            raise ValueError("Node is a value type. The argument 'values' must be provided")
        if self.is_boolean() and values is None:
            values = [1]
        return self.node._mdd_count(values)

    def dot(self):
        return self.node._dot()

    def extract(self, values=None):
        if (not self.is_boolean()) and values is None:
            raise ValueError("Node is a value type. The argument 'values' must be provided")
        if self.is_boolean() and values is None:
            values = [1]
        return self.node._mdd_extract(values)
    
    def prob(self, probability, values):
        return self.node._prob(probability, values)
    
    def prob_interval(self, probability, values):
        interval_probability = {k: [ms.Interval(u[0], u[1]) for u in v] for k, v in probability.items()}
        return self.node._prob_interval(interval_probability, values)

    def bmeas(self, probability, values):
        """Multi-state Birnbaum importance of every variable for the success set ``values``.

        Returns ``{var: [D_1, ..., D_{M-1}]}`` where ``M`` is the variable's state count and
        ``D_j = P(phi in values | var = j) - P(phi in values | var = j-1)`` is the importance
        of raising the component across the ``j-1 -> j`` state boundary (index ``d`` = the
        transition ``d -> d+1``). For a binary variable this is the single classic Birnbaum
        measure. ``probability`` maps each variable to its per-state probability vector.

        For imprecise (interval-valued) component probabilities use :meth:`bmeas_interval`."""
        return self.node._bmeas(probability, values)

    def bmeas_interval(self, probability, values):
        """Interval-arithmetic version of :meth:`bmeas`: ``probability`` maps each variable to a
        list of ``(lo, hi)`` per-state probability bounds, and each returned ``D_j`` is an
        :class:`Interval`.

        The result is a **guaranteed but conservative enclosure** of the Birnbaum importance:
        for every point probability inside the given boxes the true ``D_j`` lies within the
        returned interval, and a degenerate box (``lo == hi``) reproduces :meth:`bmeas` exactly.
        It is *not* the tightest enclosure, however -- interval arithmetic's dependency problem
        (a variable's probability recurs in the formula, and the difference
        ``P(phi|var=j) - P(phi|var=j-1)`` is evaluated with a worst-case interval subtraction)
        widens the bounds, so the interval can straddle 0 even when the true value has a
        definite sign. Like :meth:`prob_interval`, the constraint ``sum_j p[var][j] == 1`` is
        **not** enforced -- the per-state ``(lo, hi)`` bounds are treated independently."""
        interval_probability = {k: [ms.Interval(u[0], u[1]) for u in v] for k, v in probability.items()}
        return self.node._bmeas_interval(interval_probability, values)

    def minpath(self):
        """Minimal path vectors, as a genuine ZMDD set family (:class:`ZmddNode`) supporting
        label-wise ``&`` / ``-``, or ``None`` if the structure function is not coherent
        (monotone)."""
        r = self.mdd._minpath(self.node)
        return None if r is None else ZmddNode(self.mdd, r)

    def mincut(self):
        """Minimal cut vectors, as a genuine ZMDD set family (:class:`ZmddNode`), or ``None``
        if the structure function is not coherent (monotone).

        A cut vector lists the components pushed **below** their max state (an unlisted
        component stays at max); ``extract(values)`` / ``count(values)`` select the resulting
        performance level in phi's own scale, so a fault-tree failure is read with
        ``extract([0])`` (mirroring ``minpath`` paths, which are read with ``[1]``). Computed
        directly by the engine's maxsol pass, without ever building the (expensive) dual MDD."""
        r = self.mdd._mincut(self.node)
        return None if r is None else ZmddNode(self.mdd, r)
