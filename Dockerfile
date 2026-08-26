FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Patch security-sensitive OS libraries exposed by the slim base image before
# installing application dependencies. Keep package-manager caches out of the
# final layer.
RUN apt-get update \
    && apt-get install --only-upgrade -y --no-install-recommends \
       openssl libssl3t64 openssl-provider-legacy \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home /app app

COPY requirements/runtime.txt ./requirements/runtime.txt

# Build tooling is required only while installing wheels. Upgrade it past known
# vulnerable versions, install runtime dependencies, then remove packaging tools
# from the final image so they are not part of the runtime attack surface.
RUN python -m pip install --upgrade \
      "pip>=26.2.1,<27" \
      "setuptools>=80.9,<81" \
      "wheel>=0.46.2,<0.47" \
      "jaraco.context>=6.1,<7" \
    && python -m pip install --requirement requirements/runtime.txt \
    && python -m pip uninstall -y pip setuptools wheel jaraco.context

COPY --chown=app:app api ./api
COPY --chown=app:app src ./src
COPY --chown=app:app evaluation ./evaluation

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=2)"

CMD ["uvicorn", "api.inference_api:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--workers", "1"]
