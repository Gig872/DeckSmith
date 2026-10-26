= HORIZONTAL PIPE STEADY FLOW AND HEAT TRANSFER, 4 VOLUMES
* ---------------------------------------------------------------
* Model: horizontal circular pipe, flow area 0.02 m2, length 1.0 m,
*        equivalent diameter 0.1596 m, roughness 4.5e-5 m,
*        4 control volumes along the axis.
* Boundary conditions:
*   inlet  : tmdpjun 100, constant mass flow 2.0 kg/s, water at 300 K
*   outlet : tmdpvol 200, constant pressure 1.0 MPa (mass sink)
* Heating: uniform wall heat flux along the full length,
*          total power 200000 W -> 50000 W per control volume.
*          Heat structure 300 (cylindrical, 1 axial node per volume,
*          4 axial heat structures), heat source from general table 1.
* Expected: single phase subcooled liquid, 300 K -> about 324 K,
*           pressure about 1.0 MPa, mass error near zero.
* ---------------------------------------------------------------
* --- problem type and units ---
100  new  stdy-st
102  si  si
* --- general tables: total power vs time (constant 200000 W) ---
20200100  time
20200101  0.0  200000.0
20200102  1000.0  200000.0
* --- time step control ---
201  10.0  1.0e-6  0.05  3  10  100  1000
* --- hydraulic component 100: inlet time dependent junction ---
1000000  inlettj  tmdpjun
1000101  200010000  110000000  0.02
1000200  1
1000201  0.0  2.0  0.0  0.0
1000202  1000.0  2.0  0.0  0.0
* --- hydraulic component 110: pipe, 4 control volumes ---
1100000  pipe  pipe
1100001  4
1100101  0.02  4
1100301  0.25  4
1100601  0.0  4
1100801  4.5e-5  0.1596  4
1101001  0  4
1101101  0  3
1101201  3  1.0e6  300.0  0.0  0.0  0.0  4
1101300  1
1101301  2.0  0.0  0.0  3
* --- hydraulic component 200: outlet time dependent volume ---
2000000  outletv  tmdpvol
2000101  1.0  1.0  1.0  0.0  0.0  0.0  0.0  0.0  0
2000200  3
2000201  0.0  1.0e6  320.0
2000202  1000.0  1.0e6  320.0
* --- heat structure 300: pipe wall, 4 axial sections ---
3000000  4  2  2  0  0.0  0  0
3001000  0  2
3001011  0.005  2
3002011  1  2
3003011  1.0  2
3004011  300.0  2
3005011  110010000  0  1  1  0.0  4
3006011  0  0  0  0.0  4
3007011  1  1.0  0.0  0.0  4
* --- material 1: carbon steel ---
20100100  cc-steel
.
