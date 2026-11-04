# Imagem de desenvolvimento. A de produção (gunicorn, pango, fontes) vem na Fase 4.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

FROM base AS dev
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY . .
EXPOSE 5000
CMD ["flask", "run", "--debug", "--host", "0.0.0.0", "--port", "5000"]
