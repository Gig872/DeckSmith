# -*- coding: utf-8 -*-
"""ChatMixin：对话渲染、发送/停止/worker、事件泵、会话生命周期。"""
from __future__ import annotations

import queue
import random
import threading
import time

from core import Session
from .constants import OPENERS, var_label
from .events import fmt_event


class ChatMixin:
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
        if not (self.var_model.get().strip() or self.s.model):
            self._log("agent", "请先在『⚙ 设置』里选择/填写模型（可点『获取模型』从接口拉取）并保存，再开始。")
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
            self.sess.agent.event_cb = self._on_event   # 实时把 思考/工具 事件推给界面
            out = self.sess.send(text)
            self.q.put(("done", out))
        except Exception as e:  # noqa: BLE001
            self.q.put(("error", f"{type(e).__name__}: {e}"))

    def _asker(self, question: str) -> str:
        holder = {"ev": threading.Event(), "ans": ""}
        self.q.put(("ask", question, holder))
        holder["ev"].wait()
        return holder["ans"] or "(未回答)"

    def _maybe_auto_plot(self, name, args):
        """agent 出图/读图 → 自动弹「结果图」窗口（视图菜单可关；同一 (o,var) 去重）。"""
        if not self.var_auto_plot.get() or name not in ("plot_series", "curve_features"):
            return
        a = args if isinstance(args, dict) else {}
        o, var = a.get("o_path"), a.get("var")
        if not o or not var:
            return
        key = (str(o), str(var))
        if key in self._auto_opened:
            return
        self._auto_opened.add(key)
        self._open_plot_window_for(o, var)
        self._log("agent", f"（已弹出结果图窗口：{var_label(var)}）")

    def _drain(self):
        try:
            while True:
                kind, *rest = self.q.get_nowait()
                if kind == "ev":
                    ev_kind, data = rest
                    line = fmt_event(ev_kind, data)
                    if line:
                        self._events.append(line)
                        if len(self._events) > 3000:
                            self._events = self._events[-2000:]
                        if self._think_txt and self._think_win and self._think_win.winfo_exists():
                            self._think_txt.insert("end", line + "\n")
                            self._think_txt.see("end")
                    # agent 出图 → 自动弹「结果图」窗口（视图菜单可关）
                    if ev_kind == "tool":
                        self._maybe_auto_plot(data.get("name"), data.get("args"))
                elif kind == "ask":
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
                    # 兜底：若实时事件漏了出图，本轮结束仍把图弹出来
                    for t in (out.trace or []):
                        if t.get("tool") in ("plot_series", "curve_features"):
                            self._maybe_auto_plot(t.get("tool"), t.get("args"))
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

    # ================= 生命周期 =================
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
        self._clear_thinking()
        self._greet()
