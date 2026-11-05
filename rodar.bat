@echo off
rem Abre o sistema no navegador. Feche esta janela para parar.
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Criando o ambiente Python pela primeira vez...
  python -m venv .venv
  .venv\Scripts\pip install -r requirements-dev.txt
)
set TAILWINDCSS_VERSION=v4.3.4
set FLASK_CONFIG=development
.venv\Scripts\pip install -q -r requirements-dev.txt
.venv\Scripts	ailwindcss -i app/static/src/app.css -o app/static/dist/app.css --minify
rem Banco local: cria e atualiza; na primeira vez, carrega os dados de exemplo.
.venv\Scriptslask db upgrade
if not exist instance\seeded.txt (
  .venv\Scriptslask seed && echo ok> instance\seeded.txt
)
echo.
echo Sistema no ar: http://127.0.0.1:5000/
echo Prototipo (telas de exemplo): http://127.0.0.1:5000/prototipo/
echo.
start "" http://127.0.0.1:5000/
.venv\Scriptslask run --host 0.0.0.0 --port 5000
