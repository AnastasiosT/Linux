# mockup-apps — Development Notes

## Overview

Each mock simulates a real system's API/agent output for testing Checkmk integrations
without real hardware. All mocks follow the same pattern:

```
Vagrantfile → libvirt VM → Docker container → Flask/TCP server
```

| Mock | Protocol | Port | Purpose |
|------|----------|------|---------|
| meraki | HTTPS (Flask) | 443 | Cisco Meraki Dashboard REST API v1 |
| oracle-mock | TCP (raw) | 6556 | Checkmk agent with mk_oracle sections |
| ntop-mock | HTTP (Flask) | 3000 | ntopng REST API v2 |
| redfish-mock | HTTPS (Flask) | 443 | Redfish API v1 (HPE iLO) |

---

## SSL Certificate Management

### The problem
If the cert is generated inside the Dockerfile (`RUN openssl ...`), it regenerates
on every `docker compose build --no-cache`. The old trusted cert on the Checkmk host
becomes invalid and all API calls fail silently (agent uses stale cache instead).

### The solution (meraki)
- Cert is generated **once** during `vagrant up` provisioning, stored in `cert/`
- Vagrantfile checks `cert/cert.pem` before generating — if it exists, reuse it
- Dockerfile does `COPY cert.pem key.pem /app/` instead of `RUN openssl`
- `cert/key.pem` is gitignored; `cert/cert.pem` can be committed

### Symptom of cert mismatch
- Mock logs show only: `[SSL: TLSV1_ALERT_UNKNOWN_CA] tlsv1 alert unknown ca`
- Agent output still has sections (served from agent's own DataCache)
- Missing sections are ones whose cache has expired or never existed

### Trusting the cert on Checkmk
```bash
cp cert/cert.pem /omd/sites/<site>/etc/ssl/ca-certificates/meraki-mock.crt
omd reload <site>
```

---

## Checkmk Agent Cache Layers

The Meraki special agent has **two independent caches**:

1. **Checkmk data source cache** — bypassed with `cmk --no-cache -d <host>`
2. **Agent's own DataCache** (`/tmp/check_mk/agents/agent_cisco_meraki/`) — only
   bypassed if `--no-cache` is passed to the agent itself (via rule setting or
   `--no-cache` flag)

When all API calls fail SSL, the agent silently serves stale DataCache. Sections
that were never successfully cached simply don't appear.

To force a full refresh:
```bash
rm -rf /tmp/check_mk/agents/agent_cisco_meraki/
cmk --no-cache -d meraki
```

---

## Meraki Mock — Key Learnings

### Auth header
The Meraki Python SDK v2+ sends `Authorization: Bearer <key>`, NOT
`X-Cisco-Meraki-API-Key`. The mock must check both:
```python
api_key = request.headers.get("X-Cisco-Meraki-API-Key", "")
if not api_key:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        api_key = auth[7:]
```

### SDK URL paths
The SDK URL path is **not always** what the Meraki API docs show. Always verify
by running the agent with `--debug` and grepping for the actual GET URL:
```bash
agent_cisco_meraki meraki key-customer-a --orgs 111111 --no-cache --debug 2>&1 \
  | grep "GET https"
```

Known mismatch:
- Docs/intuition: `/api/v1/organizations/<id>/cellular/gateway/uplink/statuses`
- Actual SDK call: `/api/v1/organizations/<id>/cellularGateway/uplink/statuses`

### Pagination (`total_pages='all'`)
Some SDK calls use `total_pages='all'` — the SDK loops using `Link: <next>` headers.
Since the mock returns no `Link` header, the SDK stops after page 1. This is fine;
no special handling needed in the mock.

### Response format requirements

| Endpoint | Format | Notes |
|----------|--------|-------|
| `apiRequests/overview/responseCodes/byInterval` | `[{"startTs":..., "counts":[{"code":200,"count":N}]}]` | Must be a list directly, not `{"items":[...]}`. Field is `code` not `statusCode` |
| `switch/ports/statuses/bySwitch` | `{"items": [...]}` | Wrapped in `items` key |
| wireless ethernet `linkNegotiation` | `{"duplex": "full", "speed": 1000}` | Must be dict with integer speed in Mbps, not string like `"1 Gbps"` |
| `cellular/gateway/uplink/statuses` | list of gateway objects | Route as `cellularGateway/uplink/statuses` |

### Empty dict `{}` is falsy
`MerakiGetOrganization.get_live_data()` returns `{}` on API error.
In Python `if organisation := {}` evaluates to False — the org section is silently
skipped but execution continues. Missing org section = API call failed.

### Org ID vs org name
The `--orgs` flag takes org **IDs** (e.g. `111111`), not names.

### Discovering which section is missing
```bash
# Check what sections the agent produces
cmk --no-cache -d meraki 2>/dev/null | grep "^<<<"

# Run agent directly for one org with debug
agent_cisco_meraki meraki key-customer-a --orgs 111111 --no-cache --debug 2>&1 \
  | grep -E "GET|ERROR|404"
```

### Debugging parse failures
Check crash reports:
```bash
ls ~/var/check_mk/crashes/check/ | grep meraki
cat ~/var/check_mk/crashes/check/<crash>/crash.info | python3 -m json.tool \
  | grep -A5 "exc_type\|exc_value\|section_content"
```

---

## Deploying Code Changes

### Quick deploy (app.py only)
```bash
cd /home/anastasios/vagrant/mockup-apps/meraki
vagrant upload docker/meraki-mock/app.py /home/vagrant/docker/meraki-mock/app.py
vagrant ssh -c "cd /home/vagrant/docker/meraki-mock && docker compose up --build -d"
```

### Full rebuild (Dockerfile changes, cert changes)
```bash
vagrant ssh -c "cd /home/vagrant/docker/meraki-mock && docker compose build --no-cache && docker compose up -d"
```

**Warning:** `docker compose up --build` uses Docker layer cache and may NOT pick
up changes to `app.py` if only that file changed. Use `--no-cache` or `vagrant upload`
the file first, then `up --build`.

### After any mock change — clear Checkmk caches
```bash
rm -rf /tmp/check_mk/agents/agent_cisco_meraki/
cmk --no-cache -IIv meraki   # full rediscovery
```

---

## Adding a New Device Type to Meraki Mock

1. Add serial variable: `mg1 = f"{prefix}-MG01"`
2. Add to `devices` list with correct `productType`
3. Add to `device_statuses` list
4. Add data structure (e.g. `cellular_uplink_statuses`)
5. Add to `return` dict of `build_tenant()`
6. Update endpoint to return `t["cellular_uplink_statuses"]` instead of `[]`
7. Update `net` productTypes list if needed

Device types: `appliance`, `switch`, `wireless`, `sensor`, `cellularGateway`

---

## Redfish Mock — Notes

- The cert SAN must include `IP:192.168.123.114` for the agent to verify by IP
- The HPE OEM block (`"Oem": {"Hpe": {...}}`) triggers the HPE-specific code path
- `?$expand=.` on FirmwareInventory must be handled explicitly
- Cert regenerates on rebuild — re-import after any `docker compose build`

---

## Oracle Mock — Notes

- Pure TCP server on port 6556, no HTTP
- Section fields are pipe-separated (`sep(124)`)
- Field counts are exact — wrong count causes parse failure in Checkmk
- Agent TLS must be disabled for the oracle-mock host in Checkmk

---

## General Debugging Pattern

1. Run agent with `--debug` to see actual API calls and errors
2. Check mock logs: `docker logs <container> -f`
3. Check Checkmk crash reports in `~/var/check_mk/crashes/`
4. Compare actual section output: `cmk --no-cache -d <host> | grep "^<<<"`
5. Check piggyback files: `ls ~/tmp/check_mk/piggyback/`
