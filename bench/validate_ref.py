# -*- coding: utf-8 -*-
"""抽验：渲染的参考卡能否真跑。用法： python bench/validate_ref.py [idx ...]"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools.relap5 as R  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv):
    tasks = [json.loads(l) for l in open(os.path.join(HERE, "tasks.jsonl"), encoding="utf-8")]
    picks = [int(a) for a in argv] or [0, 24, 48, 72]
    ok = 0
    for i in picks:
        if not (0 <= i < len(tasks)):
            print(i, "out of range")
            continue
        t = tasks[i]
        rel = f"bench_ref_{i:03d}.i"
        R._SB.resolve(rel).write_text(t["reference"], encoding="utf-8")
        msg = R.run_relap5(rel, timeout=180)
        good = "正常结束=True" in msg
        ok += good
        print(f"[{i}] {t['family']} {t['params']} -> {'OK' if good else 'FAIL'}")
        if good:
            print("      ", msg.replace(chr(10), " | ")[:150])
        else:
            for line in msg.splitlines()[:6]:
                print("      ", line[:110])
    print(f"通过 {ok}/{len(picks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
