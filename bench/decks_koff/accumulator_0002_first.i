= Accumulator injection transient
= Tank: 3.0 MPa, 300 K nitrogen-pressurized water (liquid + N2 gas pad)
= Surge line: horizontal pipe discharging to 0.3 MPa boundary
= Transient duration 2 s
*
* --- control cards ---
100 new transnt
102 si si
201 2.0 1.0e-6 0.01 3 1 1 1
*
* --- accumulator tank: vertical pipe, 2 volumes (1=liquid, 2=gas pad) ---
1100000 tank pipe
1100001 2
1100101 0.5 1
1100102 0.5 2
1100301 1.0 1
1100302 1.0 2
1100601 90.0 1
1100602 90.0 2
1100801 0.0 0.8 1
1100802 0.0 0.8 2
1101001 0 1
1101002 0 2
1101101 0 1
1101201 3 3.0e6 300.0 0.0 0.0 0.0 1
1101202 3 3.0e6 300.0 0.0 0.0 0.0 2
1101300 1
1101301 0.0 0.0 0.0 1
*
* --- surge line: horizontal pipe, 3 volumes ---
1200000 surge pipe
1200001 3
1200101 0.01 1
1200102 0.01 2
1200103 0.01 3
1200301 1.0 1
1200302 1.0 2
1200303 1.0 3
1200601 0.0 1
1200602 0.0 2
1200603 0.0 3
1200801 0.0 0.113 1
1200802 0.0 0.113 2
1200803 0.0 0.113 3
1201001 0 1
1201002 0 2
1201003 0 3
1201101 0 1
1201102 0 2
1201201 3 3.0e6 300.0 0.0 0.0 0.0 1
1201202 3 3.0e6 300.0 0.0 0.0 0.0 2
1201203 3 3.0e6 300.0 0.0 0.0 0.0 3
1201300 1
1201301 0.0 0.0 0.0 1
1201302 0.0 0.0 0.0 2
*
* --- tank bottom to surge line inlet ---
1300000 t2s sngljun
1300101 110010000 120000000 0.01 0.0 0.0 0
1300201 0 0.0 0.0 0.0
*
* --- surge line outlet to low pressure boundary ---
1400000 outlet tmdpvol
1400101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1400200 3
1400201 0.0 3.0e5 300.0
*
* --- surge line outlet junction to boundary ---
1500000 s2o sngljun
1500101 120030000 140010000 0.01 0.0 0.0 0
1500201 0 0.0 0.0 0.0
.
