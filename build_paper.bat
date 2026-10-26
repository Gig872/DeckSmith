@echo off
REM 卡匠 DeckSmith —— 论文版冻结包（2026-10-21）
REM 与 build_exe.bat 的差别：knowledge/ 不进 exe，而是放在 exe 同目录。
REM   原因：打包进 exe 时参考库落在 PyInstaller 的临时解包目录，save_example(lib="agent")
REM   会写进临时目录并在退出后丢失；放在同目录则可写、可检查、可备份。
REM 产物：dist_paper\DeckSmith.exe + dist_paper\knowledge\（490 张样例）
setlocal
cd /d "%~dp0"

echo [1/3] 装配样例库（bench/eval_lib -> _pkg/knowledge）
if exist _pkg rmdir /s /q _pkg
mkdir _pkg\knowledge\reference\human
mkdir _pkg\knowledge\reference\agent
mkdir _pkg\knowledge\learned
xcopy /q /y bench\eval_lib\reference\human\*.i _pkg\knowledge\reference\human\ >nul
xcopy /q /y bench\eval_lib\reference\agent\*.i _pkg\knowledge\reference\agent\ >nul
xcopy /q /y bench\eval_lib\learned_seed\*.i _pkg\knowledge\learned\ >nul

echo [2/3] 打包 exe
if exist dist_paper rmdir /s /q dist_paper
if exist build_paper rmdir /s /q build_paper
pyinstaller --noconfirm --onefile --windowed --name DeckSmith ^
  --icon "%CD%\assets\icon.ico" ^
  --collect-submodules tools ^
  --exclude-module matplotlib --exclude-module numpy ^
  --add-data "%CD%\skills;skills" ^
  --add-data "%CD%\assets;assets" ^
  --distpath "%CD%\dist_paper" ^
  --workpath "%CD%\build_paper" ^
  --specpath "%CD%\build_paper" ^
  "%CD%\decksmith.py"

echo [3/3] 装配发布目录
xcopy /q /e /y _pkg\knowledge dist_paper\knowledge\ >nul
copy /y config.example.json dist_paper\ >nul

echo.
echo 完成：dist_paper\DeckSmith.exe（exe + knowledge 同目录）
echo 首次运行会在 dist_paper\ 下生成 config.json 与 workspace\。
pause
