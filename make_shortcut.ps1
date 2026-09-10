# 生成带图标的启动快捷方式（Windows）。用法： powershell -ExecutionPolicy Bypass -File make_shortcut.ps1
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyw  = Join-Path $env:SystemDrive "python\pythonw.exe"
if (-not (Test-Path $pyw)) { $pyw = (Get-Command pythonw.exe).Source }

$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut((Join-Path $here "卡匠 DeckSmith.lnk"))
$lnk.TargetPath       = $pyw
$lnk.Arguments        = "decksmith.py"
$lnk.WorkingDirectory  = $here
$lnk.IconLocation      = (Join-Path $here "assets\icon.ico")
$lnk.Description       = "卡匠 DeckSmith · RELAP5 建模智能体"
$lnk.Save()
Write-Output ("已创建快捷方式: " + (Join-Path $here "卡匠 DeckSmith.lnk"))
