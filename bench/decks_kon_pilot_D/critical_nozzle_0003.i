= NOZZLE CHOKED FLOW - TWO-PHASE (FLASHING) INITIALISATION TEST
= geometry identical to nozzle_choked.i ; only the initial state downstream is two-phase
= init: CV1 subcooled liquid 3.0 MPa/487 K, CV2-CV4 equilibrium two-phase (p below p_sat)
100  new  stdy-st
102  si  si
201  2.0  1.0e-8  2.0e-4  3  1000  5000  5000
*
1010000  upsrc  tmdpvol
1010101  1.9635e-3  0.2  3.927e-4  0.0  0.0  0.0  0.0  0.05  0000
1010200  3
1010201  0.0  3.0e6  487.0
*
1100000  nozzle  pipe
1100001  4
1100101  1.9635e-3  4
1100301  0.295  4
1100601  0.0  4
1100801  4.5e-5  0.05  4
1101001  0000000  4
1101101  0  3
1101201  3  3.00e6  487.0  0.0  0.0  0.0  1
1101202  2  2.50e6  0.001  0.0  0.0  0.0  2
1101203  2  1.70e6  0.010  0.0  0.0  0.0  3
1101204  2  0.80e6  0.030  0.0  0.0  0.0  4
1101300  1
1101301  40.0  0.0  0.0  3
*
1200000  inljun  sngljun
1200101  101010000  110000000  1.9635e-3  0.0  0.0  0000
1200201  1  40.0  0.0  0.0
*
1300000  outjun  sngljun
1300101  110010000  150000000  1.9635e-3  0.0  0.0  0000
1300201  1  40.0  0.0  0.0
*
1500000  atm  tmdpvol
1500101  1.9635e-3  0.2  3.927e-4  0.0  0.0  0.0  0.0  0.05  0000
1500200  3
1500201  0.0  1.0e5  373.0
.
