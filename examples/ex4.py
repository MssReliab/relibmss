## This is an example of a large fault tree
## Computational time may be long (about 1 minute)

import relibmss as ms

bss = ms.BSS()
c = [bss.defvar("c" + str(i)) for i in range(61)]

g62 = c[0] & c[1]
g63 = c[0] & c[2]
g64 = c[0] & c[3]
g65 = c[0] & c[4]
g66 = c[0] & c[5]
g67 = c[0] & c[6]
g68 = c[0] & c[7]
g69 = c[0] & c[8]
g70 = g62 | c[9]
g71 = g63 | c[10]
g72 = g64 | c[11]
g73 = g65 | c[12]
g74 = g62 | c[13]
g75 = g63 | c[14]
g76 = g64 | c[15]
g77 = g65 | c[16]
g78 = g62 | c[17]
g79 = g63 | c[18]
g80 = g64 | c[19]
g81 = g65 | c[20]
g82 = g62 | c[21]
g83 = g63 | c[22]
g84 = g64 | c[23]
g85 = g65 | c[24]
g86 = g62 | c[25]
g87 = g63 | c[26]
g88 = g64 | c[27]
g89 = g65 | c[28]
g90 = g66 | c[29]
g91 = g68 | c[30]
g92 = g67 | c[31]
g93 = g69 | c[32]
g94 = g66 | c[33]
g95 = g68 | c[34]
g96 = g67 | c[35]
g97 = g69 | c[36]
g98 = g66 | c[37]
g99 = g68 | c[38]
g100 = g67 | c[39]
g101 = g69 | c[40]
g102 = g66 | c[41]
g103 = g68 | c[42]
g104 = g67 | c[43]
g105 = g69 | c[44]
g106 = bss.kofn(3, [g70, g71, g72, g73])
g107 = bss.kofn(3, [g74, g75, g76, g77])
g108 = bss.kofn(3, [g78, g79, g80, g81])
g109 = bss.kofn(3, [g82, g83, g84, g85])
g110 = bss.kofn(3, [g86, g87, g88, g89])
g111 = bss.kofn(3, [g94, g95, g96, g97])
g112 = bss.kofn(3, [g98, g99, g100, g101])
g113 = g90 & g92
g114 = g91 & g93
g115 = g102 & g104
g116 = g103 & g105
g117 = g113 | c[45]
g118 = g114 | c[46]
g119 = g107 | g108 | c[51]
g120 = g109 | g110
g121 = g66 | g117 | c[47]
g122 = g68 | g118 | c[48]
g123 = g67 | g117 | c[49]
g124 = g69 | g118 | c[50]
g125 = bss.kofn(2, [g121, g123, g122, g124])
g126 = g111 | g112 | g125 | c[52]
g127 = g115 & g120
g128 = g116 & g120
g129 = g62 | g127 | c[53]
g130 = g63 | g128 | c[54]
g131 = g64 | g127 | c[55]
g132 = g65 | g128 | c[56]
g133 = g62 | g129 | c[57]
g134 = g63 | g130 | c[58]
g135 = g64 | g131 | c[59]
g136 = g65 | g132 | c[60]
g137 = bss.kofn(3, [g133, g134, g135, g136])
g138 = g106 | g119 | g137
g139 = g62 | g66 | g117 | g129 | c[47]
g140 = g63 | g68 | g118 | g130 | c[48]
g141 = g64 | g67 | g117 | g131 | c[49]
g142 = g65 | g69 | g118 | g132 | c[50]
g143 = g139 & g140 & g141 & g142
g144 = g111 | g112 | g143 | c[52]
top = g126 & g138 & g144

bdd = bss.getbdd(top)
print(bdd.size()) # The number of nodes in the BDD

s = bdd.minpath() # Fault tree: minpath() gives the system's minimal cut sets
min_cut = s.extract()
print('The number of minimal cut sets:', len(min_cut))

print('Example: 100 minimal cut sets')
from itertools import islice
for x in islice(min_cut, 0, 100):
    print(x)

## An example of the direct use of MDD

vars = bss.get_varorder()

bdd = ms.BDD(vars) # Create a BDD with the variable order
c = [bdd.defvar("c" + str(i)) for i in range(61)]

g62 = c[0] & c[1]
g63 = c[0] & c[2]
g64 = c[0] & c[3]
g65 = c[0] & c[4]
g66 = c[0] & c[5]
g67 = c[0] & c[6]
g68 = c[0] & c[7]
g69 = c[0] & c[8]
g70 = g62 | c[9]
g71 = g63 | c[10]
g72 = g64 | c[11]
g73 = g65 | c[12]
g74 = g62 | c[13]
g75 = g63 | c[14]
g76 = g64 | c[15]
g77 = g65 | c[16]
g78 = g62 | c[17]
g79 = g63 | c[18]
g80 = g64 | c[19]
g81 = g65 | c[20]
g82 = g62 | c[21]
g83 = g63 | c[22]
g84 = g64 | c[23]
g85 = g65 | c[24]
g86 = g62 | c[25]
g87 = g63 | c[26]
g88 = g64 | c[27]
g89 = g65 | c[28]
g90 = g66 | c[29]
g91 = g68 | c[30]
g92 = g67 | c[31]
g93 = g69 | c[32]
g94 = g66 | c[33]
g95 = g68 | c[34]
g96 = g67 | c[35]
g97 = g69 | c[36]
g98 = g66 | c[37]
g99 = g68 | c[38]
g100 = g67 | c[39]
g101 = g69 | c[40]
g102 = g66 | c[41]
g103 = g68 | c[42]
g104 = g67 | c[43]
g105 = g69 | c[44]
g106 = bdd.kofn(3, [g70, g71, g72, g73])
g107 = bdd.kofn(3, [g74, g75, g76, g77])
g108 = bdd.kofn(3, [g78, g79, g80, g81])
g109 = bdd.kofn(3, [g82, g83, g84, g85])
g110 = bdd.kofn(3, [g86, g87, g88, g89])
g111 = bdd.kofn(3, [g94, g95, g96, g97])
g112 = bdd.kofn(3, [g98, g99, g100, g101])
g113 = g90 & g92
g114 = g91 & g93
g115 = g102 & g104
g116 = g103 & g105
g117 = g113 | c[45]
g118 = g114 | c[46]
g119 = g107 | g108 | c[51]
g120 = g109 | g110
g121 = g66 | g117 | c[47]
g122 = g68 | g118 | c[48]
g123 = g67 | g117 | c[49]
g124 = g69 | g118 | c[50]
g125 = bdd.kofn(2, [g121, g123, g122, g124])
g126 = g111 | g112 | g125 | c[52]
g127 = g115 & g120
g128 = g116 & g120
g129 = g62 | g127 | c[53]
g130 = g63 | g128 | c[54]
g131 = g64 | g127 | c[55]
g132 = g65 | g128 | c[56]
g133 = g62 | g129 | c[57]
g134 = g63 | g130 | c[58]
g135 = g64 | g131 | c[59]
g136 = g65 | g132 | c[60]
g137 = bdd.kofn(3, [g133, g134, g135, g136])
g138 = g106 | g119 | g137
g139 = g62 | g66 | g117 | g129 | c[47]
g140 = g63 | g68 | g118 | g130 | c[48]
g141 = g64 | g67 | g117 | g131 | c[49]
g142 = g65 | g69 | g118 | g132 | c[50]
g143 = g139 & g140 & g141 & g142
g144 = g111 | g112 | g143 | c[52]
top = g126 & g138 & g144

print(top.size()) # The number of nodes in the BDD

s = top.minpath() # Fault tree: minpath() gives the system's minimal cut sets
min_cut = s.extract()
print('The number of minimal cut sets:', len(min_cut))

print('Example: 100 minimal cut sets')
from itertools import islice
for x in islice(min_cut, 0, 100):
    print(x)

