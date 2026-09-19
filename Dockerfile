# Backend image for Pavo Cloud (FastAPI + the ZK layer).
#
# Two runtimes on purpose: the prover in backend/app/zk/prover.py shells out to
# `node` to run snarkjs. On a Python-only host every /zk call answers 503 and
# demo step 3 goes red, so Node is not optional here.
#
# Build context is the REPOSITORY ROOT, not backend/ — the image needs zk/ too.
FROM python:3.11-slim-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends nodejs npm ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# snarkjs and circomlib only. The proving/verifying artifacts (.wasm, .zkey,
# verification_key.json) are committed, so nothing is compiled at build time.
COPY zk/package.json zk/package-lock.json ./zk/
RUN cd zk && npm ci --omit=dev

COPY zk ./zk
COPY backend ./backend

ENV PYTHONUNBUFFERED=1

# prover.py resolves zk/ as parents[3] of backend/app/zk/prover.py, which is
# /app here. Keep backend/ one level under /app or the artifacts go missing.
WORKDIR /app/backend

# Render (and most hosts) inject PORT; 8000 is the local default.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
