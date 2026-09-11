# -*- coding: utf-8 -*-
"""卡匠 DeckSmith · RELAP5 建模智能体 · 桌面窗口（tkinter，零第三方依赖）。

- ⚙ 设置（折叠）：AI 接入（供应商/base_url/Key/模型）+ 全局提示词 + **字号**（实时）
- 多轮会话；agent 提问**并入对话流**（可回答或反问）；**多会话历史**（存/切换）
- **停止**（协作式中断）；**术语速查**（选中词→glossary）
- 用量：会话小结（自动）+ 手动刷新
- **已规范参数** / **输入卡（无注释版）** / **结果表** 三块面板
- **整页滚轮滚动**（内容超出窗口时可上下滚）
- 导出会话 / 卡片

启动：python decksmith.py ；打包 exe：build_exe.bat
"""
from __future__ import annotations

import json
import queue
import random
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import registry
import envcheck
from config import CONFIG_FILE, load
from core import Session
from usage import Usage
import tools.ask as ask

PROVIDERS = {
    "DeepSeek": "https://api.deepseek.com/v1",
    "OpenAI": "https://api.openai.com/v1",
    "阿里通义(DashScope 兼容)": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "智谱 GLM": "https://open.bigmodel.cn/api/paas/v4",
    "月之暗面 Moonshot": "https://api.moonshot.cn/v1",
    "本地 Ollama": "http://localhost:11434/v1",
    "自定义": "",
}
MODEL_HINTS = {
    "DeepSeek": "deepseek-chat", "OpenAI": "gpt-4o-mini",
    "阿里通义(DashScope 兼容)": "qwen-plus", "智谱 GLM": "glm-4",
    "月之暗面 Moonshot": "moonshot-v1-8k", "本地 Ollama": "llama3.1", "自定义": "",
}
# 模型下拉候选（可编辑，也能自己输入任意模型名）
MODEL_PRESETS = ["deepseek-chat", "deepseek-reasoner", "deepseek-v4-flash",
                 "gpt-4o", "gpt-4o-mini", "qwen-plus", "qwen-max",
                 "glm-4", "moonshot-v1-8k", "llama3.1"]

# 每个会话开始随机播放一句开场白
OPENERS = [
    "你好，我是 RELAP5 建模助手。用自然语言说需求即可——我会边问边把模型建出来，并真跑验证、讲清物理。",
    "在的。想建个什么系统？哪怕是「一段管道」「一个分支」这种模糊说法也行，细节我来跟你确认。",
    "欢迎。你可以直接描述工况（部件、边界、工况类型），缺的我用提问补全，不臆造。",
    "我准备好了。说需求就行：稳态还是瞬态？什么部件？不确定也没关系，我们一步步来。",
    "你好。我的原则是「不跑通不交付、不讲清物理不算完」。把你的目标告诉我吧。",
    "来了。想让我从零建一个模型，还是看看/改改你已有的输入卡？",
    "你好呀。RELAP5 的卡挺绕，交给我——你只管说想要什么，卡我来写、来跑、来校验。",
    "开工吧。先告诉我这模型要模拟什么物理过程，其余的我跟你对齐。",
]


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("卡匠 DeckSmith · RELAP5 建模智能体")
        root.geometry("1320x880")

        self.s = load()
        self.usage = Usage()
        self.sess: Session | None = None
        self.sess_name = ""
        self.q: queue.Queue = queue.Queue()
        self._busy = False
        self._pending = None
        self.var_trace = tk.BooleanVar(value=True)
        self.var_font = tk.IntVar(value=11)
        self._settings_open = False
        self._params_sig = None

        registry.load_plugins("tools")
        ask.set_asker(self._asker)

        self._build_topbar()
        self._build_settings_panel()
        self._build_scroll_body()
        self._load_cfg_into_ui()
        self._apply_fonts(self.var_font.get())
        self._refresh_sessions()
        self._set_status("就绪")
        self._set_usage_text("(尚无用量)")
        self._greet()

        self._set_icon()
        self.root.bind_all("<MouseWheel>", self._on_wheel, add="+")
        self.root.after(80, self._drain)
        self.root.after(400, self._poll_params)

    # ================= 图标 =================
    def _set_icon(self):
        base = Path(__file__).resolve().parent / "assets"
        png, ico = base / "icon.png", base / "icon.ico"
        try:
            if png.is_file():
                self._icon_img = tk.PhotoImage(file=str(png))     # 保住引用，防被回收
                self.root.iconphoto(True, self._icon_img)
        except Exception:  # noqa: BLE001
            pass
        try:
            if ico.is_file():
                self.root.iconbitmap(str(ico))                    # Windows 任务栏/标题栏
        except Exception:  # noqa: BLE001
            pass

    # ================= 顶栏 =================
    def _build_topbar(self):
        bar = ttk.Frame(self.root)
        bar.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Button(bar, text="⚙ 设置", command=self._toggle_settings).pack(side="left")
        ttk.Label(bar, text="会话").pack(side="left", padx=(10, 2))
        self.var_sess = tk.StringVar()
        self.cb_sess = ttk.Combobox(bar, textvariable=self.var_sess, width=18, state="readonly")
        self.cb_sess.pack(side="left")
        self.cb_sess.bind("<<ComboboxSelected>>", lambda _e: self._load_session(self.var_sess.get()))
        ttk.Button(bar, text="新建会话", command=self._new_session).pack(side="left", padx=4)
        self.btn_stop = ttk.Button(bar, text="停止", command=self._stop, state="disabled")
        self.btn_stop.pack(side="left", padx=4)
        ttk.Button(bar, text="术语速查", command=self._glossary_sel).pack(side="left", padx=4)
        ttk.Button(bar, text="环境检测", command=self._env_check).pack(side="left", padx=4)
        ttk.Button(bar, text="导出会话", command=self._export_chat).pack(side="left", padx=4)
        ttk.Button(bar, text="导出卡片", command=self._export_card).pack(side="left", padx=4)
        ttk.Checkbutton(bar, text="工具轨迹", variable=self.var_trace).pack(side="left", padx=8)
        self.lbl_status = ttk.Label(bar, text="就绪", foreground="#666")
        self.lbl_status.pack(side="right")

    # ================= 设置（折叠） =================
    def _build_settings_panel(self):
        f = ttk.LabelFrame(self.root, text="设置", padding=8)
        self.settings_frame = f
        ttk.Label(f, text="供应商").grid(row=0, column=0, sticky="w", pady=2)
        self.var_provider = tk.StringVar()
        cb = ttk.Combobox(f, textvariable=self.var_provider, values=list(PROVIDERS), state="readonly", width=24)
        cb.grid(row=0, column=1, sticky="w", pady=2)
        cb.bind("<<ComboboxSelected>>", self._on_provider)
        ttk.Label(f, text="base_url").grid(row=1, column=0, sticky="w", pady=2)
        self.var_base = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_base, width=44).grid(row=1, column=1, sticky="w", pady=2)
        ttk.Label(f, text="API Key").grid(row=2, column=0, sticky="w", pady=2)
        self.var_key = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_key, width=44, show="*").grid(row=2, column=1, sticky="w", pady=2)
        ttk.Label(f, text="模型").grid(row=3, column=0, sticky="w", pady=2)
        self.var_model = tk.StringVar()
        # 可编辑下拉：既能从候选里选，也能直接输入自定义模型名
        self.cb_model = ttk.Combobox(f, textvariable=self.var_model,
                                     values=MODEL_PRESETS, width=42)
        self.cb_model.grid(row=3, column=1, sticky="w", pady=2)
        ttk.Label(f, text="字号").grid(row=0, column=2, sticky="e", padx=(18, 4))
        sp = ttk.Spinbox(f, from_=8, to=24, width=4, textvariable=self.var_font,
                         command=lambda: self._apply_fonts(self.var_font.get()))
        sp.grid(row=0, column=3, sticky="w")
        sp.bind("<Return>", lambda _e: self._apply_fonts(self.var_font.get()))
        ttk.Label(f, text="全局提示词").grid(row=4, column=0, sticky="nw", pady=(6, 2))
        self.txt_sys = tk.Text(f, width=58, height=4, wrap="word")
        self.txt_sys.grid(row=4, column=1, columnspan=3, sticky="we", pady=(6, 2))
        bb = ttk.Frame(f)
        bb.grid(row=5, column=0, columnspan=4, sticky="we", pady=(4, 0))
        ttk.Button(bb, text="保存设置", command=self._save_cfg).pack(side="left")
        ttk.Label(bb, text="价格表(config.json 的 prices)：每 1M token 输入/输出，示例值可改。",
                  foreground="#666").pack(side="left", padx=10)
        f.columnconfigure(1, weight=1)

    def _toggle_settings(self):
        if self._settings_open:
            self.settings_frame.pack_forget()
        else:
            self.settings_frame.pack(fill="x", padx=8, pady=(6, 0), before=self.canvas_holder)
        self._settings_open = not self._settings_open

    def _on_provider(self, _evt=None):
        p = self.var_provider.get()
        if PROVIDERS.get(p):
            self.var_base.set(PROVIDERS[p])
        # 换供应商即换模型（原来只在模型栏为空时才换 → 表现为"无法切换模型"）
        hint = MODEL_HINTS.get(p)
        if hint:
            self.var_model.set(hint)
            try:
                self.cb_model.set(hint)
            except Exception:
                pass

    def _load_cfg_into_ui(self):
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
        base = self.s.base_url
        prov = next((k for k, v in PROVIDERS.items() if v and v == base), "自定义")
        self.var_provider.set(prov)
        self.var_base.set(base)
        self.var_key.set(self.s.api_key)
        self.var_model.set(self.s.model)
        self.txt_sys.delete("1.0", "end")
        self.txt_sys.insert("1.0", cfg.get("system_extra", ""))
        self.var_font.set(int(cfg.get("font_size", 11) or 11))

    def _save_cfg(self):
        self.s.base_url = self.var_base.get().strip() or self.s.base_url
        self.s.api_key = self.var_key.get().strip()
        self.s.model = self.var_model.get().strip() or self.s.model
        try:
            d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        d.update({"base_url": self.s.base_url, "api_key": self.s.api_key, "model": self.s.model,
                  "system_extra": self.txt_sys.get("1.0", "end").strip(),
                  "font_size": int(self.var_font.get())})
        d.setdefault("relap5_dir", self.s.relap5_dir)
        d.setdefault("doc_path", self.s.doc_path)
        CONFIG_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        self._apply_fonts(self.var_font.get())
        self._new_session()
        self._log("agent", f"设置已保存：{self.s.model} @ {self.s.base_url}")

    # ================= 整页滚动 =================
    def _build_scroll_body(self):
        holder = ttk.Frame(self.root)
        holder.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas_holder = holder
        self.canvas = tk.Canvas(holder, highlightthickness=0)
        vsb = ttk.Scrollbar(holder, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        body = ttk.Frame(self.canvas)
        self.body = body
        self._win = self.canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))

        self._build_params_panel(body)
        self._build_main_panel(body)

    def _on_wheel(self, event):
        # 鼠标悬停在文本控件上时，交给文本自己滚动；否则整页滚动
        try:
            w = self.root.winfo_containing(event.x_root, event.y_root)
        except Exception:
            w = None
        if isinstance(w, (tk.Text, tk.Listbox)):
            return
        self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    # ---- 左：已规范参数 ----
    def _build_params_panel(self, body):
        left = ttk.Frame(body)
        left.pack(side="left", fill="y")
        p = ttk.LabelFrame(left, text="已规范参数（需求/意图/批量框架）", padding=6)
        p.pack(fill="both", expand=True)
        self.txt_params = ScrolledText(p, width=23, height=32, wrap="word", state="disabled",
                                       font=("Consolas", 11))
        self.txt_params.pack(fill="both", expand=True)
        ttk.Button(p, text="刷新参数", command=lambda: self._refresh_params(True)).pack(anchor="e", pady=(4, 0))

    # ---- 右：对话/用量/卡片/结果 ----
    def _build_main_panel(self, body):
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        c = ttk.LabelFrame(right, text="对话", padding=6)
        c.pack(fill="both", expand=True)
        self.chat = ScrolledText(c, wrap="word", state="disabled", height=32)
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_config("你", foreground="#0a5")
        self.chat.tag_config("agent", foreground="#036")
        self.chat.tag_config("提问", foreground="#a30")
        self.chat.bind("<Double-Button-1>", lambda _e: self._glossary_sel())

        row = ttk.Frame(c)
        row.pack(fill="x", pady=(6, 0))
        self.lbl_hint = ttk.Label(row, text="输入需求：", foreground="#666")
        self.lbl_hint.pack(side="left")
        self.var_in = tk.StringVar()
        self.entry = ttk.Entry(row, textvariable=self.var_in)
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 6))
        self.entry.bind("<Return>", lambda _e: self._send())
        self.btn_send = ttk.Button(row, text="发送", command=self._send)
        self.btn_send.pack(side="left")

        u = ttk.LabelFrame(right, text="用量 / 计费", padding=6)
        u.pack(fill="x", pady=(8, 0))
        self.lbl_usage = ttk.Label(u, text="(尚无用量)", justify="left", font=("Consolas", 11))
        self.lbl_usage.pack(side="left", anchor="nw")
        ttk.Button(u, text="刷新用量", command=self._refresh_usage).pack(side="right", anchor="ne")

        self._build_card_panel(right)
        self._build_result_panel(right)

    def _build_card_panel(self, right):
        card = ttk.LabelFrame(right, text="输入卡（无注释版）", padding=6)
        card.pack(fill="x", pady=(8, 0))
        bar = ttk.Frame(card)
        bar.pack(fill="x")
        self.btn_card = ttk.Button(bar, text="▸ 展开", width=8, command=self._toggle_card)
        self.btn_card.pack(side="left")
        self.lbl_card = ttk.Label(bar, text="(暂无卡片)", foreground="#666")
        self.lbl_card.pack(side="left", padx=6)
        # 默认折叠：让对话区占主导
        self.txt_card = ScrolledText(card, height=14, wrap="none", font=("Consolas", 11))

    def _build_result_panel(self, right):
        res = ttk.LabelFrame(right, text="结果表（最近一次真跑的关键读数）", padding=6)
        res.pack(fill="both", pady=(8, 0))
        bar = ttk.Frame(res)
        bar.pack(fill="x")
        self.btn_res = ttk.Button(bar, text="▸ 展开", width=8, command=self._toggle_res)
        self.btn_res.pack(side="left")
        self.lbl_res = ttk.Label(bar, text="(尚无运行)", foreground="#666")
        self.lbl_res.pack(side="left", padx=6)
        ttk.Button(bar, text="刷新结果", command=self._refresh_res).pack(side="right")
        self.txt_res = ScrolledText(res, height=12, wrap="none", font=("Consolas", 11))
        # 默认收起：不 pack

    def _toggle_card(self):
        if self.txt_card.winfo_ismapped():
            self.txt_card.pack_forget()
            self.btn_card.configure(text="▸ 展开")
        else:
            self.txt_card.pack(fill="both", expand=True, pady=(4, 0))
            self.btn_card.configure(text="▾ 收起")

    def _toggle_res(self):
        if self.txt_res.winfo_ismapped():
            self.txt_res.pack_forget()
            self.btn_res.configure(text="▸ 展开")
        else:
            self.txt_res.pack(fill="both", expand=True, pady=(4, 0))
            self.btn_res.configure(text="▾ 收起")
            self._refresh_res()

    # ================= 字号 =================
    def _apply_fonts(self, size: int):
        try:
            size = max(8, min(26, int(size)))
        except Exception:
            size = 11
        self.var_font.set(size)
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            try:
                tkfont.nametofont(name).configure(size=size)
            except Exception:
                pass
        mono = ("Consolas", size)
        for w in (getattr(self, "chat", None), getattr(self, "txt_params", None),
                  getattr(self, "txt_card", None), getattr(self, "txt_res", None),
                  getattr(self, "lbl_usage", None)):
            if w is not None:
                try:
                    w.configure(font=mono)
                except Exception:
                    pass

    # ================= 会话历史 =================
    def _sessions_dir(self) -> Path:
        p = Path(self.s.workspace) / "sessions"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _refresh_sessions(self):
        names = sorted(p.stem for p in self._sessions_dir().glob("*.json"))
        self.cb_sess.configure(values=names)
        if self.sess_name:
            self.var_sess.set(self.sess_name)

    def _save_session(self):
        if self.sess is None or not self.sess_name:
            return
        d = {"name": self.sess_name, "state": self.sess.state(), "usage": self.usage.to_dict(),
             "model": self.s.model}
        (self._sessions_dir() / f"{self.sess_name}.json").write_text(
            json.dumps(d, ensure_ascii=False), encoding="utf-8")

    def _load_session(self, name: str):
        if not name:
            return
        f = self._sessions_dir() / f"{name}.json"
        if not f.is_file():
            return
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("读取失败", str(e))
            return
        self.sess_name = name
        self.sess = Session(self.s, system_extra=self.txt_sys.get("1.0", "end").strip())
        self.sess.restore(d.get("state", {}))
        self.usage.load(d.get("usage", {}))
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self._log("agent", f"已载入会话「{name}」。")
        self._refresh_usage()
        self._refresh_params()
        self._refresh_card()
        self._refresh_res()

    # ================= 对话 =================
    def _log(self, who: str, text: str):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\n【{who}】\n{text}\n", who)
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _set_status(self, t: str):
        self.lbl_status.configure(text=t)

    def _send(self):
        text = self.var_in.get().strip()
        if not text:
            return
        if self._pending is not None:
            self.var_in.set("")
            self._log("你", text)
            self._pending["ans"] = text
            self._pending["ev"].set()
            self._pending = None
            self.lbl_hint.configure(text="输入需求：")
            self._set_status("运行中…")
            return
        if self._busy:
            return
        self.var_in.set("")
        self._log("你", text)
        self._busy = True
        self.btn_send.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self._set_status("运行中…")
        threading.Thread(target=self._worker, args=(text,), daemon=True).start()

    def _stop(self):
        if self.sess is not None:
            self.sess.agent.cancel()
            self._set_status("已请求停止…")

    def _worker(self, text: str):
        try:
            if self.sess is None:
                if not self.sess_name:
                    self.sess_name = time.strftime("sess_%Y%m%d_%H%M%S")
                    self._refresh_sessions()
                self.sess = Session(self.s, system_extra=self.txt_sys.get("1.0", "end").strip())
            out = self.sess.send(text)
            self.q.put(("done", out))
        except Exception as e:  # noqa: BLE001
            self.q.put(("error", f"{type(e).__name__}: {e}"))

    def _asker(self, question: str) -> str:
        holder = {"ev": threading.Event(), "ans": ""}
        self.q.put(("ask", question, holder))
        holder["ev"].wait()
        return holder["ans"] or "(未回答)"

    def _drain(self):
        try:
            while True:
                kind, *rest = self.q.get_nowait()
                if kind == "ask":
                    question, holder = rest
                    self._pending = holder
                    self._log("提问", question)
                    self.lbl_hint.configure(text="请回答上面的问题（或直接反问）：")
                    self.btn_send.configure(state="normal")
                    self._set_status("等待你的回答")
                    self.entry.focus_set()
                elif kind == "done":
                    out = rest[0]
                    self._busy = False
                    self.btn_send.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    self._log("agent", out.say or "(无最终答复)")
                    if out.stopped:
                        self._log("agent", f"[终止] {out.stopped}")
                    if out.trace and self.var_trace.get():
                        self._log("agent", "[工具轨迹] " + " | ".join(t["tool"] for t in out.trace))
                    if out.usage:
                        self.usage.add(out.usage, self.var_model.get() or self.s.model, self._prices())
                    self._refresh_usage()
                    self._refresh_params()
                    self._refresh_card()
                    if self.txt_res.winfo_ismapped():
                        self._refresh_res()
                    self._save_session()
                    self._set_status("就绪")
                elif kind == "error":
                    self._busy = False
                    self.btn_send.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    self._log("agent", f"[错误] {rest[0]}")
                    self._set_status("就绪")
        except queue.Empty:
            pass
        self.root.after(80, self._drain)

    # ================= 已规范参数（实时） =================
    def _refresh_params(self, force: bool = False):
        if self.sess is None:
            txt, sig = "(尚无。开始对话后，agent 确认的需求/意图/批量框架会实时显示在这里。)", None
        else:
            parts = (self.sess.requirements_text(), self.sess.intent_text(), self.sess.batch_text())
            txt = (f"【已确认需求】\n{parts[0]}\n\n【建模意图】\n{parts[1]}\n\n【批量框架】\n{parts[2]}")
            sig = repr(parts)
        if not force and sig == self._params_sig:      # 无变化就不重绘
            return
        self._params_sig = sig
        self.txt_params.configure(state="normal")
        self.txt_params.delete("1.0", "end")
        self.txt_params.insert("1.0", txt)
        self.txt_params.configure(state="disabled")

    def _poll_params(self):
        # 实时：agent 一记下参数（remember_requirement / set_model_intent / set_batch_plan）
        # 就立刻刷新，不等整轮结束。
        try:
            self._refresh_params()
        except Exception:  # noqa: BLE001
            pass
        self.root.after(400, self._poll_params)

    # ================= 卡片 / 结果 =================
    def _artifact_path(self):
        if self.sess is None or not self.sess.meta.get("artifacts"):
            return None
        rel = self.sess.meta["artifacts"][-1].replace("\\", "/")
        if rel.startswith("workspace/"):
            rel = rel[len("workspace/"):]
        return Path(self.s.workspace) / rel

    @staticmethod
    def _strip_comments(text: str) -> str:
        return "\n".join(ln.rstrip() for ln in text.splitlines()
                         if ln.strip() and ln.strip()[0] not in ("*", "="))

    def _refresh_card(self):
        p = self._artifact_path()
        self.lbl_card.configure(text=p.name if p else "(暂无卡片)")
        self.txt_card.configure(state="normal")
        self.txt_card.delete("1.0", "end")
        if p:
            try:
                self.txt_card.insert("1.0", self._strip_comments(p.read_text(encoding="utf-8")))
            except Exception as e:  # noqa: BLE001
                self.txt_card.insert("1.0", f"(读取失败: {e})")
        self.txt_card.configure(state="disabled")

    def _last_o(self):
        if self.sess is None or not self.sess.meta.get("last_o"):
            return None
        rel = self.sess.meta["last_o"].replace("\\", "/")
        if rel.startswith("workspace/"):
            rel = rel[len("workspace/"):]
        return rel

    def _refresh_res(self):
        rel = self._last_o()
        self.lbl_res.configure(text=rel or "(尚无运行)")
        self.txt_res.configure(state="normal")
        self.txt_res.delete("1.0", "end")
        if rel:
            try:
                txt = registry.call("result_summary", {"o_path": rel})
                txt += "\n\n" + registry.call("transient_history", {"o_path": rel, "what": "flow"})
                self.txt_res.insert("1.0", txt)
            except Exception as e:  # noqa: BLE001
                self.txt_res.insert("1.0", f"(读取失败: {e})")
        self.txt_res.configure(state="disabled")

    # ================= 环境检测 =================
    def _env_check(self):
        win = tk.Toplevel(self.root)
        win.title("环境检测")
        win.geometry("640x460")

        def render():
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            try:
                rows = envcheck.check()
                txt.insert("1.0", envcheck.summary(rows))
            except Exception as e:  # noqa: BLE001
                txt.insert("1.0", f"检测出错：{type(e).__name__}: {e}")
            txt.configure(state="disabled")

        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="重新检测", command=render).pack(side="left")
        ttk.Label(bar, text="✓ 通过  ✗ 需处理", foreground="#666").pack(side="left", padx=10)
        txt = ScrolledText(win, wrap="word", font=("Consolas", 11))
        txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        render()

    # ================= 术语速查 =================
    def _glossary_sel(self):
        try:
            sel = self.chat.get("sel.first", "sel.last").strip()
        except tk.TclError:
            sel = ""
        if not sel:
            self._log("agent", "（术语速查：请先在对话区选中一个词，再点『术语速查』或双击。）")
            return
        term = sel.splitlines()[0][:40]
        res = registry.call("glossary", {"term": term})
        self._log("agent", f"[术语] {term}\n{res}")

    # ================= 导出 =================
    def _export_chat(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("文本", "*.txt"), ("Markdown", "*.md")],
                                            initialfile=(self.sess_name or "relap5_session") + ".txt")
        if not path:
            return
        Path(path).write_text(self.chat.get("1.0", "end"), encoding="utf-8")
        self._log("agent", f"已导出会话 → {path}")

    def _export_card(self):
        p = self._artifact_path()
        if not p or not p.is_file():
            return
        path = filedialog.asksaveasfilename(defaultextension=".i",
                                            filetypes=[("RELAP5 输入卡", "*.i")], initialfile=p.name)
        if not path:
            return
        Path(path).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        self._log("agent", f"已导出卡片 → {path}")

    # ================= 用量 =================
    def _set_usage_text(self, t: str):
        self.lbl_usage.configure(text=t)

    def _refresh_usage(self):
        self._set_usage_text(self.usage.summary(self.var_model.get() or self.s.model, self._prices()))

    def _prices(self) -> dict:
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("prices", {}) or {}
        except Exception:
            return {}

    def _greet(self):
        self._log("agent", random.choice(OPENERS))

    def _new_session(self):
        self._save_session()
        self.sess = None
        self.sess_name = ""
        self.var_sess.set("")
        self.usage.reset()
        self._refresh_usage()
        self._refresh_params()
        self._refresh_card()
        self._refresh_res()
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self._greet()


def main() -> int:
    # Windows：给本进程设 AppUserModelID，使**任务栏**用本程序图标（而非 python 的）
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DeckSmith.RELAP5.Agent")
    except Exception:  # noqa: BLE001
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
