= PWR single-channel fuel rod steady-state heat conduction
= Coolant: 15.5 MPa, 560 K water, 0.2 kg/s through single volume channel
= Fuel rod: UO2 0-4.0 mm, He gap 4.0-4.1 mm (0.5 MPa), Zr clad 4.1-4.7 mm
= Uniform fission power 30 kW in fuel, gap conductance model, cylindrical
*
* --- control cards ---
100 new stdy-st
102 si si
201 100.0 1.0e-6 0.1 3 1 1 1
*
* --- coolant channel: single volume ---
1200000 chan snglvol
1200101 0.005 1.0 0.005 0.0 0.0 0.0 0.0 0.01 0
1200200 3 15.5e6 560.0
*
* --- inlet source: time dependent volume ---
1100000 src tmdpvol
1100101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1100200 3
1100201 0.0 15.5e6 560.0
*
* --- inlet: time dependent junction, 0.2 kg/s ---
1300000 inlet tmdpjun
1300101 110010000 120000000 0.005
1300200 1
1300201 0.0 0.2 0.0 0.0
*
* --- outlet: time dependent volume, 15.5 MPa ---
1400000 outlet tmdpvol
1400101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1400200 3
1400201 0.0 15.5e6 560.0
*
* --- heat structure: fuel rod, cylindrical, gap conductance ---
* CCC=120, G=1 -> cards 11201XNN
11201000 1 5 2 0 0.0 0 0 2
11201002 0.5e6 120000000
11201011 1.0e-6 1.0e-6 0.0 0.0 1
11201100 0 2
11201101 0.002 1
11201102 0.002 2
11201103 0.0001 3
11201104 0.0006 4
11201201 1 1
11201202 1 2
11201203 2 3
11201204 3 4
11201301 1.0 1
11201302 1.0 2
11201303 0.0 3
11201304 0.0 4
11201400 0
11201401 560.0 1
11201402 560.0 2
11201403 560.0 3
11201404 560.0 4
11201405 560.0 5
11201501 0 0 0 0.0 0.0 1
11201601 120010000 0 1 1 1.0 1
11201701 1 1.0 0.0 0.0 1
11201901 0.0 10.0 10.0 0.0 0.0 0.0 0.0 1.0 1
*
* --- material properties ---
* composition 1: UO2 fuel (conductivity table 01-49, heat capacity table 51-99)
20100100 tbl/fctn 1 1
20100101 300.0 6.0
20100102 1000.0 3.0
20100103 2000.0 2.0
20100151 300.0 2.4e6
20100152 1000.0 2.6e6
20100153 2000.0 2.8e6
* composition 2: helium gap gas (mole fraction table)
20100200 tbl/fctn 3 1
20100201 helium 1.0
20100251 300.0 0.0
20100252 2000.0 0.0
* composition 3: zircaloy cladding
20100300 tbl/fctn 1 1
20100301 300.0 13.0
20100302 1000.0 17.0
20100303 2000.0 22.0
20100351 300.0 1.7e6
20100352 1000.0 1.9e6
20100353 2000.0 2.1e6
*
* --- power table: 30 kW constant ---
20200100 power
20200101 0.0 30000.0
20200102 100.0 30000.0
.
