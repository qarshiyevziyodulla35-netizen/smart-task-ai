@echo off
chcp 65001 >nul
title SmartTask AI - Telegram Mini App Tunneli
cls
python "%~dp0tunnel.py"
pause
