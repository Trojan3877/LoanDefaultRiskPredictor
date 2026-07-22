FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home /app app

COPY requirements/runtime.txt ./requirements/runtime.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --requirement requirements/runtime.txt

COPY --chown=app:app api ./api
COPY --chown=app:app src ./src
COPY --chown=app:app evaluation ./evaluation

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=2)"

CMD ["uvicorn", "api.inference_api:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--workers", "1"]
