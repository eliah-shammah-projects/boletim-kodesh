# Imagem de desenvolvimento. A de produção (gunicorn, pango, fontes) vem na Fase 4.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TAILWINDCSS_VERSION=v4.3.4
WORKDIR /app

FROM base AS dev
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY . .
# Baixa o binário do Tailwind (fixado acima) e compila o CSS.
RUN tailwindcss -i app/static/src/app.css -o app/static/dist/app.css --minify
EXPOSE 5000
CMD ["flask", "run", "--debug", "--host", "0.0.0.0", "--port", "5000"]
