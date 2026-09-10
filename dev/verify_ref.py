# -*- coding: utf-8 -*-
"""核验 agent 自建的 12 个参考例：逐个真跑 + 物理校验。"""
import glob, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import registry
registry.load_plugins("tools")
import tools.relap5 as R

ref = r"knowledge/reference"
out = []
ok = 0
for p in sorted(glob.glob(os.path.join(ref, "ref_*.i"))):
    name = os.path.basename(p)
    tgt = os.path.join("workspace", "v_" + name)
    try:
        shutil.copy(p, tgt)
    except Exception as e:
        out.append(f"{name}: COPY失败 {e}")
        continue
    r = R.run_relap5("v_" + name)
    o = None
    import re
    m = re.search(r"输出=(\S+)", r)
    if m:
        o = m.group(1).replace("\\", "/")
    line = f"{name}: {r.splitlines()[0]}"
    if o:
        s = R.check_sanity(o)
        verdict = "物理通过" if "物理合理性：通过" in s else "物理存疑"
        masserr = [x for x in s.splitlines() if "质量守恒" in x]
        line += f" | {verdict} | {masserr[0] if masserr else ''}"
        if "物理合理性：通过" in s and "正常结束=True" in r:
            ok += 1
    out.append(line)
    try:
        os.remove(tgt)
    except Exception:
        pass
out.append(f"\n通过: {ok}/12")
open("verify_ref_out.txt", "w", encoding="utf-8").write("\n".join(out))
