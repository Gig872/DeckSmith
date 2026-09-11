# -*- coding: utf-8 -*-
"""SessionsMixin：多会话历史的存/列/切换。"""
from __future__ import annotations

import json
from pathlib import Path
from tkinter import messagebox

from core import Session


class SessionsMixin:
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
        self._clear_thinking()
        self._log("agent", f"已载入会话「{name}」。")
        self._refresh_usage()
        self._refresh_params()
        self._refresh_card()
        self._refresh_res()
