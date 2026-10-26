# -*- coding: utf-8 -*-
"""refrun：批量跑**参考（真值）卡**，抽取期望标量，并做有效性过滤。

产出 bench/expected.jsonl，每行：
  {task_id, family, task_type, ok(正常结束), valid(通过物理体检), scalars{var:agg->值}}
支持断点续跑（已完成的 task_id 跳过）。

用法： python bench/refrun.py [起始索引] [结束索引]
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools.relap5 as R  # noqa: E402
from bench.agg import scalars  # noqa: E402
from postprocess.extract import get_series  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(HERE, "tasks.jsonl")
OUT = os.path.join(HERE, "expected.jsonl")


def done_ids() -> set:
    ids = set()
    if os.path.isfile(OUT):
        for line in open(OUT, encoding="utf-8"):
            try:
                ids.add(json.loads(line)["task_id"])
            except Exception:  # noqa: BLE001
                pass
    return ids


def _write(p, text: str, tries: int = 6) -> bool:
    """写文件并对占用/竞争重试。"""
    for k in range(tries):
        try:
            p.write_text(text, encoding="utf-8")
            return True
        except OSError:
            time.sleep(0.5 * (k + 1))
    return False


def converged(text: str) -> bool:
    """稳态题：末两次输出编辑的关键量变化应很小（否则参考卡未到稳态）。"""
    for var in ("tempf", "pressure"):
        ser = get_series(text, var)
        worst = 0.0
        for _cid, pts in ser.items():
            if len(pts) >= 2:
                a, b = pts[-2][1], pts[-1][1]
                worst = max(worst, abs(b - a) / (abs(b) or 1.0))
        if ser:
            return worst <= 0.01
    return True


TRANSIENT = {"sbloca_blowdown", "lof_transient", "valve_transient", "accumulator", "numerical_dt"}


def is_transient(t: dict) -> bool:
    """按"源族"判断：T2/T3 任务族名统一，需看 params.src_family。"""
    src = (t.get("params") or {}).get("src_family") or t.get("family")
    return src in TRANSIENT


def main(argv):
    tasks = [json.loads(l) for l in open(TASKS, encoding="utf-8")]
    lo = int(argv[0]) if argv else 0
    hi = int(argv[1]) if len(argv) > 1 else len(tasks)
    seen = done_ids()
    fout = open(OUT, "a", encoding="utf-8")
    t0 = time.time()
    n_ok = n_valid = n_skip = 0
    for i in range(lo, min(hi, len(tasks))):
        t = tasks[i]
        if t["task_id"] in seen:
            n_skip += 1
            continue
        rel = f"ref_{i:04d}_{os.getpid() % 997}.i"     # 唯一名，避免并发/占用冲突
        if not _write(R._SB.resolve(rel), t["reference"]):
            print(f"[{i}] 写入失败，跳过", flush=True)
            continue
        msg = R.run_relap5(rel, timeout=900)
        ok = "正常结束=True" in msg
        scal, sanity, valid = {}, "", False
        m = re.search(r"输出=(\S+)", msg)
        if ok and m:
            try:
                txt = R._read_o(R._SB.resolve(m.group(1)))
                scal = scalars(txt, t.get("key_outputs") or [])
                sanity = R.check_sanity(m.group(1))
                valid = R.sanity_passes(sanity)      # 统一判据
                if valid and not is_transient(t) and not converged(txt):
                    valid = False
                    sanity += "\n[未收敛] 末次输出仍在变化，参考卡未到稳态"
            except Exception as e:  # noqa: BLE001
                sanity = f"(体检异常: {e})"
        n_ok += ok
        n_valid += valid
        rec = {"task_id": t["task_id"], "family": t["family"], "task_type": t["task_type"],
               "ok": ok, "valid": valid, "scalars": scal,
               "sanity_flag": ("OK" if valid else ("跑通但体检不过" if ok else "跑不通"))}
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fout.flush()
        el = time.time() - t0
        print(f"[{i}/{len(tasks)}] {t['task_id']:24s} ok={ok} valid={valid} "
              f"({el:.0f}s)", flush=True)
    fout.close()
    print(f"完成：新增 ok={n_ok} valid={n_valid} 跳过={n_skip}，用时 {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
