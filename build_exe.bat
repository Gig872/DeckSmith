@echo off
REM 卡匠 DeckSmith —— 打包为单个 exe（Windows）。需先： pip install pyinstaller
REM 生成：dist\DeckSmith.exe
cd /d "%~dp0"

pyinstaller --noconfirm --onefile --windowed --name DeckSmith ^
  --icon assets\icon.ico ^
  --collect-submodules tools ^
  --add-data "skills;skills" ^
  --add-data "knowledge;knowledge" ^
  --add-data "assets;assets" ^
  decksmith.py

echo.
echo 完成。exe 在 dist\DeckSmith.exe
echo 说明：exe 首次运行会在**其所在目录**自动生成 config.json（空 key）与 workspace/；
echo       让测试者填自己的 API Key / 模型，并把 relap5_dir 指向其 RELAP5 安装（或用界面/环境变量 RELAP5_DIR）。
pause
