# -*- coding: utf-8 -*-
"""重跑前置：① 知识库物理隔离（卡移入 bench/holdout/，不删除）② 归档旧评测结果。

原则：不删除、不靠声明，物理移出 agent 可达范围。全部可逆（见 restore_knowledge.py）。
"""
from __future__ import annotations

import glob
import io
import json
import os
import shutil
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
HOLD = os.path.join(HERE, "holdout")

SRC = [
    ("learned",         os.path.join(ROOT, "knowledge", "learned")),
    ("reference_agent", os.path.join(ROOT, "knowledge", "reference", "agent")),
    ("reference_human", os.path.join(ROOT, "knowledge", "reference", "human")),
]


def isolate_knowledge():
    os.makedirs(HOLD, exist_ok=True)
    moved = []
    for tag, src in SRC:
        if not os.path.isdir(src):
            continue
        dst = os.path.join(HOLD, tag)
        os.makedirs(dst, exist_ok=True)
        for p in sorted(glob.glob(os.path.join(src, "*.i"))):
            shutil.move(p, os.path.join(dst, os.path.basename(p)))
            moved.append({"tier": tag, "name": os.path.basename(p), "src": src})
    man = os.path.join(HOLD, "MANIFEST.json")
    prev = []
    if os.path.isfile(man):
        try:
            prev = json.loads(io.open(man, encoding="utf-8").read())
        except Exception:
            prev = []
    seen = {(m["tier"], m["name"]) for m in prev}
    prev += [m for m in moved if (m["tier"], m["name"]) not in seen]
    io.open(man, "w", encoding="utf-8").write(json.dumps(prev, ensure_ascii=False, indent=2))
    return moved


def build_eval_lib():
    """把 holdout 的卡装配成「带库」条件用的评测库（副本，不动 holdout）。"""
    lib = os.path.join(HERE, "eval_lib")
    mapping = [
        ("reference_human", os.path.join(lib, "reference", "human")),
        ("reference_agent", os.path.join(lib, "reference", "agent")),
        ("learned",         os.path.join(lib, "learned_seed")),
    ]
    n = 0
    for tag, dst in mapping:
        src = os.path.join(HOLD, tag)
        if not os.path.isdir(src):
            continue
        os.makedirs(dst, exist_ok=True)
        for p in glob.glob(os.path.join(src, "*.i")):
            dstf = os.path.join(dst, os.path.basename(p))
            try:
                if os.path.exists(dstf):          # 目标可能只读（上次拷贝留下的属性）
                    os.chmod(dstf, 0o666)
                    os.remove(dstf)
                shutil.copy2(p, dstf)
                os.chmod(dstf, 0o666)
                n += 1
            except OSError as e:  # noqa: PERF203
                print("  [跳过]", dstf, e)
    return n


def archive_results():
    stamp = time.strftime("%Y%m%d_%H%M%S")
    arch = os.path.join(HERE, "archive", stamp)
    old = sorted(glob.glob(os.path.join(HERE, "run_results*.jsonl")))
    if old:
        os.makedirs(arch, exist_ok=True)
        for p in old:
            shutil.move(p, os.path.join(arch, os.path.basename(p)))
    return arch, [os.path.basename(p) for p in old]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", action="store_true",
                    help="同时归档旧 run_results*.jsonl（重跑当天用，避免新旧混算）")
    a = ap.parse_args()
    moved = isolate_knowledge()
    arch, olds = archive_results() if a.archive else ("(未归档；加 --archive 启用)", [])
    print("知识库隔离：移出", len(moved), "张卡 ->", HOLD)
    for tag, _ in SRC:
        d = os.path.join(HOLD, tag)
        n = len(glob.glob(os.path.join(d, "*.i"))) if os.path.isdir(d) else 0
        print(f"  holdout/{tag}: {n} 张")
    nb = build_eval_lib()
    print("带库条件装配：eval_lib 副本", nb, "张（供 --knowledge on 使用）")
    print("旧结果归档：", len(olds), "个文件 ->", arch if olds else "(无)")
    for o in olds:
        print("  ", o)
    # 复核：原目录应为空
    for tag, src in SRC:
        left = glob.glob(os.path.join(src, "*.i"))
        if left:
            print(f"  [警告] {src} 仍有 {len(left)} 张未移出")
    print("done")


if __name__ == "__main__":
    main()
