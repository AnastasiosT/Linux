
FROM python:3.11-slim
 
LABEL maintainer="you@example.com" \
      description="NetApp ONTAP REST API mock for CheckMK testing"
 
# ── System deps (openssl for cert generation, curl for healthcheck) ──────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssl curl \
    && rm -rf /var/lib/apt/lists/*
 
WORKDIR /app
 
# ── Python deps ───────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# ── Application ───────────────────────────────────────────────────────────────
COPY app.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
 
EXPOSE 443
 
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -fsk https://localhost/api/cluster >/dev/null || exit 1
 
ENTRYPOINT ["/app/entrypoint.sh"]
 
