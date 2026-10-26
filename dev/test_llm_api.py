import sys, time, json
sys.path.insert(0, r"C:\relap-5\agent-kit")
from config import load
from llm import LLM, LLMError, OutOfCredit
s = load()
print("base_url:", s.base_url)
print("model:", s.model)
print("key_len:", len(s.api_key or ""))
t0=time.time()
try:
    l = LLM(s)
    msg = l.complete([{"role":"user","content":"Say OK"}])
    print("OK call. content:", repr(msg.get("content"))[:200])
    print("usage:", l.last_usage)
except OutOfCredit as e:
    print("OUT_OF_CREDIT:", str(e)[:300])
except LLMError as e:
    print("LLM_ERROR:", str(e)[:300])
except Exception as e:
    print("OTHER:", type(e).__name__, str(e)[:300])
print("elapsed", round(time.time()-t0,2))
