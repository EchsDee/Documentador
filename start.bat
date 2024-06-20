@echo off
:loop
python documentador.py
timeout /t 43200 /nobreak >nul
goto loop