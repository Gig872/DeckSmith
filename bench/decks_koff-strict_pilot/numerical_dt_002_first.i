= PWR SBLOCA DEPRESSURIZATION, SINGLE VOLUME + BREAK TO CONTAINMENT
= VOLUME 0.2 M3, INITIAL 15 MPA 600 K SUBCOOLED WATER
= BREAK OPENS AT T=5 S, EQUIVALENT AREA 2.0E-4 M2, DISCHARGE TO 0.1 MPA 300 K
* ---------------------------------------------------------------------------
* 100 CARD : TRANSIENT CALCULATION
100 new transnt
* 102 CARD : SI UNITS
102 si si
* 201 CARD : END TIME 30 S, MIN DT 1E-8, MAX DT 0.005 S, CONTROL 3
201 30.0 1.0e-8 5.0e-3 3
* ---------------------------------------------------------------------------
* CONTROL VOLUME 100 : PRIMARY SYSTEM (SINGLE VOLUME, 0.2 M3)
* AREA 1.0 M2, LENGTH 0.2 M, VOLUME 0.2 M3, HORIZONTAL, ELEVATION 0
1000000 pvessel snglvol
1000101 1.0 0.2 0.2 0.0 0.0 0.0 0.0 1.0 0
* INITIAL STATE : P = 15 MPA, T = 600 K (SUBCOOLED LIQUID)
1000200 1 15.0e6 600.0
* ---------------------------------------------------------------------------
* TIME DEPENDENT VOLUME 110 : CONTAINMENT SINK, 0.1 MPA, 300 K
1100000 cntmt tmdpvol
1100101 100.0 1.0 100.0 0.0 0.0 0.0 0.0 10.0 0
1100200 3
1100201 0.0 0.1e6 300.0
1100202 1000.0 0.1e6 300.0
* ---------------------------------------------------------------------------
* TIME DEPENDENT JUNCTION 120 : BREAK, FROM VESSEL 100 TO CONTAINMENT 110
* AREA 2.0E-4 M2, MASS FLOW GIVEN (CONTROL WORD 1)
1200000 brk tmdpjun
1200101 100010000 110010000 2.0e-4
1200200 1
* BREAK CLOSED UNTIL T = 5 S, THEN FULL AREA FLOW (NEGATIVE = OUT OF VESSEL)
1200201 0.0 0.0 0.0 0.0
1200202 4.999 -0.0 0.0 0.0
1200203 5.0 -1.0e6 0.0 0.0
1200204 1000.0 -1.0e6 0.0 0.0
* ---------------------------------------------------------------------------
* JUNCTION 130 : VESSEL OUTLET SIDE TO BREAK (ZERO LENGTH CONNECTION)
* NOT USED - BREAK CONNECTS DIRECTLY TO VESSEL OUTLET
* ---------------------------------------------------------------------------
.end
