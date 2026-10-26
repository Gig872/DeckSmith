# -*- coding: utf-8 -*-
"""把 bench/holdout/ 里的卡原样还原回 knowledge/（prep_rerun 的逆操作）。"""
from __future__ import annotations

import glob
import io
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
HOLD = os.path.join(HERE, "holdout")
MAN = os.path.join(HOLD, "MANIFEST.json")

TIER_SRC = {
    "learned":         os.path.join(ROOT, "knowledge", "learned"),
    "reference_agent": os.path.join(ROOT, "knowledge", "reference", "agent"),
    "reference_human": os.path.join(ROOT, "knowledge", "reference", "human"),
}


def main():
    if not os.path.isfile(MAN):
        print("无清单：", MAN)
        return
    items = json.loads(io.open(MAN, encoding="utf-8").read())
    n = 0
    for it in items:
        tier, name = it["tier"], it["name"]
        src = os.path.join(HOLD, tier, name)
        dst_dir = TIER_SRC.get(tier)
        if not dst_dir or not os.path.isfile(src):
            continue
        os.makedirs(dst_dir, exist_ok=True)
        shutil.move(src, os.path.join(dst_dir, name))
        n += 1
    print("已还原", n, "张卡")
    for tag, d in TIER_SRC.items():
        print(f"  {tag}: {len(glob.glob(os.path.join(d, '*.i')))} 张")


if __name__ == "__main__":
    main()
