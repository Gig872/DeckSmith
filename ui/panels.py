# -*- coding: utf-8 -*-
"""PanelsMixin：已规范参数（实时）/ 输入卡（无注释）/ 结果表。"""
from __future__ import annotations

from pathlib import Path

import registry


class PanelsMixin:
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
                txt = registry.call("verify_result", {"o_path": rel})   # 自主评估（独立复核）
                txt += "\n\n" + registry.call("result_summary", {"o_path": rel})
                txt += "\n\n" + registry.call("transient_history", {"o_path": rel, "what": "flow"})
                self.txt_res.insert("1.0", txt)
            except Exception as e:  # noqa: BLE001
                self.txt_res.insert("1.0", f"(读取失败: {e})")
        self.txt_res.configure(state="disabled")
