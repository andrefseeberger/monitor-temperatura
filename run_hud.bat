@echo off
set PYTHON_EXE=pythonw

REM Ajuste o caminho do script se não estiver no mesmo diretório
set SCRIPT_PATH=%~dp0simple_temp_hud.py

REM "%PYTHON_EXE%" "%SCRIPT_PATH%"
powershell -Command "Start-Process '%PYTHON_EXE%' -ArgumentList '%~dp0simple_temp_hud.py' -Verb RunAs"
