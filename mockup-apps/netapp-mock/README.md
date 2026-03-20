# NetApp ONTAP REST API Mock — for CheckMK 2.4.x

## Architecture
```
┌─────────────────────────────────────────────────┐
│  CheckMK server                                 │
│  special agent: agent_netapp_ontap              │
│  (uses netapp-ontap-cmk Python library)         │
└─────────────────┬───────────────────────────────┘
                  │ HTTPS :443  (any credentials)
                  ▼
┌─────────────────────────────────────────────────┐
│  Docker container  (or Vagrant VM)              │
│  ┌─────────────────────────────────────────┐   │
│  │  gunicorn (SSL)  →  Flask  app.py       │   │
│  │  ONTAP REST API  /api/*                 │   │
│  └─────────────────────────────────────────┘   │
│  Self-signed cert auto-generated at startup     │
└─────────────────────────────────────────────────┘
```

## Mock Data Table

| Category       | Object                  | State     | Notes |
|----------------|-------------------------|-----------|-------|
| Nodes          | node-01                 | online    | ~35% CPU |
|                | node-02                 | online    | ~40% CPU |
| Aggregates     | aggr0_node01            | online    | root |
|                | aggr1_node01            | online    | ⚠ 87% full |
|                | aggr1_node02            | online    | 46% full |
| Volumes        | vol_data01              | online    | 5 TB |
|                | vol_legacy_offline      | **offline** | ← alert |
| Disks          | 1.0.01 – 1.0.12        | present   | SAS |
|                | 2.0.01 – 2.0.12        | present   | SAS |
|                | 1.0.13                  | **broken** | ← alert |
| LUNs           | oracle_lun01/02         | online    | |
|                | legacy_lun_offline      | **offline** | ← alert |
| Ports          | node-01 e0a–e0d         | up        | 25 GbE |
|                | node-02 e0d             | **down**  | ← alert |
| FC Ports       | node-01 0a–0c           | online    | |
|                | node-01 0d              | **error** | ← alert |
| Shelves/Fans   | shelf-1 fan-2           | **warning** | 550 RPM |
| Temp sensors   | shelf-3 sensor-3        | **warning** | 62 °C |
| SVMs           | svm_data01              | running   | |
|                | svm_backup              | **stopped** | ← alert |
| SnapMirror     | vol_data01 → vault      | healthy   | 8h lag |
|                | vol_data02 → mirror     | **unhealthy** | 2d+ lag |
| Qtree quotas   | qtree_finance           | soft-limit exceeded | |

## Setup (Docker)
```bash
# Clone / copy files, then:
docker compose up -d --build

# Verify:
curl -sk -u admin:password https://localhost/api/cluster | python3 -m json.tool

# Extract and trust the cert (for CheckMK):
docker compose exec netapp-mock \
  openssl x509 -in /app/certs/cert.pem -out netapp-mock.crt
# Copy netapp-mock.crt to CheckMK server's trusted CA bundle
```

## Setup (Vagrant)
```bash
vagrant up          # provisions Ubuntu 24.04, installs Docker, starts mock
vagrant ssh
curl -sk https://192.168.125.10/api/cluster
```

## Configure CheckMK

1. **Setup → Agents → Other integrations → NetApp via Ontap REST API**
2. Host: `192.168.125.10` (Vagrant) or container IP
3. Username: `admin`, Password: `password` (anything works)
4. Tick "No TLS certificate validation" **or** import `netapp-mock.crt`
5. Save & run service discovery

## View logs
```bash
docker compose logs -f          # live
docker compose logs --tail=100  # last 100 lines
```

## Update mock data

All seed data is in `app.py` — look for the `SEED` / `_vol()` / `_shelf()` / `_disk()` helper functions. Change values and redeploy:
```bash
docker compose up -d --build
```
