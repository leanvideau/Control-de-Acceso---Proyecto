@echo off
cd /d "%~dp0"
python actualizar.py
pip install -q -r requirements.txt
python sincronizar.py --preguntar-dias --cargar
pause
