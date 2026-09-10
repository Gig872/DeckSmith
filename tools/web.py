# -*- coding: utf-8 -*-
"""通用联网工具：web_search（搜索）+ web_fetch（抓正文）。零第三方依赖。

搜索默认用 DuckDuckGo（免 key）；如不稳，可换带 key 的服务（见 config: search_api）。
"""
from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request

from registry import tool

_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _get(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers=_UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def _strip_tags(s: str) -> str:
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def _first(pat: str, s: str) -> str:
    m = re.search(pat, s, re.S)
    return _strip_tags(m.group(1)) if m else ""


@tool("web_search", "联网搜索，返回结果的标题、链接与**正文摘要**（摘要用于快速判断，深读用 web_fetch）。",
      {"query": {"type": "string", "description": "搜索词"},
       "n": {"type": "integer", "description": "返回条数，默认5"}}, ["query"])
def web_search(query: str, n: int = 5) -> str:
    q = urllib.parse.quote(query)
    k = max(1, int(n))
    endpoints = [
        (f"https://www.bing.com/search?q={q}", "bing"),      # 本机可达
        (f"https://html.duckduckgo.com/html/?q={q}", "ddg"),  # 备用
    ]
    for ep, kind in endpoints:
        try:
            h = _get(ep)
        except Exception:
            continue
        out = []
        if kind == "bing":
            for b in re.findall(r'<li class="b_algo".*?</li>', h, re.S)[:k]:
                m = re.search(r'<h2[^>]*>\s*<a[^>]*href="(http[^"]+)"[^>]*>(.*?)</a>', b, re.S)
                if not m:
                    continue
                link, title = m.group(1), m.group(2)
                snip = _first(r'<p[^>]*>(.*?)</p>', b) or _first(r'class="b_caption".*?>(.*?)</', b)
                out.append(f"- {_strip_tags(title)}\n  {link}\n  摘要: {snip[:400]}")
            if not out:   # 退回旧的标题匹配
                for link, title in re.findall(r'<h2[^>]*>\s*<a[^>]*href="(http[^"]+)"[^>]*>(.*?)</a>', h, re.S)[:k]:
                    out.append(f"- {_strip_tags(title)}\n  {link}")
        else:  # ddg
            for b in re.findall(r'<div class="result[^"]*".*?</div>\s*</div>', h, re.S)[:k]:
                m = re.search(r'result__a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b, re.S)
                if not m:
                    continue
                link, title = m.group(1), m.group(2)
                mm = re.search(r"uddg=([^&]+)", link)
                if mm:
                    link = urllib.parse.unquote(mm.group(1))
                snip = _first(r'result__snippet[^>]*>(.*?)</a>', b)
                out.append(f"- {_strip_tags(title)}\n  {link}\n  摘要: {snip[:400]}")
        if out:
            return "\n\n".join(out)
    return "[web_search] 未取到结果（网络或反爬受限）。"


@tool("web_fetch", "抓取一个网页的正文（去标签，截断）。对 web_search 里最有用的链接深读时使用。",
      {"url": {"type": "string"}, "max_chars": {"type": "integer"}}, ["url"])
def web_fetch(url: str, max_chars: int = 4000) -> str:
    try:
        return _strip_tags(_get(url))[: int(max_chars)]
    except Exception as e:
        return f"[web_fetch] 失败: {e}"
