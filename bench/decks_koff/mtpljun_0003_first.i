= Branch (1-in 2-out) splitter, steady state
= Inlet source 1.5 MPa / 300 K water -> BRANCH -> two legs -> 0.3 MPa outlets
= Split junction areas 0.005 m2 each; symmetric legs (K=1)
*
100 new stdy-st
102 si si
201 10.0 1.0e-6 0.1 3 1 1 1
*
* --- inlet source boundary: 1.5 MPa, 300 K ---
1000000 inlet tmdpvol
1000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1000200 3
1000201 0.0 1.5e6 300.0
*
* --- branch volume: area 0.01 m2, length 0.2 m ---
1100000 branch branch
1100001 3
1100101 0.01 0.2 0.002 0.0 0.0 0.0 0.0 0.0 0
1100200 3 1.5e6 300.0
1100201 100000000 110000000 0.01 1.0 1.0 0
1100202 110000000 120000000 0.005 1.0 1.0 0
1100203 110000000 130000000 0.005 1.0 1.0 0
1100201 1 1.0 0.0 0.0
1100202 1 1.0 0.0 0.0
1100203 1 1.0 0.0 0.0
*
* --- leg A downstream volume: area 0.005 m2, length 0.2 m ---
1200000 legA snglvol
1200101 0.005 0.2 0.001 0.0 0.0 0.0 0.0 0.0 0
1200200 3 3.0e5 300.0
*
* --- leg B downstream volume: area 0.005 m2, length 0.2 m ---
1300000 legB snglvol
1300101 0.005 0.2 0.001 0.0 0.0 0.0 0.0 0.0 0
1300200 3 3.0e5 300.0
*
* --- outlet boundary A: 0.3 MPa, 300 K ---
1400000 outA tmdpvol
1400101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1400200 3
1400201 0.0 3.0e5 300.0
*
* --- outlet boundary B: 0.3 MPa, 300 K ---
1500000 outB tmdpvol
1500101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1500200 3
1500201 0.0 3.0e5 300.0
*
* --- leg A outlet junction: legA -> outA ---
1600000 outjunA sngljun
1600101 120000000 140010000 0.005 1.0 1.0 0
1600201 1 1.0 0.0 0.0
*
* --- leg B outlet junction: legB -> outB ---
1700000 outjunB sngljun
1700101 130000000 150010000 0.005 1.0 1.0 0
1700201 1 1.0 0.0 0.0
.
