= LOF transient: pump-driven heated channel (1.0 MPa, 300 K water)
* Purpose: a centrifugal pump drives water through a heated horizontal pipe.
*   The plant runs at steady state until t = 2 s, then the pump motor torque
*   is tripped off; the rotor coasts down on its own inertia and the flow
*   decays (loss of flow, LOF). Transient is run for 150 s.
* Topology: tmdpvol(1.0e6 Pa,300 K) -> sngljun -> snglvol(suction)
*           -> pump -> pipe(4 volumes, heat structure 100 kW)
*           -> sngljun -> tmdpvol(1.0e6 Pa,300 K)
* Pump: rated speed 157.08 rad/s, rated head 20 m, inertia 0.2 kg m2,
*       rated volumetric flow 0.02 m3/s (default, not given by user),
*       rated torque 50 N-m, rated density 1000 kg/m3.
* Heated pipe: A = 0.02 m2, L = 1 m (4 x 0.25 m), roughness 4.5e-5 m,
*       hydraulic diameter 0.16 m, uniform 100 kW total power.
* Initial state: steady state of this loop at rated pump speed, obtained by a
*   pre-run with the pump never tripped: mdot = 32.4 kg/s everywhere,
*   liquid velocity 1.625 m/s, P = 1.0e6 Pa, T = 300 K (all junction
*   initial conditions below are set to this steady flow).
* Trip 401: time 0 gt null 0 2.0 n  => true for t > 2 s => motor torque off,
*   from then on the pump speed follows the torque-inertia equation.
100  new  transnt
102  si  si
201  150.0  1.0e-6  0.01  3  100  200  500

* --- inlet pressure/temperature boundary (source) ---
1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  1.0e6  300.0

* --- source to suction volume junction (initial 32.4 kg/s) ---
1020000  inj  sngljun
1020101  101000000  105000000  0.02  0.0  0.0  0000
1020201  1  32.4  0.0  0.0

* --- pump suction volume ---
1050000  vol  snglvol
1050101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1050200  3  1.0e6  300.0

* --- pump: one volume + suction/discharge junctions ---
1100000  pmp  pump
1100101  0.02  0.5  0.01  0.0  0.0  0.0  0000
1100108  105010000  0.02  0.0  0.0  0000
1100109  120000000  0.02  0.0  0.0  0000
1100200  3  1.0e6  300.0
1100201  1  32.4  0.0  0.0
1100202  1  32.4  0.0  0.0
* pump flags: single-phase table = Bingham built-in (-1), no two-phase (-1),
*   no two-phase difference table (-3), no motor torque table (-1),
*   no speed table (-1), pump trip = 401, no reverse flow allowed (0)
1100301  -1  -1  -3  -1  -1  401  0
* rated speed, initial speed ratio, rated volumetric flow, rated head,
*   rated torque, inertia, rated density, rated motor torque, TF2 TF0 TF1 TD3
1100302  157.08  1.0  0.02  20.0  50.0  0.2  1000.0  0.0  0.0  0.0  0.0  0.0

* --- heated horizontal pipe, 4 control volumes ---
1200000  pipe  pipe
1200001  4
1200101  0.02  4
1200301  0.25  4
1200601  0.0  4
1200801  4.5e-5  0.16  4
1201001  0000000  4
1201101  0  3
1201201  3  1.0e6  300.0  0  0  0  4
1201300  1
1201301  32.4  0.0  0.0  3

* --- pipe outlet to outlet boundary ---
1300000  outj  sngljun
1300101  120010000  141000000  0.02  0.0  0.0  0000
1300201  1  32.4  0.0  0.0

* --- outlet pressure boundary (sink) ---
1410000  outb  tmdpvol
1410101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1410200  3
1410201  0.0  1.0e6  300.0

* --- heat structure 112: wall around the 4 pipe volumes, 100 kW total ---
11201000  4  2  1  0  0.0  0  0  4
11201100  0  1
11201101  1  0.005
11201201  1  1
11201301  1.0  1
11201400  0
11201401  300.0  1
11201402  300.0  2
11201501  120010000  0  1  0  0.0886  1
11201502  120020000  0  1  0  0.0886  2
11201503  120030000  0  1  0  0.0886  3
11201504  120040000  0  1  0  0.0886  4
11201601  0  0  0  0  0.0886  1
11201602  0  0  0  0  0.0886  2
11201603  0  0  0  0  0.0886  3
11201604  0  0  0  0  0.0886  4
11201701  1  0.25  0.0  0.0  1
11201702  1  0.25  0.0  0.0  2
11201703  1  0.25  0.0  0.0  3
11201704  1  0.25  0.0  0.0  4
11201801  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1
11201802  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  2
11201803  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  3
11201804  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  4

* --- total heating power 100 kW, constant in time ---
20200100  power
20200101  0.0  1.0e5
20200102  100.0  1.0e5

* --- heat structure material ---
20100100  s-steel

* --- trip 401: true for t > 2.0 s (pump motor torque cut off) ---
401  time  0  gt  null  0  2.0  n
.
