# -*- coding: utf-8 -*-
"""SettingsMixin：设置面板（AI 接入 + 全局提示词 + 思考模式）与配置读写。"""
from __future__ import annotations

import json
import threading
import tkinter as tk
from tkinter import ttk

from config import CONFIG_FILE
from .constants import PROVIDERS, MODEL_HINTS


class SettingsMixin:
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
        # 不预设：打开设置/换供应商时**向接口查询可用模型**填入候选；也可自己输入。
        self.cb_model = ttk.Combobox(f, textvariable=self.var_model, values=[], width=36)
        self.cb_model.grid(row=3, column=1, sticky="w", pady=2)
        ttk.Button(f, text="获取模型", width=9, command=self._fetch_models).grid(
            row=3, column=2, sticky="w", padx=(8, 0))
        # 模型行为：思考模式（与上面的接入配置同属"模型"类）
        ttk.Checkbutton(f, text="思考模式（开启模型思维链，更慢更贵）",
                        variable=self.var_thinking, command=self._on_thinking).grid(
            row=4, column=1, columnspan=3, sticky="w", pady=(2, 0))
        ttk.Label(f, text="全局提示词").grid(row=5, column=0, sticky="nw", pady=(6, 2))
        self.txt_sys = tk.Text(f, width=58, height=4, wrap="word")
        self.txt_sys.grid(row=5, column=1, columnspan=3, sticky="we", pady=(6, 2))
        bb = ttk.Frame(f)
        bb.grid(row=6, column=0, columnspan=4, sticky="we", pady=(4, 0))
        ttk.Button(bb, text="保存设置", command=self._save_cfg).pack(side="left")
        ttk.Label(bb, text="价格表(config.json 的 prices)：每 1M token 输入/输出，示例值可改。",
                  foreground="#666").pack(side="left", padx=10)
        f.columnconfigure(1, weight=1)

    def _toggle_settings(self):
        if self._settings_open:
            self.settings_frame.pack_forget()
        else:
            self.settings_frame.pack(fill="x", padx=8, pady=(6, 0), before=self.canvas_holder)
            self._fetch_models()          # 打开设置即**主动查询**可用模型
        self._settings_open = not self._settings_open

    def _on_provider(self, _evt=None):
        p = self.var_provider.get()
        if PROVIDERS.get(p):
            self.var_base.set(PROVIDERS[p])
        self._fetch_models()              # 换供应商即查询该接口的模型

    def _on_thinking(self):
        self.s.thinking = bool(self.var_thinking.get())   # 立即生效（下次调用即用）

    def _fetch_models(self):
        """向 base_url 的 /models 查询可用模型（后台线程，避免卡界面）。"""
        base = self.var_base.get().strip()
        key = self.var_key.get().strip()
        if not base:
            return
        self._set_status("正在获取模型列表…")

        def work():
            try:
                from llm import list_models
                ids, err = list_models(base, key), ""
            except Exception as e:  # noqa: BLE001
                ids, err = [], f"{type(e).__name__}: {e}"
            self.root.after(0, lambda: self._apply_models(ids, err))

        threading.Thread(target=work, daemon=True).start()

    def _apply_models(self, ids, err):
        if ids:
            self.cb_model.configure(values=ids)
            if not self.var_model.get():
                self.var_model.set(ids[0])
            self._set_status(f"模型列表已更新（{len(ids)} 个）")
            self._log("agent", f"已从接口获取 {len(ids)} 个模型，可在『模型』下拉里选择。")
        else:
            self._set_status("就绪")
            if not self.var_model.get():
                hint = MODEL_HINTS.get(self.var_provider.get())
                if hint:
                    self.var_model.set(hint)
            self._log("agent", f"获取模型列表失败：{err or '接口未返回列表'}（可直接手输模型名）")

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
        self.var_thinking.set(bool(cfg.get("thinking", self.s.thinking)))
        self.s.thinking = bool(self.var_thinking.get())

    def _save_cfg(self):
        self.s.base_url = self.var_base.get().strip() or self.s.base_url
        self.s.api_key = self.var_key.get().strip()
        self.s.model = self.var_model.get().strip() or self.s.model
        self.s.thinking = bool(self.var_thinking.get())
        try:
            d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        d.update({"base_url": self.s.base_url, "api_key": self.s.api_key, "model": self.s.model,
                  "system_extra": self.txt_sys.get("1.0", "end").strip(),
                  "thinking": bool(self.var_thinking.get())})
        d.setdefault("relap5_dir", self.s.relap5_dir)
        d.setdefault("doc_path", self.s.doc_path)
        CONFIG_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        self._new_session()
        self._log("agent", f"设置已保存：{self.s.model} @ {self.s.base_url}")
