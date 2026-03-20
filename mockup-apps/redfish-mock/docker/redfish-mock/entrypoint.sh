#!/bin/bash
# entrypoint.sh — generate TLS certificate if missing, then launch gunicorn
set -euo pipefail

CERT_FILE="/app/cert.pem"
KEY_FILE="/app/key.pem"

# ── TLS certificate ───────────────────────────────────────────────────────────
if [[ ! -f "$CERT_FILE" ]]; then
    echo "[entrypoint] Generating self-signed TLS certificate (10-year validity) ..."

    SANS="DNS:redfish-mock,DNS:localhost,IP:127.0.0.1"
    if [[ -n "${EXTRA_SANS:-}" ]]; then
        SANS="${SANS},${EXTRA_SANS}"
    fi

    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout "$KEY_FILE" \
        -out  "$CERT_FILE" \
        -days 3650 \
        -subj "/CN=redfish-mock" \
        -addext "subjectAltName=${SANS}"

    echo "[entrypoint] Certificate ready. SANs: ${SANS}"
fi

exec gunicorn \
    --bind 0.0.0.0:443 \
    --workers 1 \
    --access-logfile - \
    --certfile "$CERT_FILE" \
    --keyfile  "$KEY_FILE" \
    app:app
