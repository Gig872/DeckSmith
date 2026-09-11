# dev/ —— 开发与验证脚本（非单元测试）

这里是一次性/集成性质的手动脚本（需要 **API Key** 或 **RELAP5** 才能跑），用于开发期的端到端验证；
**不参与 CI**。标准单元测试见仓库根的 `tests/`。

## 运行方式（重要）

这些脚本 `import registry/core/config` 等顶层模块，**必须让仓库根目录在 `sys.path`**。所以：

```bat
REM 在仓库根目录 C:\relap-5\agent-kit 下执行：
set PYTHONPATH=.
python dev\test_hard2.py
```

或直接：
```bat
cd C:\relap-5\agent-kit
python -c "import sys; sys.path.insert(0,'.'); exec(open('dev/test_hard2.py',encoding='utf-8').read())"
```

> 从 `dev/` 目录**直接** `python test_x.py` 会报 `ModuleNotFoundError: registry`——这是预期，按上面加 `PYTHONPATH=.` 即可。

## 脚本一览（示例）
- `test_session.py` 多轮会话 / 引导澄清
- `test_hard*.py` 硬题（失流/失水/沸腾/CHF/临界流/一二次回路）
- `test_corpus*.py` 自主构建参考库
- `verify_ref.py` 复跑核验参考库
- `test_budget.py` 目标自适应预算
