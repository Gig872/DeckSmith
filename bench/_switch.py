# -*- coding: utf-8 -*-
r"""看门狗：等 single_pipe_steady 跑完 → 杀掉串行 runner → 以并发接管剩余题。

以脱离进程方式启动： python bench/_switch.py --workers 6
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FAM = "single_pipe_steady"


def count_family(fam: str) -> int:
    n = 0
    for p in glob.glob(os.path.join(HERE, "run_results*.jsonl")):
        for line in open(p, encoding="utf-8", errors="replace"):
            try:
                if json.loads(line)["family"] == fam:
                    n += 1
            except Exception:  # noqa: BLE001
                pass
    return n


def find_runner_pids():
    ps = ["powershell", "-NoProfile", "-Command",
          "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
          "Where-Object {$_.CommandLine -like '*bench/runner.py*'} | "
          "Select-Object -ExpandProperty ProcessId"]
    try:
        r = subprocess.run(ps, capture_output=True, text=True, timeout=60)
        return [int(x) for x in r.stdout.split() if x.strip().isdigit()]
    except Exception:  # noqa: BLE001
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--total", type=int, default=96, help="该族总题数")
    a = ap.parse_args()

    log = open(os.path.join(HERE, "_switch.log"), "w", encoding="utf-8")

    def w(m):
        log.write(time.strftime("[%H:%M:%S] ") + m + "\n")
        log.flush()

    w(f"看门狗启动：等待 {FAM} 完成（共 {a.total} 题）")
    while True:
        n = count_family(FAM)
        if n >= a.total:
            break
        time.sleep(20)
    w(f"{FAM} 已完成 {n}/{a.total}，准备切换")

    for pid in find_runner_pids():
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True)
        w(f"已终止串行 runner pid={pid}")
    time.sleep(8)

    DETACHED, NEWGRP = 0x00000008, 0x00000200
    logf = open(os.path.join(HERE, "_runner_par.log"), "w", encoding="utf-8")
    p = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "runner.py"),
         "--workers", str(a.workers), "--skip-done", "--repeats", "1"],
        cwd=ROOT, stdout=logf, stderr=subprocess.STDOUT,
        creationflags=DETACHED | NEWGRP)
    w(f"已启动并发 runner pid={p.pid}，workers={a.workers}")
    log.close()


if __name__ == "__main__":
    main()
