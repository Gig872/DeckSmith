# -*- coding: utf-8 -*-
"""环境自检：分发到新机器后，快速判断"能不能跑"。
返回一组检查项 [{'name','ok','detail'}]，供命令行或界面展示。
"""
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

import config as C


def check() -> list[dict]:
    rows: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        rows.append({"name": name, "ok": bool(ok), "detail": str(detail)})

    # 1) Python
    add("Python 版本", sys.version_info >= (3, 9), f"{platform.python_version()}（需 ≥ 3.9）")

    # 2) tkinter（桌面界面）
    try:
        import tkinter  # noqa: F401
        add("tkinter（桌面界面）", True, "可用")
    except Exception as e:  # noqa: BLE001
        add("tkinter（桌面界面）", False, f"不可用：{e}（请装带 tkinter 的 Python）")

    # 3) 第三方依赖（核心零依赖；matplotlib 为**可选**绘图增强）
    add("第三方依赖（核心）", True, "无（纯标准库，无需 pip install）")
    try:
        import plotenv
        if plotenv.available():
            add("绘图增强 matplotlib（可选）", True, "已装 —— 可导出精细 PNG")
        else:
            ok_i, why = plotenv.can_install()
            tip = ("可在『结果图』窗口点『启用 matplotlib』自动安装"
                   if ok_i else "打包版：改用 build_exe.bat mpl 的带库构建")
            add("绘图增强 matplotlib（可选）", True, f"未装 —— 零依赖 Canvas 出图可用；{tip}")
    except Exception as e:  # noqa: BLE001
        add("绘图增强 matplotlib（可选）", True, f"未检测：{e}")

    # 4) 配置
    add("config.json", C.CONFIG_FILE.is_file(), str(C.CONFIG_FILE))
    s = C.load()
    add("API Key 已填", bool(s.api_key), "已填" if s.api_key else "未填 —— 请在『⚙ 设置』里填")
    add("模型", bool(s.model), f"{s.model} @ {s.base_url}")

    # 5) RELAP5
    exe, rdir = C.relap5_paths()
    add("RELAP5 可执行文件", exe.is_file(), str(exe) if str(exe) else "(未探测到)")
    try:
        tpf = list(Path(rdir).glob("tpf*")) if rdir and Path(rdir).is_dir() else []
    except Exception:  # noqa: BLE001
        tpf = []
    add("RELAP5 物性文件 tpf*", bool(tpf), f"{len(tpf)} 个 @ {rdir or '(无目录)'}")

    # 6) 技术手册
    doc = Path(s.doc_path) if s.doc_path else None
    add("技术手册（手册检索用）", bool(doc and doc.is_file()),
        str(doc) if doc else "未找到 —— 设 config.json 的 doc_path 或环境变量 RELAP5_DOC")

    # 7) 技能 / 样例库
    skdir = Path(s.skills_dir)
    add("skills 技能目录", skdir.is_dir(), f"{len(list(skdir.glob('*.md')))} 个技能 @ {skdir}")
    ref, lrn = Path(s.reference_dir), Path(s.learned_dir)
    n_ref = len(list((ref / "human").glob("*.i"))) + len(list((ref / "agent").glob("*.i")))
    n_lrn = len(list(lrn.glob("*.i")))
    add("knowledge 样例库", ref.is_dir() or lrn.is_dir(),
        f"参考库 {n_ref} 例 / 自主学习库 {n_lrn} 例")

    # 8) 工作目录可写
    try:
        p = Path(s.workspace)
        p.mkdir(parents=True, exist_ok=True)
        t = p / ".wtest"
        t.write_text("x", encoding="utf-8")
        t.unlink()
        add("工作目录可写", True, f"{s.workspace} — 可写")
    except Exception as e:  # noqa: BLE001
        add("工作目录可写", False, f"{s.workspace} — 不可写：{e}")

    return rows


def summary(rows: list[dict]) -> str:
    ok = sum(1 for r in rows if r["ok"])
    lines = [f"{'✓' if r['ok'] else '✗'} {r['name']}：{r['detail']}" for r in rows]
    bad = [r["name"] for r in rows if not r["ok"]]
    lines.append("")
    lines.append(f"合计 {ok}/{len(rows)} 项通过。" +
                 ("全部就绪，可以开工。" if not bad else f"需处理：{', '.join(bad)}"))
    return "\n".join(lines)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(summary(check()))
