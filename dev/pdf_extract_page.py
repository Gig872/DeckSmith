# -*- coding: utf-8 -*-
import sys, pymupdf
PDF = r"C:\relap-5\refs\loft_input_data_deck_relap5.pdf"
pno = int(sys.argv[1]); ylo = float(sys.argv[2]); yhi = float(sys.argv[3]); out = sys.argv[4]
d = pymupdf.open(PDF)
pg = d[pno - 1]
ws = pg.get_text("words")
ws = [w for w in ws if 100 < w[0] < 570 and ylo <= w[1] <= yhi]
ws.sort(key=lambda w: (round(w[3], 1), w[0]))
f = open(out, "w", encoding="utf-8")
for w in ws:
    f.write("top=%7.2f bot=%7.2f x0=%6.1f x1=%6.1f  %s\n" % (w[1], w[3], w[0], w[2], w[4]))
f.close()
