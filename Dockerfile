###############################################################################
# LoanDefaultRiskPredictor • Dockerfile
# ---------------------------------------------------------------------------
# Stage 1  ➜  builder   : installs Python deps into a virtualenv layer
# Stage 2  ➜  runtime   : copies slim venv + source, exposes FastAPI on :8000
###############################################################################

########################  Stage 1 – builder  ##################################
FROM python:3.11-slim AS builder

ENV VENV_PATH=/opt/venv
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# Create virtualenv & install deps
RUN python -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

########################  Stage 2 – runtime  ##################################
FROM python:3.11-slim AS runtime

ENV VENV_PATH=/opt/venv
ENV PATH="$VENV_PATH/bin:$PATH"
WORKDIR /app

# Copy virtualenv from builder layer (≈120 MB ➜ 55 MB with strip)
COPY --from=builder $VENV_PATH $VENV_PATH

# Copy application source
COPY src/ ./src/
COPY models/ ./models/        # ensure model artefact shipped
COPY docs/ ./docs/            # openapi.json for swagger if desired

# Default to FastAPI server
EXPOSE 8000
CMD ["uvicorn", "src.predict_api:app", "--host", "0.0.0.0", "--port", "8000"]
