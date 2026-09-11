@echo off
REM 卡匠 DeckSmith —— 打包为单个 exe（Windows）。需先： pip install pyinstaller
REM   build_exe.bat         基础版（纯标准库，零依赖；出图用内置 Canvas）
REM   build_exe.bat mpl     带 matplotlib 的构建（可导出精细 PNG；体积更大）
REM 生成：dist\DeckSmith.exe
setlocal
cd /d "%~dp0"

set MPL_OPTS=
if /I "%~1"=="mpl" set MPL_OPTS=--collect-all matplotlib --collect-all numpy --hidden-import matplotlib.backends.backend_agg

pyinstaller --noconfirm --onefile --windowed --name DeckSmith ^
  --icon assets\icon.ico ^
  --collect-submodules tools ^
  %MPL_OPTS% ^
  --add-data "skills;skills" ^
  --add-data "knowledge;knowledge" ^
  --add-data "assets;assets" ^
  decksmith.py

echo.
if defined MPL_OPTS (echo 已打包 **带 matplotlib** 版本。) else (echo 已打包 **基础版** ^(零依赖，Canvas 出图^)。如需精细 PNG 请用: build_exe.bat mpl)
echo exe 在 dist\DeckSmith.exe
echo 说明：exe 首次运行会在**其所在目录**自动生成 config.json（空 key）与 workspace/；
echo       让测试者填自己的 API Key / 模型，并把 relap5_dir 指向其 RELAP5 安装（或用界面/环境变量 RELAP5_DIR）。
pause
