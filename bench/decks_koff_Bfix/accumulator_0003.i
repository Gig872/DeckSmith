=  ACCUMULATOR INJECTION TRANSIENT  (2 s)
=  Tank: vertical pipe 100, 3.0 MPa / 300 K, N2 pad on top
=  Surge line: pipe 200, ID 0.15 m, L 10 m, horizontal
=  Downstream: tmdpvol 300 at 0.5 MPa (constant pressure sink)
*  Assumptions (defaults, changeable):
*   - tank water volume 40 m3, tank ID 2.0 m -> area 3.1416 m2, L 12.732 m
*   - initial liquid level 10.0 m (31.4 m3 water), gas pad 2.732 m
*   - N2 pad modelled as noncondensable NITROGEN (card 110) on top of
*     saturated steam; pad pressure 3.0 MPa, pad temperature 300 K
*   - surge line ID 0.15 m, L 10 m, horizontal, roughness 4.5e-5 m
*   - downstream sink 0.5 MPa, 300 K
*   - no heat transfer to walls (adiabatic)
*   - surge line initialised with liquid (not gas) to avoid a gas blowdown
*     start-up transient; the line fills with liquid from the tank
*   - tank is a plain vertical pipe: the liquid column is NOT held up by a
*     check valve, so the whole column (31.4 m3) drains through the line.
*     A real accumulator has a check valve at the tank outlet; here the
*     drain-down is limited only by the 2 s run time.
100  new transnt
102  si si
110  nitrogen
115  1.0
201  2.0  1.0e-6  0.01  3  100  1000  1
*
*  ---------------- tank (vertical pipe, 6 volumes) ----------------
1000000  tank  pipe
1000001  6
1000101  3.1416  1
1000102  3.1416  2
1000103  3.1416  3
1000104  3.1416  4
1000105  3.1416  5
1000106  3.1416  6
1000301  2.1220  1
1000302  2.1220  2
1000303  2.1220  3
1000304  2.1220  4
1000305  2.1220  5
1000306  2.1220  6
1000601  90.0  1
1000602  90.0  2
1000603  90.0  3
1000604  90.0  4
1000605  90.0  5
1000606  90.0  6
1000801  4.5e-5  2.0  1
1000802  4.5e-5  2.0  2
1000803  4.5e-5  2.0  3
1000804  4.5e-5  2.0  4
1000805  4.5e-5  2.0  5
1000806  4.5e-5  2.0  6
1001001  0  1
1001002  0  2
1001003  0  3
1001004  0  4
1001005  0  5
1001006  0  6
1001101  0  1
1001102  0  2
1001103  0  3
1001104  0  4
1001105  0  5
*  liquid volumes 1-4 : 3.0 MPa, 300 K subcooled liquid
1001201  3  3.0e6  300.0  0.0  0.0  0.0  1
1001202  3  3.0e6  300.0  0.0  0.0  0.0  2
1001203  3  3.0e6  300.0  0.0  0.0  0.0  3
1001204  3  3.0e6  300.0  0.0  0.0  0.0  4
*  gas pad volumes 5-6 : 3.0 MPa, 300 K nitrogen (t=4, quality 0)
1001205  4  3.0e6  300.0  0.0  0.0  0.0  5
1001206  4  3.0e6  300.0  0.0  0.0  0.0  6
1001300  1
1001301  0.0  0.0  0.0  1
1001302  0.0  0.0  0.0  2
1001303  0.0  0.0  0.0  3
1001304  0.0  0.0  0.0  4
1001305  0.0  0.0  0.0  5
*
*  ---------------- surge line (horizontal pipe, 4 volumes) ----------------
2000000  surge  pipe
2000001  4
2000101  0.017671  1
2000102  0.017671  2
2000103  0.017671  3
2000104  0.017671  4
2000301  2.5  1
2000302  2.5  2
2000303  2.5  3
2000304  2.5  4
2000601  0.0  1
2000602  0.0  2
2000603  0.0  3
2000604  0.0  4
2000801  4.5e-5  0.15  1
2000802  4.5e-5  0.15  2
2000803  4.5e-5  0.15  3
2000804  4.5e-5  0.15  4
2001001  0  1
2001002  0  2
2001003  0  3
2001004  0  4
2001101  0  1
2001102  0  2
2001103  0  3
2001201  3  3.0e6  300.0  0.0  0.0  0.0  1
2001202  3  3.0e6  300.0  0.0  0.0  0.0  2
2001203  3  3.0e6  300.0  0.0  0.0  0.0  3
2001204  3  3.0e6  300.0  0.0  0.0  0.0  4
2001300  1
2001301  0.0  0.0  0.0  1
2001302  0.0  0.0  0.0  2
2001303  0.0  0.0  0.0  3
*
*  ---------------- downstream constant pressure sink ----------------
3000000  sink  tmdpvol
3000101  1.0  1.0  1.0  0.0  0.0  0.0  1.0e-5  1.0  0
3000200  3
3000201  0.0  0.5e6  300.0
*
*  ---------------- junctions ----------------
*  tank bottom -> surge line inlet
1500000  tankout  sngljun
1500101  100010000  200000000  0.017671  0.5  0.5  0
1500201  1  0.0  0.0  0.0
*  surge line outlet -> sink
2500000  sinkin  sngljun
2500101  200010000  300010000  0.017671  0.5  0.5  0
2500201  1  0.0  0.0  0.0
.
