@echo off
rem Abre o prototipo no navegador. Feche esta janela para parar.
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Criando o ambiente Python pela primeira vez...
  python -m venv .venv
  .venv\Scripts\pip install -r requirements-dev.txt
)
set TAILWINDCSS_VERSION=v4.3.4
set FLASK_CONFIG=development
.venv\Scripts	ailwindcss -i app/static/src/app.css -o app/static/dist/app.css --minify
echo.
echo Prototipo no ar. No computador: http://127.0.0.1:5000/prototipo/
echo No celular (mesmo Wi-Fi), use o endereco "http://<IP deste computador>:5000/prototipo/"
echo que aparece abaixo, na linha que NAO comeca com 127.0.0.1.
echo.
start "" http://127.0.0.1:5000/prototipo/
.venv\Scriptslask run --host 0.0.0.0 --port 5000
