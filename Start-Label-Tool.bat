@echo off
chcp 65001 >nul
title DHL Label Tool

if "%~1"=="" goto run_gui

:run_batch
echo ========================================================
echo DHL Label Tool - Stapelverarbeitung
echo ========================================================
echo.
python "%~dp0dhl_label_splitter.py" --batch %*
echo.
echo ========================================================
echo Fertig! Alle Labels wurden randlos gespeichert.
echo ========================================================
echo.
ping 127.0.0.1 -n 4 >nul
exit /b 0

:run_gui
start "" python "%~dp0dhl_label_splitter.py"
exit /b 0
