import warnings
import relibmss as ms

from relibmss._rpn import to_rpn as _to_rpn

class _Expression:
    def __init__(self, value):
        self.value = value

    def __and__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('&')))
    
    def __or__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('|')))

    def __xor__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('^')))

    def __invert__(self):
        return _Expression((self, _Expression('~')))

    def to_rpn(self):
        if isinstance(self.value, tuple):
            return _to_rpn(self)
        return str(self.value)

    def __str__(self):
        return self.to_rpn()

class Context:
    def __init__(self, vars=None):
        self.vars = set([])
        self.bdd = ms.BDD()
        for varname in (vars or []):
            self.vars.add(varname)
            self.bdd.defvar(varname)

    def defvar(self, name):
        self.vars.add(name)
        return _Expression(name)
    
    def get_varorder(self):
        return self.bdd.get_varorder()

    def __str__(self):
        return str(self.vars)
    
    def getbdd(self, arg: _Expression):
        if not isinstance(arg, _Expression):
            arg = _Expression(arg)
        rpn = arg.to_rpn()
        return self.bdd.rpn(rpn)
    
    def const(self, value):
        return _Expression(value)

    def And(self, args: list):
        assert len(args) > 0
        x = args[0] if isinstance(args[0], _Expression) else _Expression(args[0])
        for y in args[1:]:
            if not isinstance(y, _Expression):
                y = _Expression(y)
            x = _Expression((x, y, _Expression('&')))
        return x

    def Or(self, args: list):
        assert len(args) > 0
        x = args[0] if isinstance(args[0], _Expression) else _Expression(args[0])
        for y in args[1:]:
            if not isinstance(y, _Expression):
                y = _Expression(y)
            x = _Expression((x, y, _Expression('|')))
        return x

    def Not(self, arg: _Expression):
        if not isinstance(arg, _Expression):
            arg = _Expression(arg)
        return _Expression((arg, _Expression('~')))

    def ifelse(self, condition: _Expression, then_expr: _Expression, else_expr: _Expression):
        if not isinstance(condition, _Expression):
            condition = _Expression(condition)
        if not isinstance(then_expr, _Expression):
            then_expr = _Expression(then_expr)
        if not isinstance(else_expr, _Expression):
            else_expr = _Expression(else_expr)
        return _Expression((condition, then_expr, else_expr, _Expression('?')))

    def kofn(self, k: int, args: list):
        assert k <= len(args)
        n = len(args)
        # Memoize on (k, i) where i is the start index into `args`, so overlapping
        # subproblems reuse the SAME _Expression object. That lets _to_rpn's id-based
        # sharing emit load() instead of re-expanding, turning the RPN (and the DD
        # construction) from exponential into O(k*n). The DD produced is identical.
        memo = {}
        def rec(k, i):
            m = n - i               # size of the remaining sub-array args[i:]
            if k == 1:
                return self.Or(args[i:])
            if k == m:
                return self.And(args[i:])
            key = (k, i)
            if key not in memo:
                memo[key] = self.ifelse(args[i], rec(k - 1, i + 1), rec(k, i + 1))
            return memo[key]
        return rec(k, 0)
    
    def prob(self, arg: _Expression, probability: dict, values=None):
        warnings.warn("This function is obsolete. Use the method of BddNode directly.", category=DeprecationWarning)
        if values is None:
            values = [True]
        top = self.getbdd(arg)
        return top.prob(probability, values)

    def bmeas(self, arg: _Expression, probability: dict, values=None):
        warnings.warn("This function is obsolete. Use the method of BddNode directly.", category=DeprecationWarning)
        if values is None:
            values = [True]
        top = self.getbdd(arg)
        return top.bmeas(probability, values)

    def prob_interval(self, arg: _Expression, probability: dict, values=None):
        warnings.warn("This function is obsolete. Use the method of BddNode directly.", category=DeprecationWarning)
        if values is None:
            values = [True]
        top = self.getbdd(arg)
        return top.prob_interval(probability, values)

    def bmeas_interval(self, arg: _Expression, probability: dict, values=None):
        warnings.warn("This function is obsolete. Use the method of BddNode directly.", category=DeprecationWarning)
        if values is None:
            values = [True]
        top = self.getbdd(arg)
        return top.bmeas_interval(probability, values)

    def minpath(self, arg: _Expression):
        warnings.warn("This function is obsolete. Use the method of BddNode directly.", category=DeprecationWarning)
        top = self.getbdd(arg)
        return top.minpath()

