import relibmss as ms

# Create a binary system
bss = ms.BSS()

# Define events (This version only supports repeated events)
A = bss.defvar('A')
B = bss.defvar('B')
C = bss.defvar('C')

# Make a system
top = bss.kofn(2, [A, B, C]) # k-of-n gate

# Convert the ZDD representation to a list of sets
path = bss.getbdd(top).extract()
print('All paths which is to be one')
for x in path:
    print(x)

# Obtain the minimal path vectors
s = bss.minpath(top)

# Convert the ZDD representation to a list of sets
min_path = s.extract()
print('The number of minimal path vectors:', len(min_path))
for x in min_path:
    print(x)

## An example of the direct use of MDD
bdd = ms.BDD()

# Define events (This version only supports repeated events)
A = bdd.defvar('A')
B = bdd.defvar('B')
C = bdd.defvar('C')

# Make a system
top = bdd.kofn(2, [A, B, C]) # k-of-n gate

# Convert the ZDD representation to a list of sets
path = top.extract()
print('All paths which is to be one')
for x in path:
    print(x)

# Obtain the minimal path vectors
s = top.minpath()

# Convert the ZDD representation to a list of sets
min_path = s.extract()
print('The number of minimal path vectors:', len(min_path))
for x in min_path:
    print(x)
