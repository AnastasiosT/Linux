# Meraki Dashboard API v1 — Mock Server

A self-hosted mock of the Cisco Meraki Dashboard REST API, built with Flask and
deployed via Vagrant + Docker. Designed for testing the
[thl-cmk Cisco Meraki special agent](https://thl-cmk.hopto.org/checkmk/cisco/meraki/cisco_meraki)
for Checkmk without requiring real Meraki hardware or a live API key.

**Multi-tenant:** a single container serves multiple independent organizations.
Each tenant is identified by its API key — no extra VMs or containers needed.

---

## Architecture

```
Checkmk server
  └── agent_cisco_meraki  (API key: key-customer-a)
        └── HTTPS → api.meraki.com (/etc/hosts → 192.168.126.10)
                        └── Vagrant VM  (mockup-meraki network)
                              └── Docker container (meraki-mock)
                                    └── Flask + Gunicorn (port 443, SSL)
                                          ├── key-customer-a → Customer-A org
                                          └── key-customer-b → Customer-B org
```

---

## Adding / editing customers

Edit `TENANTS` in [docker/meraki-mock/app.py](docker/meraki-mock/app.py):

```python
TENANTS = {
    "key-customer-a": build_tenant(
        org_id="111111", org_name="Customer-A",
        prefix="CUSA", wan1_ip="203.0.113.10", branch_wan1="198.51.100.20",
    ),
    "key-customer-b": build_tenant(
        org_id="222222", org_name="Customer-B",
        prefix="CUSB", wan1_ip="203.0.114.10", branch_wan1="198.51.101.20",
    ),
    # Add more customers here:
    # "key-customer-c": build_tenant(
    #     org_id="333333", org_name="Customer-C",
    #     prefix="CUSC", wan1_ip="203.0.115.10", branch_wan1="198.51.102.20",
    # ),
}
```

| Parameter | Description |
|-----------|-------------|
| `org_id` | Unique org ID string (shown in Checkmk) |
| `org_name` | Organization name (used as prefix for network/device names) |
| `prefix` | Serial number prefix — e.g. `CUSA` → serials `CUSA-MX01`, `CUSA-SW01` |
| `wan1_ip` | WAN IP of the HQ MX appliance |
| `branch_wan1` | WAN IP of the Branch MX appliance |

After editing, redeploy:

```bash
vagrant provision --provision-with mock
```

---

## Mock data (per tenant)

Each tenant gets the same topology with tenant-specific names and IPs:

| Device | Serial | Model | Network | Status |
|--------|--------|-------|---------|--------|
| `{org}-HQ-MX` | `{PREFIX}-MX01` | MX68 | `{org}-HQ` | online |
| `{org}-HQ-SW` | `{PREFIX}-SW01` | MS220-8P | `{org}-HQ` | online |
| `{org}-HQ-AP` | `{PREFIX}-AP01` | MR46 | `{org}-HQ` | online |
| `{org}-HQ-Sensor` | `{PREFIX}-SN01` | MT10 | `{org}-HQ` | online |
| `{org}-Branch-MX` | `{PREFIX}-MX02` | MX65 | `{org}-Branch` | online |
| `{org}-Branch-SW` | `{PREFIX}-SW02` | MS120-8 | `{org}-Branch` | alerting |

VPN topology: HQ-MX as hub, Branch-MX as spoke.

### Intentional alert states
- Branch-SW: status `alerting`
- Branch-SW port 2: CRC align errors
- HQ-MX cellular uplink: not connected

---

## Project structure

```
meraki/
├── Vagrantfile                 # single VM, single container — edit app.py to add customers
└── docker/
    └── meraki-mock/
        ├── app.py              # Flask mock — TENANTS dict, build_tenant() factory
        ├── Dockerfile          # python:3.12-slim + gunicorn + self-signed SSL cert
        ├── docker-compose.yml  # single service, port 443
        └── requirements.txt    # flask, gunicorn
```

---

## Setup

### 1. Start the VM

```bash
cd /home/anastasios/vagrant/mockup-apps/meraki
vagrant up
```

The cert is automatically exported to `meraki-mock.crt` in the project folder.

### 2. Trust the cert on the Checkmk server

```bash
cp meraki-mock.crt /omd/sites/<site>/etc/ssl/ca-certificates/
omd reload <site>
```

### 3. Add /etc/hosts entry

```bash
echo "192.168.126.10  api.meraki.com" | sudo tee -a /etc/hosts
```

### 4. Verify

```bash
curl -s -H "X-Cisco-Meraki-API-Key: key-customer-a" \
  https://api.meraki.com/api/v1/organizations | python3 -m json.tool
```

---

## Checkmk configuration

Add one **special agent rule** per customer under
Setup > Other integrations > Cisco Meraki via REST API:

| Field | Customer A | Customer B |
|-------|-----------|-----------|
| API Key | `key-customer-a` | `key-customer-b` |
| Organisation ID | `111111` | `222222` |
| Host | `api.meraki.com` | `api.meraki.com` |

Both rules point to the same host/IP — the API key determines which org's data is returned.

---

## Running the agent manually

```bash
# Customer A
/omd/sites/<site>/local/lib/python3/cmk_addons/plugins/meraki/libexec/agent_cisco_meraki \
  meraki 'key-customer-a' --orgs 111111

# Customer B
/omd/sites/<site>/local/lib/python3/cmk_addons/plugins/meraki/libexec/agent_cisco_meraki \
  meraki 'key-customer-b' --orgs 222222

# Clear agent cache
rm -rf /omd/sites/<site>/tmp/check_mk/agents/agent_cisco_meraki/meraki/
```

---

## Updating mock data

```bash
scp docker/meraki-mock/app.py vagrant@192.168.126.10:/home/vagrant/docker/meraki-mock/app.py
ssh vagrant@192.168.126.10 "cd /home/vagrant/docker/meraki-mock && docker compose up --build -d"
rm -rf /omd/sites/<site>/tmp/check_mk/agents/agent_cisco_meraki/meraki/
```

---

## Viewing logs

```bash
ssh vagrant@192.168.126.10 "docker logs meraki-mock -f"
```

Unknown API key returns HTTP 401. Unimplemented endpoints log:
```
WARNING UNIMPLEMENTED: GET /api/v1/...
```
