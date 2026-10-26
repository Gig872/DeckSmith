= TRIGGER VALVE TRANSIENT : 0.8 MPa WATER 300 K BLOWDOWN TO 0.4 MPa SINK
* ---------------------------------------------------------------
* Model layout (all horizontal, elevation = 0):
*   100 tmdpvol  UPSTRM : constant 0.8 MPa / 300 K source
*   110 snglvol  VOLMID : valve downstream node (initial 0.4 MPa / 300 K)
*   120 tmdpvol  DNSTRM : constant 0.4 MPa / 300 K sink
*   101 sngljun  JIN    : UPSTRM -> VOLMID
*   102 valve    JVALVE : VOLMID -> DNSTRM  (TRPVLV, closed until t=5 s)
*   trip 501 : time >= 5.0 s  -> opens the trigger valve
* ---------------------------------------------------------------
* Valve area 0.02 m2 is the FULL-OPEN area (CCC0101 W3).
* Trigger valve: trip false -> closed, trip true -> open.
* ---------------------------------------------------------------
100 new transnt
102 si si
*
* --- trips -----------------------------------------------------
501 time 0 gt null 0 5.0 n
*
* --- time step control -----------------------------------------
201 10.0 1.0-6 0.01 3 100 100 0
*
* --- upstream constant-pressure source : 0.8 MPa, 300 K --------
1000000 upstrm tmdpvol
1000101 0.02 1.0 0.02 0.0 0.0 0.0 0.0 0.16 0
1000200 3
1000201 0.0 8.0e5 300.0
*
* --- downstream node (valve outlet volume) ---------------------
1100000 volmid snglvol
1100101 0.02 1.0 0.02 0.0 0.0 0.0 0.0 0.16 0
1100200 3 4.0e5 300.0
*
* --- downstream constant-pressure sink : 0.4 MPa, 300 K --------
1200000 dnstrm tmdpvol
1200101 0.02 1.0 0.02 0.0 0.0 0.0 0.0 0.16 0
1200200 3
1200201 0.0 4.0e5 300.0
*
* --- junction : upstream source -> downstream node -------------
1010000 jin sngljun
1010101 100010000 110000000 0.02 0.0 0.0 0000000
1010201 1 0.0 0.0 0.0
*
* --- trigger valve : downstream node -> sink -------------------
1020000 jvalve valve
1020101 110010000 120000000 0.02 0.0 0.0 0000000
1020201 1 0.0 0.0 0.0
1020300 trpv
1020301 501
.
