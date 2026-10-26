= JET MIXER STEADY STATE : DRIVE 1.0 MPa + SUCTION 0.8 MPa -> DISCHARGE 0.5 MPa
* RELAP5 steady-state model of a jet mixer (JETMIXER component, 3 junctions)
* N=1 drive junction    : from 1.0 MPa constant-pressure source (tmdpvol 100)
* N=2 suction junction  : from 0.8 MPa constant-pressure source (tmdpvol 110)
* N=3 discharge junction: to 0.5 MPa constant-pressure sink (tmdpvol 120)
* Mixer flow area 0.005 m2, length 0.5 m, horizontal, single-phase liquid water 300 K
* No heat source: energy in = energy out, all three streams at 300 K
* Flow is driven by pressure difference only; junction loss coefficients set the flow
*   drive K=1.0, suction K=1.0, discharge K=2.0
* Units: SI
100 new stdy-st
102 si si
201 100.0 1.0e-6 0.01 3 10 100 1000
*
* ---------------------------------------------------------------- boundaries
* drive source : 1.0 MPa, 300 K
1000000 drive tmdpvol
1000101 0.005 0.5 0.0 0.0 0.0 0.0 0.0 0.0798 0
1000200 3
1000201 0.0 1.0e6 300.0
*
* suction source : 0.8 MPa, 300 K
1100000 suction tmdpvol
1100101 0.005 0.5 0.0 0.0 0.0 0.0 0.0 0.0798 0
1100200 3
1100201 0.0 8.0e5 300.0
*
* discharge sink : 0.5 MPa, 300 K
1200000 sink tmdpvol
1200101 0.005 0.5 0.0 0.0 0.0 0.0 0.0 0.0798 0
1200200 3
1200201 0.0 5.0e5 300.0
*
* ---------------------------------------------------------------- jet mixer
* JETMIXER : junction 1 = drive, junction 2 = suction, junction 3 = discharge
2000000 mixer jetmixer
2000001 3
2000101 0.005 0.5 0.0025 0.0 0.0 0.0 0.0 0.0798 0
2000200 3 1.0e6 300.0
* junction 1 : drive, enters mixer inlet side
2001101 100010000 200000000 0.005 1.0 1.0 0
* junction 2 : suction, enters mixer inlet side
2001102 110010000 200000000 0.005 1.0 1.0 0
* junction 3 : discharge, leaves mixer outlet side
2001103 200010000 120000000 0.005 2.0 2.0 0
* initial junction velocities (liquid, vapour)
2001201 5.0 0.0
2001202 5.0 0.0
2001203 10.0 0.0
.
