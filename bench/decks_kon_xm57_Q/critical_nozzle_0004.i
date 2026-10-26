=喷管临界流（壅塞）稳态模型：上游3.0MPa/487K过冷水 → 4段圆管喷管 → 下游0.1MPa大气
* 依据：RELAP5 MOD3.3，SI单位制；基底来自已验证样例 agent/horizontal_pipe_16cv_100kW_10kgs_1MPa_steady
* 物理意图：验证高压过冷水经喷管向低压排放是否发生壅塞；报告稳态质量流量
* 模型结构：tmdpvol(100) → pipe(120,4CV) → tmdpvol(102)
* 注：所有注释行以 * 开头；无行内引号；几何一致（倾角=0 ⇒ 高程=0）
100 new stdy-st
102 si si
201 100.0 0.001 10.0 3 1 1 0
* —— 上游定压水源（tmdpvol）
1000000 upstream tmdpvol
* CCC0101: area, length, volume, azimuth, incline, delta_z, rough, dh, flag
1000101 0.01005 0.1 0.001005 0.0 0.0 0.0 4.5e-5 0.113 00000
* CCC0200: control code (εbt = 1 0 3)
1000200 103
* CCC0201: time, pressure, temperature
1000201 0.0 3.0e6 487.0
* —— 喷管（pipe, 4 control volumes）
1200000 nozzle pipe
* CCC0001: number of volumes
1200001 4
* CCC0101: area, vol# (4次，每CV面积相同)
1200101 0.01005 1
1200101 0.01005 2
1200101 0.01005 3
1200101 0.01005 4
* CCC0301: length, vol# (均分1.18m → 0.295m)
1200301 0.295 1
1200301 0.295 2
1200301 0.295 3
1200301 0.295 4
* CCC0601: incline, vol# (水平管)
1200601 0.0 1
1200601 0.0 2
1200601 0.0 3
1200601 0.0 4
* CCC0801: rough, dh, vol# (dh = 0.113 m)
1200801 4.5e-5 0.113 1
1200801 4.5e-5 0.113 2
1200801 4.5e-5 0.113 3
1200801 4.5e-5 0.113 4
* CCC1001: flag (pvbfe = 0000000), vol#
1201001 0000000 1
1201001 0000000 2
1201001 0000000 3
1201001 0000000 4
* CCC1101: junction flag (fvcahs = 000000), jun# (4CV → 3 internal junctions)
1201101 000000 1
1201101 000000 2
1201101 000000 3
* CCC1201: init code (εbt = 1 0 3), P, T, 0, 0, 0, vol# (平衡态P&T)
1201201 103 3.0e6 487.0 0.0 0.0 0.0 1
1201201 103 3.0e6 487.0 0.0 0.0 0.0 2
1201201 103 3.0e6 487.0 0.0 0.0 0.0 3
1201201 103 3.0e6 487.0 0.0 0.0 0.0 4
* CCC1300: junction flow control (1 = mass flow)
1201300 1
* CCC1301: initial mass flow, liq_vel, vap_vel, jun# (set to zero for auto-converge)
1201301 0.0 0.0 0.0 1
1201301 0.0 0.0 0.0 2
1201301 0.0 0.0 0.0 3
* —— 上游→喷管接管
1030000 jun100 sngljun
1030101 100010000 120000000 0.01005 0.0 0.0 0000
1030201 1 0.0 0.0 0.0
* —— 喷管→下游接管
1040000 jun102 tmdpjun
1040101 120040000 102000000 0.01005
1040200 1
1040201 0.0 0.0 0.0 0.0
* —— 下游大气（tmdpvol）
1020000 downstrm tmdpvol
* CCC0101: area, length, volume, azimuth, incline, delta_z, rough, dh, flag
1020101 0.01005 0.1 0.001005 0.0 0.0 0.0 4.5e-5 0.113 00000
* CCC0200: control code (εbt = 1 0 3)
1020200 103
* CCC0201: time, pressure, temperature
1020201 0.0 1.0e5 373.0
.