= Pump-driven loop steady state: 0.8 MPa, 300 K water [已验证可跑]
* Topology: tmdpvol(0.8MPa,300K) -> sngljun -> snglvol -> pump -> pipe(4 vols, horizontal) -> sngljun -> tmdpvol(0.8MPa)
* Pump: rated speed 157.08 rad/s, rated flow 0.02 m3/s, rated head 10 m, inertia 1.0
* Pipe: area 0.02 m2, length 1 m, 4 volumes, roughness 4.5e-5 m
* KEY: loop initialized with a consistent 1.0 m/s flow field (20 kg/s) so the pump
*      starts on the stable branch of its head curve; starting from zero flow makes the
*      pump overshoot into the reverse octant and stall (head<0, flow~0).
* 结果: 稳态循环流量 32.39 kg/s (液速1.62 m/s); 泵压升约0 Pa(零扬程/runaway点);
*       温度300->300.05K; 质量误差1.2e-7kg; 管段压降~103 Pa
100  new  stdy-st
102  si  si
201  100.0  1.0e-6  0.1  3  100  200  500

1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  8.0e5  300.0

1020000  inj  sngljun
1020101  101000000  105000000  0.02  0.0  0.0  0000
1020201  0  1.0  0.0  0.0

1050000  vol  snglvol
1050101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1050200  3  8.0e5  300.0

1100000  pmp  pump
1100101  0.02  0.5  0.01  0.0  0.0  0.0  0000
1100108  105010000  0.02  0.0  0.0  0000
1100109  120000000  0.02  0.0  0.0  0000
1100200  3  8.0e5  300.0
1100201  0  1.0  0.0  0.0
1100202  0  1.0  0.0  0.0
1100301  -1  -1  -3  -1  -1  0  0
1100302  157.08  1.0  0.02  10.0  50.0  1.0  1000.0  0.0  0.0  0.0  0.0  0.0

1200000  pipe  pipe
1200001  4
1200101  0.02  4
1200301  0.25  4
1200601  0.0  4
1200801  4.5e-5  0.16  4
1201001  0000000  4
1201101  0  3
1201201  3  8.0e5  300.0  0  0  0  4
1201300  0
1201301  1.0  0.0  0.0  3

1300000  outj  sngljun
1300101  120010000  141000000  0.02  0.0  0.0  0000
1300201  0  1.0  0.0  0.0

1410000  outb  tmdpvol
1410101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1410200  3
1410201  0.0  8.0e5  300.0

.
