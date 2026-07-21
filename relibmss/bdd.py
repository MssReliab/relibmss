import relibmss as ms
from .zdd import ZddNode

def _to_bddnode(bdd, value):
    if isinstance(value, BddNode):
        return value
    elif isinstance(value, int):
        if value == 0:
            return BddNode(bdd, bdd._value(False))
        else:
            return BddNode(bdd, bdd._value(True))
    elif isinstance(value, bool):
        return BddNode(bdd, bdd._boolean(value))
    else:
        raise ValueError("Invalid value")

class _Case:
    def __init__(self, cond, then):
        self.cond = cond
        self.then = then

class BDD:
    def __init__(self, vars=None):
        self.bdd = ms.PyBDD()
        self.vars = set([])
        for name in (vars or []):
            self.defvar(name)

    def __repr__(self):
        return 'BDD(vars={})'.format(self.get_varorder())
        
    def info(self):
        (nvars, nnodes, ncache) = self.bdd._size()
        return {
            "vars": nvars,
            "nodes": nnodes,
            "terminals": 2,
            "cache": ncache
        }
    
    def clear_cache(self):
        self.bdd._clear_cache()
    
    def defvar(self, name):
        self.vars.add(name)
        return BddNode(self.bdd, self.bdd._defvar(name))
    
    def create_node(self, header, nodes):
        return BddNode(self.bdd, self.bdd._create_node(header, nodes[0].node, nodes[1].node))
    
    def get_varorder(self):
        return self.bdd._get_varorder()
    
    def const(self, value):
        return _to_bddnode(self.bdd, value)
    
    def And(self, values):
        nodes = [_to_bddnode(self.bdd, x) for x in values]
        nodes = [x.node for x in nodes]
        return BddNode(self.bdd, self.bdd._and(nodes))
    
    def Or(self, values):
        nodes = [_to_bddnode(self.bdd, x) for x in values]
        nodes = [x.node for x in nodes]
        return BddNode(self.bdd, self.bdd._or(nodes))
    
    def Not(self, value):
        node = _to_bddnode(self.bdd, value)
        return BddNode(self.bdd, node.node._not())
    
    def kofn(self, k, values):
        nodes = [_to_bddnode(self.bdd, x) for x in values]
        nodes = [x.node for x in nodes]
        return BddNode(self.bdd, self.bdd._kofn(k, nodes))
    
    def case(self, then, cond = True):
        cond_node = _to_bddnode(self.bdd, cond)
        then_node = _to_bddnode(self.bdd, then)
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
    
    def rpn(self, expr):
        return BddNode(self.bdd, self.bdd._rpn(expr))

class BddNode:
    def __init__(self, bdd, node):
        self.bdd = bdd
        self.node = node
    
    def __repr__(self):
        return 'BddNode({})'.format(self.get_id())

    def __str__(self):
        return 'BddNode({})'.format(self.get_id())

    def get_id(self):
        return self.node._get_id()
    
    def get_header(self):
        return self.node._get_header()
    
    def get_level(self):
        return self.node._get_level()
    
    def get_label(self):
        return self.node._get_label()
    
    def get_children(self):
        return [BddNode(self.bdd, x) for x in self.node._get_children()]

    def __and__(self, other):
        other_node = _to_bddnode(self.bdd, other)
        return BddNode(self.bdd, self.node._and(other_node.node))
    
    def __or__(self, other):
        other_node = _to_bddnode(self.bdd, other)
        return BddNode(self.bdd, self.node._or(other_node.node))
    
    def __xor__(self, other):
        other_node = _to_bddnode(self.bdd, other)
        return BddNode(self.bdd, self.node._xor(other_node.node))
    
    # `__eq__` builds a BDD (not a bool), which nulls `__hash__`. Restore identity
    # hashing so nodes stay usable as set members / dict keys.
    __hash__ = object.__hash__

    def __eq__(self, other):
        other_node = _to_bddnode(self.bdd, other)
        return BddNode(self.bdd, self.node._eq(other_node.node))
    
    def __ne__(self, other):
        other_node = _to_bddnode(self.bdd, other)
        return BddNode(self.bdd, self.node._ne(other_node.node))
    
    def ifelse(self, then, els):
        then_node = _to_bddnode(self.bdd, then)
        els_node = _to_bddnode(self.bdd, els)
        return BddNode(self.bdd, self.node._ifelse(then_node.node, els_node.node))
    
    def size(self):
        return self.node._size()
    
    def count(self, values=None):
        """Number of satisfying assignments (paths to the ``1`` terminal). For minimal
        path/cut *sets*, use :meth:`minpath` / :meth:`mincut` and count the resulting
        :class:`ZddNode`."""
        if values is None:
            values = [True]
        return self.node._bdd_count(values)

    def dot(self):
        return self.node._dot()

    def extract(self, values=None):
        """Enumerate the satisfying assignments (paths to the ``1`` terminal) as lists of
        literals. For minimal path/cut sets use :meth:`minpath` / :meth:`mincut`."""
        if values is None:
            values = [True]
        return self.node._bdd_extract(values)

    def prob(self, probability, values=None):
        if values is None:
            values = [True]
        return self.node._prob(probability, values)

    def prob_interval(self, probability, values=None):
        if values is None:
            values = [True]
        interval_probability = {k: ms.Interval(v[0], v[1]) for k, v in probability.items()}
        return self.node._prob_interval(interval_probability, values)

    def minpath(self):
        """Minimal **path** vectors of the structure function, as a genuine ZDD set
        family (:class:`ZddNode`), or ``None`` if the function is not monotone
        (coherent). A minimal path vector is a minimal set of components whose
        functioning makes the system function. Fault trees built from
        ``&``/``|``/``kofn`` are always monotone; a non-monotone one (e.g. using ``^``
        or ``~``) returns ``None``. See :meth:`mincut` for the dual."""
        r = self.bdd._minpath(self.node)
        return None if r is None else ZddNode(self.bdd, r)

    def dual(self):
        """The dual structure function ``phi^D(x) = ~phi(~x)`` (a boolean BDD node).
        The minimal path vectors of the dual are the minimal cut vectors of the
        original; see :meth:`mincut`."""
        return BddNode(self.bdd, self.node._dual())

    def mincut(self):
        """Minimal **cut** vectors of the structure function, as a genuine ZDD set
        family (:class:`ZddNode`), or ``None`` if the function is not monotone. A
        minimal cut vector is a minimal set of components whose failure makes the
        system fail; equivalent to ``dual().minpath()``."""
        r = self.bdd._mincut(self.node)
        return None if r is None else ZddNode(self.bdd, r)

    def bmeas(self, probability, values=None):
        if values is None:
            values = [True]
        return self.node._bmeas(probability, values)

    def bmeas_interval(self, probability, values=None):
        if values is None:
            values = [True]
        interval_probability = {k: ms.Interval(v[0], v[1]) for k, v in probability.items()}
        return self.node._bmeas_interval(interval_probability, values)
