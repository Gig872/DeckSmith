= JET MIXER STEADY STATE MODEL - SINGLE PHASE LIQUID WATER
* Jet mixer (JETMIXER branch, 3 junctions):
*   N=1 drive  inlet : from TMDPVOL 100 at 1.0 MPa / 300 K
*   N=2 suction inlet: from TMDPVOL 110 at 0.8 MPa / 300 K
*   N=3 discharge    : to   TMDPVOL 120 at 0.5 MPa / 300 K
* Mixer flow area 0.005 m2, length 0.5 m, horizontal, Dh = 0.0798 m
* Purpose: steady state flow split (drive flow / suction flow)
* Units: SI
100 new stdy-st
102 si si
*
* --- time step control (steady state run) ---
201 100.0 1.0e-6 0.1 3 100 1000 0
*
* ================= boundary volumes =================
*
* drive source : 1.0 MPa, 300 K
1000000 drive-source
1000101 0.005 0.5 0.0025 0.0 0.0 0.0 0.0 0.0798 0
1000200 3
1000201 0.0 1.0e6 300.0
*
* suction source : 0.8 MPa, 300 K
1100000 suction-source
1100101 0.005 0.5 0.0025 0.0 0.0 0.0 0.0 0.0798 0
1100200 3
1100201 0.0 8.0e5 300.0
*
* discharge sink : 0.5 MPa, 300 K
1200000 discharge-sink
1200101 0.005 0.5 0.0025 0.0 0.0 0.0 0.0 0.0798 0
1200200 3
1200201 0.0 5.0e5 300.0
*
* ================= jet mixer =================
*
3000000 mixer
3000100 3
3000101 0.005 0.5 0.0025 0.0 0.0 0.0 0.0 0.0798 0
3000200 3
3000201 0.0 5.0e5 300.0
*
* junction 1 : drive inlet  (from drive source outlet)
3000101 100010000 300000000 0.005 1.0 1.0 0
* junction 2 : suction inlet (from suction source outlet)
3000201 110010000 300000000 0.005 1.0 1.0 0
* junction 3 : discharge (to sink inlet)
3000301 300010000 120000000 0.005 1.0 1.0 0
*
* initial junction velocities (m/s)
3001201 0.0 0.0
3002201 0.0 0.0
3003201 0.0 0.0
.
