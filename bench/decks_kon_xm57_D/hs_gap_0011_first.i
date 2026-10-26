= FUEL ROD 3-LAYER HEAT STRUCTURE + SINGLE CHANNEL, STEADY STATE
* scenario : one cylindrical PWR fuel rod coupled to one coolant volume
*            fuel r=0-4.0 mm / He gap 4.0-4.1 mm / clad 4.1-4.7 mm, L = 1.0 m
* coolant  : subcooled water 15.5 MPa 560 K, 0.3 kg/s, one hydraulic volume
* energy   : 50 kW uniform fission power in fuel -> conduction -> gap (He 0.5 MPa)
*            -> clad -> convective film to coolant; steady state, 50 kW leaves with water
* drive    : inlet tmdpjun fixed 0.3 kg/s, outlet free junction to 15.5 MPa sink
* design   : A_chan = 1.0e-4 m2, Dh = 0.0113 m, v ~ 4.2 m/s, Re ~ 3e5
* units SI, end time 300 s (fuel thermal time constant ~ 20 s, ~14 time constants)
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

*---- gap reference volume for the gap conductance model (0.5 MPa, 560 K) ----
1550000  gapref  tmdpvol
1550101  0.001  0.1  0.0  0.0  0.0  0.0  0.0  0.03  0000
1550200  3
1550201  0.0  0.5e6  560.0

*==== heat structure 110 / geometry 1 : fuel rod, cylindrical, NP = 6 ====
* NH=1 NP=6 cylindrical steady-init=0 leftcoord=0 no-reflood 0 max-axial=4
11101000  1  6  2  0  0.0  0  0  4
* gap conductance model: initial gap pressure 0.5e6 Pa, reference volume
11101001  0.5e6  155010000
* gap deformation data: fuel rough, clad rough, fuel disp, clad creep, HS no.
11101011  1.0e-6  2.0e-6  0.0  0.0  1
* mesh flag: W1=0 local mesh data, W2=1 format 1 (n intervals, right coordinate m)
11101100  0  1
11101101  2  0.004
11101102  1  0.0041
11101103  2  0.0047
* composition: intervals 1-2 UO2 (1), interval 3 He gap (2), intervals 4-5 Zr (3)
11101201  1  1
11101202  1  2
11101203  2  3
11101204  3  4
11101205  3  5
* relative radial power distribution: uniform inside fuel only
11101301  1.0  1
11101302  1.0  2
11101303  0.0  3
11101304  0.0  4
11101305  0.0  5
* initial temperature distribution (first guess of the steady profile), K
11101400  0
11101401  2400.0  1
11101402  2000.0  2
11101403  900.0  3
11101404  760.0  4
11101405  660.0  5
11101406  630.0  6
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
* UO2 fuel, built-in properties
20100100  uo2
* helium gap gas: W2=3 gap conduction model, W3=1 tabulated volumetric heat capacity
20100200  tbl/fctn  3  1
20100201  helium  1.0
20100251  300.0  4.0e3
20100252  1500.0  2.5e3
* zirconium cladding, built-in properties
20100300  zr

*==== total fission power table: 50 kW constant ====
20200100  power
20200101  0.0  5.0e4
20200102  300.0  5.0e4
.
