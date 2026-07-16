import warnings
import relibmss as ms

from relibmss._rpn import to_rpn as _to_rpn
from relibmss._eval import evaluate as _evaluate

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

# Operator dispatch, built once. Keyed by the token the DSL stores in the last slot of
# an expression tuple — the operator is identified positionally, never by scanning text,
# so a *variable* named '&' can never be mistaken for the AND operator.
_BSS_OPS = {
    '&': lambda ctx, a: a[0] & a[1],
    '|': lambda ctx, a: a[0] | a[1],
    '^': lambda ctx, a: a[0] ^ a[1],
    '~': lambda ctx, a: ctx.bdd.Not(a[0]),
    '?': lambda ctx, a: a[0].ifelse(a[1], a[2]),
}


class Context:
    def __init__(self, vars=None):
        self.vars = set([])
        self.bdd = ms.BDD()
        self._varnodes = {}
        for varname in (vars or []):
            self.vars.add(varname)
            self.bdd.defvar(varname)

    def defvar(self, name):
        self.vars.add(name)
        return _Expression(name)
    
    def get_varorder(self):
        return self.bdd.get_varorder()

    def set_varorder(self, order: list):
        """Fix the variable order before any BDD variable is created.

        `defvar` only records a name; the BDD variable itself is created lazily when the
        expression is first converted (`getbdd`), in order of first appearance. Call this
        beforehand to pin the order explicitly instead:

            A, B, C = bss.defvar('A'), bss.defvar('B'), bss.defvar('C')
            bss.set_varorder(['C', 'B', 'A'])
            top = bss.getbdd(A & B | C)      # level order is C, B, A

        Variables left out keep being created on first appearance, after these.
        """
        existing = self.bdd.get_varorder()
        if existing:
            raise ValueError(
                "variable order is already fixed ({}); set_varorder must be called "
                "before any BDD variable is created".format(existing))
        unknown = [name for name in order if name not in self.vars]
        if unknown:
            raise ValueError("undeclared variable(s): {}".format(unknown))
        for name in order:
            self.bdd.defvar(name)

    def __str__(self):
        return str(self.vars)

    def _leaf(self, value):
        # Classify by Python type: a str is a variable name, bool/int are constants.
        # The old RPN bridge stringified everything, so a variable named 'True' or '0'
        # collided with the constant tokens and silently became a constant.
        if isinstance(value, str):
            node = self._varnodes.get(value)
            if node is None:
                self.vars.add(value)
                node = self.bdd.defvar(value)   # idempotent; creates on first use
                self._varnodes[value] = node
            return node
        if isinstance(value, (bool, int)):
            return self.bdd.const(value)
        raise ValueError("invalid leaf value: {!r}".format(value))

    def _apply(self, op, args):
        try:
            fn = _BSS_OPS[op]
        except KeyError:
            raise ValueError("unknown operator: {!r}".format(op))
        return fn(self, args)

    def getbdd(self, arg: _Expression):
        if not isinstance(arg, _Expression):
            arg = _Expression(arg)
        return _evaluate(arg, self._leaf, self._apply)
    
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

