= PWR SBLOCA DEPRESSURIZATION - SINGLE VOLUME + BREAK TO CONTAINMENT
= Vessel: 0.2 m3, 15 MPa, 600 K subcooled. Break opens at t=5 s, 2.0 cm2, to 0.1 MPa/300 K.
* ---------------------------------------------------------------
* Problem control
* ---------------------------------------------------------------
100 new transnt
101 run
102 si si
*
* ---------------------------------------------------------------
* Time step control: 30 s transient, dt max 0.005 s
* ---------------------------------------------------------------
201 30.0 1.0e-6 0.005 3 100 1000 1000
*
* ---------------------------------------------------------------
* Component 100 : primary system (single volume, 0.2 m3)
*   area 1.0 m2 x length 0.2 m = 0.2 m3, horizontal, no elevation
* ---------------------------------------------------------------
1000000 pvessel snglvol
1000101 1.0 0.2 0.2 0.0 0.0 0.0 0.0 1.0 0
* control code 3 = pressure + temperature (single phase, subcooled)
1000200 3
1000201 15.0e6 600.0
*
* ---------------------------------------------------------------
* Component 200 : containment (time dependent volume, sink)
*   0.1 MPa, 300 K, large volume
* ---------------------------------------------------------------
2000000 contain tmdpvol
2000101 100.0 10.0 1000.0 0.0 0.0 0.0 0.0 10.0 0
2000200 3
2000201 0.0 0.1e6 300.0
*
* ---------------------------------------------------------------
* Component 300 : break (time dependent junction, 2.0 cm2)
*   from vessel outlet (100010000) to containment (200010000)
*   control code 1 = mass flow rate; 0 until 5 s, then critical flow
* ---------------------------------------------------------------
3000000 break tmdpjun
3000101 100010000 200010000 2.0e-4
3000200 1
3000201 0.0 0.0 0.0 0.0
3000202 5.0 0.0 0.0 0.0
3000203 5.0001 1.0e6 1.0e6 0.0
3000204 30.0 1.0e6 1.0e6 0.0
*
.end
