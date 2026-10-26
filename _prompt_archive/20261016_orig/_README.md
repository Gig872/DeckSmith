# 原始提示词存档（2026-10-16，改动前）

用途：本次为试验「agent 自我分段」而修改 `skills/20_workflow.md`，先把原版存档，保证可回档。

## 回档方法
```
C:/python/python.exe -c "import glob,shutil,os;d=r'C:\\relap-5\\agent-kit\\_prompt_archive\\20261016_orig';t=r'C:\\relap-5\\agent-kit';[shutil.copy2(f, os.path.join(t,'core.py' if os.path.basename(f)=='core.py' else 'skills', os.path.basename(f))) for f in glob.glob(os.path.join(d,'*.md'))+glob.glob(os.path.join(d,'*.py'))]"
```
（`_MANIFEST.md5` 列出每个文件的 md5，回档后可逐条核对。）
