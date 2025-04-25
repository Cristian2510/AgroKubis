@echo off
echo Activando entorno virtual...
call venv\Scripts\activate

echo Iniciando aplicación Flask en modo desarrollo...
python app.py
pause
