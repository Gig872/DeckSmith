= PWR accumulator (SI) injection transient
= Tank: 3.0 MPa, 300 K nitrogen-pressurized water
= Surge line injects into 0.1 MPa low-pressure horizontal pipe
= Transient duration 2 s
*
* --- control cards ---
100 new transnt
102 si si
201 2.0 1.0e-6 0.01 3 1 1 1
*
* --- noncondensable gas: nitrogen (required for accumulator) ---
110 nitrogen
*
* --- accumulator tank ---
1200000 accum accum
1200101 10.0 3.0 30.0 0.0 90.0 3.0 0.0 1.0 0
1200200 3.0e6 300.0 0.0
1201101 130000000 0.002 0.0 0.0 0
1202200 20.0 2.0 1.0 1.0 0.05 1 0.0 0.0 0
*
* --- low pressure horizontal pipe (downstream system) ---
1300000 lppipe pipe
1300001 3
1300101 0.002 1
1300102 0.002 2
1300103 0.002 3
1300301 1.0 1
1300302 1.0 2
1300303 1.0 3
1300601 0.0 1
1300602 0.0 2
1300603 0.0 3
1300801 0.0 0.1 1
1300802 0.0 0.1 2
1300803 0.0 0.1 3
1301001 0 1
1301002 0 2
1301003 0 3
1301101 0 1
1301102 0 2
1301201 3 1.0e5 300.0 0 0 0 1
1301202 3 1.0e5 300.0 0 0 0 2
1301203 3 1.0e5 300.0 0 0 0 3
1301300 0
1301301 0.0 0.0 0.0 1
1301302 0.0 0.0 0.0 2
*
* --- outlet boundary: constant 0.1 MPa ---
1400000 outlet tmdpvol
1400101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1400200 3
1400201 0.0 1.0e5 300.0
*
* --- connect pipe outlet to boundary ---
1500000 outjun sngljun
1500101 130010000 140010000 0.002 0.0 0.0 0
1500201 0 0.0 0.0 0.0
.
