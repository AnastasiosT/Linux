#!/usr/bin/env bash
# entrypoint.sh — generate TLS certificate if missing, then launch gunicorn
set -euo pipefail

CERT_DIR="/app/certs"
CERT_FILE="${CERT_DIR}/cert.pem"
KEY_FILE="${CERT_DIR}/key.pem"

# ── TLS certificate ───────────────────────────────────────────────────────────
mkdir -p "${CERT_DIR}"

if [[ ! -f "${CERT_FILE}" ]] || [[ ! -f "${KEY_FILE}" ]]; then
    echo "[entrypoint] Generating self-signed TLS certificate (10-year validity) …"

    SANS="DNS:netapp-mock,DNS:localhost,IP:127.0.0.1"
    if [[ -n "${EXTRA_SANS:-}" ]]; then
        SANS="${SANS},${EXTRA_SANS}"
    fi

    openssl req \
        -x509 \
        -newkey rsa:4096 \
        -days   3650 \
        -nodes \
        -keyout "${KEY_FILE}" \
        -out    "${CERT_FILE}" \
        -subj   "/C=DE/ST=Bavaria/L=Munich/O=NetApp Mock/CN=netapp-mock" \
        -addext "subjectAltName=${SANS}" \
        2>/dev/null

    echo "[entrypoint] Certificate written to ${CERT_FILE}"
    echo "[entrypoint] Fingerprint: $(openssl x509 -in "${CERT_FILE}" -fingerprint -sha256 -noout)"
fi

# ── Print connection info ─────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"
echo "  NetApp ONTAP Mock  –  HTTPS ready"
echo "  Base URL : https://$(hostname -i 2>/dev/null || echo '0.0.0.0')"
echo "  Cluster  : GET /api/cluster"
echo "  Auth     : any user / any password  (not validated)"
echo "════════════════════════════════════════════════════════"
echo ""

# ── Start gunicorn ────────────────────────────────────────────────────────────
exec gunicorn \
    --bind        "0.0.0.0:443" \
    --certfile    "${CERT_FILE}" \
    --keyfile     "${KEY_FILE}" \
    --workers     "${GUNICORN_WORKERS:-2}" \
    --threads     "${GUNICORN_THREADS:-4}" \
    --timeout     "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile  "-" \
    --error-logfile   "-" \
    --log-level   "${LOG_LEVEL:-info}" \
    --access-logformat '%(t)s "%(r)s" %(s)s %(b)s %(D)sµs' \
    app:app
