= Accumulator (safety injection tank) transient injection
= Tank: 3.0 MPa, 300 K subcooled water (N2-pressurized), pure liquid
= Surge line: horizontal pipe, 5 volumes, discharges to 0.5 MPa boundary
= Transient 2 s; report injected mass and tank pressure history
*
* --- control cards ---
100 new transnt
102 si si
201 2.0 1.0e-6 0.02 3 1 1 1
*
* --- accumulator tank: single volume, 3.0 MPa, 300 K ---
1100000 tank snglvol
1100101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1100200 3 3.0e6 300.0
*
* --- surge line: horizontal pipe, 5 volumes ---
1200000 surge pipe
1200001 5
1200101 0.005 1
1200102 0.005 2
1200103 0.005 3
1200104 0.005 4
1200105 0.005 5
1200301 0.5 1
1200302 0.5 2
1200303 0.5 3
1200304 0.5 4
1200305 0.5 5
1200601 0.0 1
1200602 0.0 2
1200603 0.0 3
1200604 0.0 4
1200605 0.0 5
1200801 0.0 0.0798 1
1200802 0.0 0.0798 2
1200803 0.0 0.0798 3
1200804 0.0 0.0798 4
1200805 0.0 0.0798 5
1201001 0 1
1201002 0 2
1201003 0 3
1201004 0 4
1201005 0 5
1201101 0 1
1201102 0 2
1201103 0 3
1201104 0 4
1201201 3 3.0e6 300.0 0.0 0.0 0.0 1
1201202 3 3.0e6 300.0 0.0 0.0 0.0 2
1201203 3 3.0e6 300.0 0.0 0.0 0.0 3
1201204 3 3.0e6 300.0 0.0 0.0 0.0 4
1201205 3 3.0e6 300.0 0.0 0.0 0.0 5
1201300 1
1201301 0.0 0.0 0.0 1
1201302 0.0 0.0 0.0 2
1201303 0.0 0.0 0.0 3
1201304 0.0 0.0 0.0 4
*
* --- low pressure boundary: time dependent volume, 0.5 MPa ---
1300000 lpsys tmdpvol
1300101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1300200 3
1300201 0.0 5.0e5 300.0
*
* --- junction: tank to surge line ---
1400000 jtank sngljun
1400101 110010000 120000000 0.005 0.0 0.0 0
1400201 0 0.0 0.0 0.0
*
* --- junction: surge line to low pressure boundary ---
1500000 jout sngljun
1500101 120050000 130010000 0.005 0.0 0.0 0
1500201 0 0.0 0.0 0.0
.
