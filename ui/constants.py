# -*- coding: utf-8 -*-
"""界面常量：供应商预设、默认模型提示、开场白。"""

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

# 变量中文名（仅用于界面显示，变量名本身不变）
VAR_LABELS = {
    "pressure": "压力",
    "voidf": "液相份额",
    "voidg": "空泡份额",
    "voidgo": "初始空泡份额",
    "tempf": "液相温度",
    "tempg": "气相温度",
    "mass_flow": "质量流量",
    "liq_vel": "液相速度",
    "vap_vel": "气相速度",
    "area": "流通面积",
}


def var_label(v: str) -> str:
    """给变量名附上中文：`voidg（空泡份额）`。"""
    cn = VAR_LABELS.get(v)
    return f"{v}（{cn}）" if cn else str(v)

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
