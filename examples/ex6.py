import relibmss as ms

# Define gates
def gate1(mss, x, y):
    return mss.switch([
        mss.case(cond=mss.And([x == 0, y == 0]), then=0),
        mss.case(cond=mss.Or([x == 0, y == 0]), then=1),
        mss.case(cond=mss.Or([x == 2, y == 2]), then=3),
        mss.case(then=2) # default
    ])

def gate2(mss, x, y):
    return mss.switch([
        mss.case(cond=x == 0, then=0),
        mss.case(then=y)
    ])

mss = ms.MSS()

A = mss.defvar('A', 2)
B = mss.defvar('B', 3)
C = mss.defvar('C', 3)

# Define the order of variables. This must be done before making the MDD: variables are
# created when the expression is first converted, and the order is fixed at that point.
# Without this call they are created in order of first appearance in the expression.
# Passing vars=[("C", 3), ("B", 3), ("A", 2)] to MSS() fixes the order the same way.
mss.set_varorder(["C", "B", "A"])

sx = gate1(mss, B, C)
ss = gate2(mss, A, sx)

mdd = mss.getmdd(ss)
source = mdd.dot()
print(source)

from graphviz import Source
Source(source)
