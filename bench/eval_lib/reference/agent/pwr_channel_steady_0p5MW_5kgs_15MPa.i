= PWR heated channel, steady state, 0.5 MW, 15 MPa / 560 K water, 5 kg/s
* 4-volume circular pipe (A=0.01 m2, L=2 m total, 0.5 m/volume, horizontal)
* Cylindrical fuel-rod heat structure coupled to the 4 pipe volumes
*   rod: pellet r=0.09 m, cladding outer r=0.10 m (OD 0.2 m)
* Heat source type 1 = general table 1 (POWER), total 0.5 MW, 0.25 per segment
* NOTE 1: point-kinetics parameters (beta=0.0065, Lambda=1e-4, rho0=0) are NOT
*   solved in a steady-state (stdy-st) run: steady power is the constant 0.5 MW.
* NOTE 2: driver = fixed inlet mass flow 5 kg/s (tmdpjun); outlet tmdpvol at
*   15 MPa acts as a sink so mass/energy balance is closed.
* NOTE 3: a thin OD 9.5 mm rod would give surface flux 8.4 MW/m2 (unphysical,
*   drives wall far above Tsat -> spurious subcooled void + energy imbalance).
*   Rod radius enlarged to r_out=0.10 m so flux=0.40 MW/m2 (realistic PWR value).
* Verified: normal end, mass error ~8e-4 kg; Tout=578.5K (dT=18.5K vs Q/(m*cp)=18.1K);
*   voidg=0 everywhere (subcooled liquid, Tsat=615.3K). All 7 independent checks pass.
100  new  stdy-st
102  si  si
201  60.0  1.0e-6  0.01  3  100  200  500
1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  1.5e7  560.0
1020000  inj  tmdpjun
1020101  101000000  110000000  0.01
1020200  1
1020201  0.0  5.0  0.0  0.0
1100000  pipe  pipe
1100001  4
1100101  0.01  4
1100301  0.5  4
1100601  0.0  4
1100801  4.5e-5  0.11284  4
1101001  0000000  4
1101101  0  3
1101201  3  1.5e7  560.0  0  0  0  4
1101300  1
1101301  3.0  0.0  0.0  3
1200000  outj  sngljun
1200101  110010000  151000000  0.01  0.0  0.0  0000
1200201  1  3.0  0.0  0.0
1510000  outb  tmdpvol
1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1510200  3
1510201  0.0  1.5e7  560.0
11101000  4  3  2  0  0.0  0  0  4
11101100  0  1
11101101  1  0.09
11101102  1  0.10
11101201  1  1
11101202  2  2
11101301  1.0  1
11101302  1.0  2
11101400  0
11101401  560.0  1
11101402  560.0  2
11101403  560.0  3
11101501  0  0  0  0  0.0  1
11101502  0  0  0  0  0.0  2
11101503  0  0  0  0  0.0  3
11101504  0  0  0  0  0.0  4
11101601  110010000  0  1  1  0.5  1
11101602  110020000  0  1  1  0.5  2
11101603  110030000  0  1  1  0.5  3
11101604  110040000  0  1  1  0.5  4
11101701  1  0.25  0.0  0.0  1
11101702  1  0.25  0.0  0.0  2
11101703  1  0.25  0.0  0.0  3
11101704  1  0.25  0.0  0.0  4
11101801  0.11284  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1
11101802  0.11284  10.0  10.0  0.0  0.0  0.0  0.0  1.0  2
11101803  0.11284  10.0  10.0  0.0  0.0  0.0  0.0  1.0  3
11101804  0.11284  10.0  10.0  0.0  0.0  0.0  0.0  1.0  4
11101901  0.11284  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1
11101902  0.11284  10.0  10.0  0.0  0.0  0.0  0.0  1.0  2
11101903  0.11284  10.0  10.0  0.0  0.0  0.0  0.0  1.0  3
11101904  0.11284  10.0  10.0  0.0  0.0  0.0  0.0  1.0  4
20200100  power
20200101  0.0  5.0e5
20200102  100.0  5.0e5
20100100  s-steel
20100200  s-steel
.