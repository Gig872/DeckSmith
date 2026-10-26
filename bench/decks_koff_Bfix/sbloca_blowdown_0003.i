= PWR SBLOCA DEPRESSURIZATION - SINGLE VOLUME + BREAK TO CONTAINMENT
* Case: single control volume (0.2 m3) at 10 MPa / 600 K, break opens at t=10 s
* Break area 1.0E-04 m2 discharging to containment 0.1 MPa / 300 K
* Transient length 30 s
*
* Components
*   100  vessel  snglvol   primary system lumped volume
*   200  cont    tmdpvol   containment (pressure/temperature boundary)
*   300  brk     sngljun   break junction, vessel -> containment
*   301  trip    variable trip: time >= 10 s
*
* Units: SI
100 new transnt
102 si si
*
* --- time step control: end time, min dt, max dt, control, minor edit, major edit, restart
201 30.0 1.0e-6 1.0e-3 3 100 1000 1
*
* ===================== vessel (primary lumped volume) =====================
1000000 vessel snglvol
* area, length, volume, azimuth, inclination, elevation, roughness, dh, flag
1000101 1.0 0.2 0.2 0.0 0.0 0.0 0.0 0.5 0
* control code 1 = water, t=3 -> pressure and temperature follow
1000200 3 10.0e6 600.0
*
* ===================== containment boundary =====================
2000000 cont tmdpvol
2000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 1.0 0
* control code 3 = pressure + temperature table
2000200 3
2000201 0.0 0.1e6 300.0
*
* ===================== break junction =====================
3000000 brk sngljun
* from vessel outlet, to containment, area, fwd loss, rev loss, flag
3000101 100010000 200010000 1.0e-4 0.0 0.0 0
* control code 1 = mass flow; initial flow zero (break closed before t=10 s)
3000201 1 0.0 0.0 0.0
*
* ===================== trip: break opens at t = 10 s =====================
301 time 0 ge null 0 10.0
*
* ===================== break flow table (mass flow, kg/s) =====================
* break closed until 10 s, then junction area is opened by trip 301
3000200 1 301
3000201 0.0 0.0 0.0 0.0
3000202 10.0 0.0 0.0 0.0
3000203 10.001 1.0e6 1.0e6 0.0
3000204 30.0 1.0e6 1.0e6 0.0
.
