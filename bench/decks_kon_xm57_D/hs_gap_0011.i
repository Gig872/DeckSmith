= FUEL ROD 3-LAYER HS + SINGLE CHANNEL, STEADY STATE, NP = 8 (MESH CHECK)
* same model as fr50.i but radial mesh refined: 4 intervals in fuel, 2 in clad
* purpose: node-independence check of the fuel centre / clad surface temperatures
100  new  stdy-st
102  si  si
201  300.0  1.0e-6  0.02  3  100  200  500

*---- inlet source volume (15.5 MPa, 560 K) ----
1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  1.55e7  560.0

*---- inlet junction, control word 1 = mass flow 0.3 kg/s ----
1020000  inj  tmdpjun
1020101  101000000  110000000  1.0e-4
1020200  1
1020201  0.0  0.3  0.0  0.0

*---- coolant channel, single volume, vertical, A = 1.0e-4 m2, L = 1.0 m ----
1100000  chan  pipe
1100001  1
1100101  1.0e-4  1
1100301  1.0  1
1100601  90.0  1
1100801  4.5e-5  0.0113  1
1101001  0000000  1
1101201  3  1.55e7  560.0  0  0  0  1

*---- outlet junction, control word 0 = free, flow from momentum equation ----
1200000  outj  sngljun
1200101  110010000  151000000  1.0e-4  0.0  0.0  0000
1200201  0  0.0  0.0  0.0

*---- outlet sink volume (15.5 MPa, 560 K) ----
1510000  ob  tmdpvol
1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1510200  3
1510201  0.0  1.55e7  560.0

*==== heat structure 110 / geometry 1 : fuel rod, cylindrical, NP = 8 ====
11101000  1  8  2  0  0.0  0  0  4
* gap conductance model: initial gap pressure 0.5e6 Pa, reference volume 110-01
11101001  0.5e6  110010000
* gap deformation data: fuel rough, clad rough, fuel disp, clad creep, HS no.
11101011  1.0e-6  2.0e-6  0.0  0.0  1
* mesh flag: W1=0 local mesh data, W2=1 format 1 (n intervals, right coordinate m)
11101100  0  1
11101101  4  0.004
11101102  1  0.0041
11101103  2  0.0047
* composition: intervals 1-4 UO2 (1), interval 5 He gap (2), intervals 6-7 Zr (3)
11101201  1  1
11101202  1  2
11101203  1  3
11101204  1  4
11101205  2  5
11101206  3  6
11101207  3  7
* relative radial power distribution: uniform inside fuel only
11101301  1.0  1
11101302  1.0  2
11101303  1.0  3
11101304  1.0  4
11101305  0.0  5
11101306  0.0  6
11101307  0.0  7
* initial temperature distribution, K
11101400  0
11101401  2400.0  1
11101402  2250.0  2
11101403  1950.0  3
11101404  1500.0  4
11101405  920.0  5
11101406  700.0  6
11101407  660.0  7
11101408  630.0  8
* left boundary: r = 0, adiabatic (axis of symmetry)
11101501  0  0  0  0  0.0  1
* right boundary: convective, volume 110010000, cylinder height 1.0 m
11101601  110010000  0  1  1  1.0  1
* heat source: type 1 = power table 1, multiplier 1.0, HS no.
11101701  1  1.0  0.0  0.0  1
* additional left / right boundary data
11101801  0.0113  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1
11101901  0.0113  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1

*==== materials ====
20100100  uo2
20100200  tbl/fctn  3  1
20100201  helium  1.0
20100251  300.0  4.0e3
20100252  1500.0  2.5e3
20100300  zr

*==== total fission power table: 50 kW constant ====
20200100  power
20200101  0.0  5.0e4
20200102  300.0  5.0e4
.
