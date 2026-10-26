= SBLOCA Final Model: 10MPa/0.2m3/10cm2 Break at t=2s (30s)
* System Volume: 110-000000 (snglvol)
1100000 sys snglvol
1100101 0.2 1.0 0.0 0.0 0.0 0.0 0.0 0.505 0000
1100200 3 10000000.0 600.0
* Break Valve: 120-000000 (valve + trpvlv), opens at t=2 s
1200000 brk valve
1200101 110010000 131000000 0.001 0.0 0.0 000100
1200201 1 1.0 0.0 0.0
1200300 trpvlv
1200301 401
* Containment Boundary: 131-000000 (tmdpvol)
1310000 cnt tmdpvol
1310101 0.05 0.5 0.0 0.0 0.0 0.0 0.0 0.252 0000
1310200 3
1310201 0.0 100000.0 300.0
* Control Cards
100 new transnt
102 si si
201 30.0 1.0e-6 0.01 3 100 200 500
* Trigger Card: time > 2.0 s
401 time 0 gt null 0 2.0 n
.