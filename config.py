# -*- coding: utf-8 -*-
"""agent-kit 配置：模型/服务、熔断参数、工作目录。无硬编码路径。"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# 打包(PyInstaller)兼容：
#   BASE = 可写数据目录（打包后 = exe 所在目录；开发时 = 源码目录）→ config.json / workspace / learned
#   RES  = 只读资源目录（打包后 = 解包临时目录 _MEIPASS；开发时 = 源码目录）→ skills / reference / 手册
FROZEN = bool(getattr(sys, "frozen", False))
RES = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
BASE = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
ROOT = BASE
CONFIG_FILE = BASE / "config.json"
WORKSPACE = BASE / "workspace"


def _res_or_base(rel: str) -> Path:
    p = RES / rel
    return p if p.exists() else (BASE / rel)


@dataclass
class Settings:
    base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""
    model: str = "deepseek-chat"
    temperature: float = 0.2
    max_tokens: int = 16000    # 单次输出上限：给"读手册+理解+构建"留足空间
    thinking: bool = False     # 思考模式：开启模型的思维链（更慢更贵；仅对支持的模型生效）
    # 熔断 / 沙箱
    # 注意：以下为**不可逾越的硬顶**。实际每任务的起档由目标复杂度决定
    # （见 safety.Budget），运行中只会在"确有进展"时逐级放宽，绝不越过硬顶。
    # 硬顶按"最复杂目标形态"（完整整体式压水堆·瞬态）标定。
    max_steps: int = 200         # 工具调用轮次硬顶
    max_seconds: int = 5400      # 单次任务时长硬顶（90 分钟）
    request_timeout: int = 120   # 单次请求超时
    token_budget: int = 24_000_000   # 累计 token 硬顶（大任务需更多；XL 起档 12M，可升到此）
    ctx_chars: int = 600_000     # 上下文字符上限硬顶（按需放宽）
    dry_run: bool = False        # True: 不真调模型，用脚本化 mock 验证循环
    # 目录（打包兼容：skills/reference 走只读资源，workspace/learned 走可写数据目录）
    workspace: str = str(WORKSPACE)
    skills_dir: str = str(_res_or_base("skills"))

    # ---- RELAP5 领域 ----
    # 以下路径**不写死本机**：优先环境变量 → config.json → 多候选探测（见 detect_*）。
    relap5_dir: str = ""          # 含 relap5.exe + tpf* 的目录；空则自动探测
    relap5_exe: str = ""          # 可显式指定可执行文件
    doc_path: str = ""            # 技术手册（检索用）；空则自动探测
    reference_dir: str = str(_res_or_base("knowledge/reference"))  # 参考库（人工种子，最高权重）
    learned_dir: str = str(BASE / "knowledge" / "learned")         # 自主学习库（agent 自沉淀，可写）


def load() -> Settings:
    s = Settings()
    if CONFIG_FILE.is_file():
        try:
            d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            for k in Settings.__dataclass_fields__:
                if k in d and d[k] not in (None, ""):
                    setattr(s, k, d[k])
        except Exception:
            pass
    # 环境变量覆盖（分发到不同机器时最省事）
    s.base_url = os.environ.get("AGENT_BASE_URL", s.base_url)
    s.api_key = os.environ.get("AGENT_API_KEY", s.api_key)
    s.model = os.environ.get("AGENT_MODEL", s.model)
    s.relap5_dir = os.environ.get("RELAP5_DIR", s.relap5_dir)
    s.doc_path = os.environ.get("RELAP5_DOC", s.doc_path)
    # 若未显式给出/给的不存在，自动探测
    if not s.relap5_dir or not (Path(s.relap5_dir) / "relap5.exe").is_file():
        s.relap5_dir = detect_relap5() or s.relap5_dir
    if not s.doc_path or not Path(s.doc_path).is_file():
        s.doc_path = detect_doc() or s.doc_path
    # 打包后首次运行：在 exe 旁生成空 config.json 模板（不含任何密钥）
    if FROZEN and not CONFIG_FILE.is_file():
        try:
            CONFIG_FILE.write_text(json.dumps(
                {"base_url": s.base_url, "api_key": "", "model": s.model,
                 "relap5_dir": "", "doc_path": "",
                 "_note": "请填 api_key / model；relap5_dir 指向你的 RELAP5 安装目录（含 relap5.exe 与 tpf*）"},
                ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    return s


def ensure_dirs(s: Settings) -> None:
    # 只创建**可写**目录（skills/reference 可能是包内只读资源，不强行建）
    for p in (s.workspace, s.learned_dir):
        try:
            Path(p).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    # 打包后首次运行：把包内的 learned 种子复制到可写目录
    try:
        seed = RES / "knowledge" / "learned"
        dst = Path(s.learned_dir)
        if seed.is_dir() and seed.resolve() != dst.resolve() and not any(dst.glob("*.i")):
            import shutil
            for f in seed.glob("*.i"):
                shutil.copy(f, dst / f.name)
    except Exception:
        pass


def _first_with(fname: str, *dirs) -> str:
    for c in dirs:
        if c and (Path(c) / fname).is_file():
            return str(c)
    return ""


def detect_relap5() -> str:
    """自动探测含 relap5.exe 的目录：环境变量 → config → 项目内 → 常见安装位置。"""
    s = Settings()
    if CONFIG_FILE.is_file():
        try:
            s.relap5_dir = json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("relap5_dir", "") or ""
        except Exception:
            pass
    cands = [os.environ.get("RELAP5_DIR"), s.relap5_dir,
             ROOT / "relap5", ROOT / "relap5程序", ROOT / "bin",
             r"C:\relap5", r"C:\relap5程序", r"C:\RELAP5",
             r"D:\relap5", r"D:\relap5程序",
             os.path.expanduser("~/relap5")]
    return _first_with("relap5.exe", *cands)


def detect_doc() -> str:
    """自动探测技术手册：环境变量 → config → 项目内 → 常见位置。"""
    s = Settings()
    if CONFIG_FILE.is_file():
        try:
            s.doc_path = json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("doc_path", "") or ""
        except Exception:
            pass
    names = ["relap5输入卡介绍.md", "manual.md"]
    dirs = [os.environ.get("RELAP5_DOC"), s.doc_path,
            RES, RES / "knowledge", ROOT, ROOT / "knowledge", ROOT / "docs",
            r"C:\relap5"]
    for d in dirs:
        if d and Path(d).is_file() and Path(d).suffix == ".md":
            return str(d)                      # 直接给了文件
        if d and Path(d).is_dir():
            for nm in names:
                if (Path(d) / nm).is_file():
                    return str(Path(d) / nm)
    return ""


def relap5_paths() -> tuple[Path, Path]:
    """返回 (relap5.exe, 其目录[含物性文件])。"""
    s = load()
    d = s.relap5_dir or detect_relap5()
    exe = Path(s.relap5_exe) if s.relap5_exe else Path(d) / "relap5.exe"
    return exe, Path(d)
