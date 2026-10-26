= jet mixer steady state model
= drive water 1.0 MPa + suction water 0.9 MPa mix in mixer chamber (A=0.005 m2)
= then discharge to 0.5 MPa pressure boundary; water 300 K, single phase liquid
* 100 card: problem type = new steady state
100  new  stdy-st
* 102 card: si units
102  si  si
* 201 card: end time, min dt, max dt, dt option, minor edit, major edit, restart
201  100.0  1.0e-6  0.02  3  100  200  500
*
* ---------- drive water source, constant 1.0 MPa / 300 K ----------
1010000  drive  tmdpvol
1010101  10.0  10.0  0.0  0.0  0.0  0.0  0.0  3.568  0000
1010200  3
1010201  0.0  1.0e6  300.0
*
* ---------- suction water source, constant 0.9 MPa / 300 K ----------
2010000  suctn  tmdpvol
2010101  10.0  10.0  0.0  0.0  0.0  0.0  0.0  3.568  0000
2010200  3
2010201  0.0  0.9e6  300.0
*
* ---------- discharge boundary, constant 0.5 MPa / 300 K ----------
4010000  outbn  tmdpvol
4010101  10.0  10.0  0.0  0.0  0.0  0.0  0.0  3.568  0000
4010200  3
4010201  0.0  0.5e6  300.0
*
* ---------- jet mixer body, single volume, area 0.005 m2, length 0.1 m ----------
3100000  mixer  snglvol
3100101  0.005  0.1  0.0  0.0  0.0  0.0  0.0  0.0798  0000
3100200  3  0.72e6  300.0
*
* ---------- drive nozzle junction, area 0.002 m2, loss coefficient 1.0 ----------
1020000  djet  sngljun
1020101  101000000  310000000  0.002  1.0  1.0  0000
1020201  1  47.0  0.0  0.0
*
* ---------- suction junction, area 0.003 m2, loss coefficient 1.0 ----------
2020000  sjet  sngljun
2020101  201000000  310000000  0.003  1.0  1.0  0000
2020201  1  57.0  0.0  0.0
*
* ---------- discharge junction, area 0.005 m2, loss coefficient 1.0 ----------
4020000  dsch  sngljun
4020101  310010000  401000000  0.005  1.0  1.0  0000
4020201  1  104.0  0.0  0.0
.
