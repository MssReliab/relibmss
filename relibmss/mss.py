import warnings
import relibmss as ms

from relibmss.mdd import MddNode
from relibmss._rpn import to_rpn as _to_rpn
from relibmss._eval import evaluate as _evaluate

class _Expression:
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('+')))
    
    def __sub__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('-')))
    
    def __mul__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('*')))
    
    def __truediv__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('/')))
    
    def __eq__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('==')))
    
    def __ne__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('!=')))
    
    def __lt__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('<')))
    
    def __le__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('<=')))
    
    def __gt__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('>')))
    
    def __ge__(self, other):
        if not isinstance(other, _Expression):
            other = _Expression(other)
        return _Expression((self, other, _Expression('>=')))
    
    # `__eq__` is overloaded to build an expression (not a bool), which would set
    # `__hash__` to None and make instances unhashable. Keep identity-based hashing
    # so expressions remain usable as set members / dict keys.
    __hash__ = object.__hash__

    def to_rpn(self):
        if isinstance(self.value, tuple):
            return _to_rpn(self)
        return str(self.value)

    def __str__(self):
        return self.to_rpn()

class _Case:
    def __init__(self, cond, then):
        self.cond = cond
        self.then = then

# Operator dispatch, built once. The operator is identified positionally (last slot of
# the expression tuple), so a *variable* named 'min' can never be mistaken for the
# min operator — which used to panic the Rust RPN parser.
_MSS_OPS = {
    '+': lambda ctx, a: a[0] + a[1],
    '-': lambda ctx, a: a[0] - a[1],
    '*': lambda ctx, a: a[0] * a[1],
    '/': lambda ctx, a: a[0] / a[1],
    '==': lambda ctx, a: a[0] == a[1],
    '!=': lambda ctx, a: a[0] != a[1],
    '<': lambda ctx, a: a[0] < a[1],
    '<=': lambda ctx, a: a[0] <= a[1],
    '>': lambda ctx, a: a[0] > a[1],
    '>=': lambda ctx, a: a[0] >= a[1],
    '&&': lambda ctx, a: ctx.mdd.And([a[0], a[1]]),
    '||': lambda ctx, a: ctx.mdd.Or([a[0], a[1]]),
    '!': lambda ctx, a: ctx.mdd.Not(a[0]),
    'min': lambda ctx, a: ctx.mdd.Min([a[0], a[1]]),
    'max': lambda ctx, a: ctx.mdd.Max([a[0], a[1]]),
    '?': lambda ctx, a: a[0].ifelse(a[1], a[2]),
}


class Context:
    def __init__(self, vars=None):
        self.vars = {}
        self.mdd = ms.MDD()
        self._varnodes = {}
        for varname, domain in (vars or []):
            self.vars[varname] = domain
            self.mdd.defvar(varname, domain)

    def defvar(self, name, domain):
        self.vars[name] = domain
        return _Expression(name)

    def get_varorder(self):
        return self.mdd.get_varorder()

    def set_varorder(self, order: list):
        """Fix the variable order before any MDD variable is created.

        `defvar` only records a name and its domain; the MDD variable itself is created
        lazily when the expression is first converted (`getmdd`), in order of first
        appearance. Call this beforehand to pin the order explicitly:

            X, Y, Z = mss.defvar('X', 3), mss.defvar('Y', 3), mss.defvar('Z', 3)
            mss.set_varorder(['Z', 'Y', 'X'])
            top = mss.getmdd(mss.Min([X, Y, Z]))    # level order is Z, Y, X

        Variables left out keep being created on first appearance, after these.
        """
        existing = self.mdd.get_varorder()
        if existing:
            raise ValueError(
                "variable order is already fixed ({}); set_varorder must be called "
                "before any MDD variable is created".format(existing))
        unknown = [name for name in order if name not in self.vars]
        if unknown:
            raise ValueError("undeclared variable(s): {}".format(unknown))
        for name in order:
            self.mdd.defvar(name, self.vars[name])

    def __str__(self):
        return str(self.vars)

    def _leaf(self, value):
        # Classify by Python type: a str is a variable name, bool/int are constants.
        if isinstance(value, str):
            node = self._varnodes.get(value)
            if node is None:
                if value not in self.vars:
                    raise ValueError("unknown variable: {}".format(value))
                node = self.mdd.defvar(value, self.vars[value])   # idempotent
                self._varnodes[value] = node
            return node
        if isinstance(value, (bool, int)):
            return self.mdd.const(value)
        raise ValueError("invalid leaf value: {!r}".format(value))

    def _apply(self, op, args):
        try:
            fn = _MSS_OPS[op]
        except KeyError:
            raise ValueError("unknown operator: {!r}".format(op))
        return fn(self, args)

    def getmdd(self, arg: _Expression):
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
            x = _Expression((x, y, _Expression('&&')))
        return x

    def Or(self, args: list):
        assert len(args) > 0
        x = args[0] if isinstance(args[0], _Expression) else _Expression(args[0])
        for y in args[1:]:
            if not isinstance(y, _Expression):
                y = _Expression(y)
            x = _Expression((x, y, _Expression('||')))
        return x

    def Min(self, args: list):
        assert len(args) > 0
        x = args[0] if isinstance(args[0], _Expression) else _Expression(args[0])
        for y in args[1:]:
            if not isinstance(y, _Expression):
                y = _Expression(y)
            x = _Expression((x, y, _Expression('min')))
        return x

    def Max(self, args: list):
        assert len(args) > 0
        x = args[0] if isinstance(args[0], _Expression) else _Expression(args[0])
        for y in args[1:]:
            if not isinstance(y, _Expression):
                y = _Expression(y)
            x = _Expression((x, y, _Expression('max')))
        return x

    def Not(self, arg: _Expression):
        if not isinstance(arg, _Expression):
            arg = _Expression(arg)
        return _Expression((arg, _Expression('!')))

    def ifelse(self, condition: _Expression, then_expr: _Expression, else_expr: _Expression):
        if not isinstance(condition, _Expression):
            condition = _Expression(condition)
        if not isinstance(then_expr, _Expression):
            then_expr = _Expression(then_expr)
        if not isinstance(else_expr, _Expression):
            else_expr = _Expression(else_expr)
        return _Expression((condition, then_expr, else_expr, _Expression('?')))
    
    def case(self, then, cond = None):
        if not isinstance(cond, _Expression):
            cond = _Expression(cond)
        if not isinstance(then, _Expression):
            then = _Expression(then)
        return _Case(cond=cond, then=then)
    
    def switch(self, conds: list):
        assert len(conds) >= 2
        if len(conds) == 2:
            assert isinstance(conds[0], _Case) and isinstance(conds[1], _Case)
            return self.ifelse(conds[0].cond, conds[0].then, conds[1].then)
        else:
            x = conds[0]
            if not isinstance(x, _Case):
                raise ValueError("The element must be a Case object")
            return self.ifelse(x.cond, x.then, self.switch(conds[1:]))

    def prob(self, arg: _Expression, probability: dict, values: list):
        warnings.warn("This function is obsolete. Use the method of MddNode directly.", category=DeprecationWarning)
        top = self.getmdd(arg)
        return top.prob(probability, values)

    def prob_interval(self, arg: _Expression, probability: dict, values: list):
        warnings.warn("This function is obsolete. Use the method of MddNode directly.", category=DeprecationWarning)
        top = self.getmdd(arg)
        return top.prob_interval(probability, values)

    def bmeas(self, arg: _Expression, probability: dict, values: list):
        warnings.warn("This function is obsolete. Use the method of MddNode directly.", category=DeprecationWarning)
        top = self.getmdd(arg)
        return top.bmeas(probability, values)

    def bmeas_interval(self, arg: _Expression, probability: dict, values: list):
        warnings.warn("This function is obsolete. Use the method of MddNode directly.", category=DeprecationWarning)
        top = self.getmdd(arg)
        return top.bmeas_interval(probability, values)

    def minpath(self, arg: _Expression):
        top = self.getmdd(arg)
        return top.minpath()

    def mincut(self, arg: _Expression):
        top = self.getmdd(arg)
        return top.mincut()
