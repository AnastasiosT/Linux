# ntopng REST API v2 — Mock Server

A self-hosted mock of the ntopng REST API, built with Flask and deployed via
Vagrant + Docker. Designed for testing the **Checkmk CEE ntopng integration**
without a real ntopng instance.

---

## Auth flow (how Checkmk connects)

```
1. GET  /lua/rest/version.lua                   Basic Auth → API version
2. POST /lua/rest/v2/create/ntopng/session.lua  Basic Auth → session cookie
3. POST /lua/rest/v2/get/...                    Cookie: session=<token> → data
```

No TLS — uses plain HTTP on port 3000.

---

## Mock data

### Interfaces
| ifid | name | Speed |
|------|------|-------|
| 1 | eth0 | 1 Gbps |
| 2 | eth1 | 100 Mbps |

### Hosts
| IP | Name | Local |
|----|------|-------|
| 192.168.1.10 | web-server | yes |
| 192.168.1.20 | db-server | yes (1 alert) |
| 192.168.1.30 | workstation-01 | yes |
| 192.168.1.40 | workstation-02 | yes |
| 8.8.8.8 | dns.google | no |

### Active alerts
- `db-server` (192.168.1.20): `host_score` — severity warning
- Flow `workstation-01 → dns.google`: `potentially_dangerous_protocol` — severity notice

---

## Endpoints implemented

| Endpoint | Description |
|----------|-------------|
| `GET /lua/rest/version.lua` | API version (Basic Auth) |
| `POST /lua/rest/v2/create/ntopng/session.lua` | Session cookie (Basic Auth) |
| `POST /lua/rest/v2/get/ntopng/interfaces.lua` | List all interfaces |
| `POST /lua/rest/v2/get/interface/data.lua` | Interface stats (`?ifid=`) |
| `POST /lua/rest/v2/get/host/data.lua` | Host data (`?ifid=&host=IP@vlan`) |
| `POST /lua/rest/v2/get/host/interfaces.lua` | Host interfaces (`?host=`) |
| `POST /lua/rest/v2/get/host/l7/stats.lua` | Host L7 protocol stats |
| `POST /lua/rest/v2/get/host/custom_data.lua` | Host list (`?ifid=&field_alias=ip,vlan`) |
| `POST /lua/rest/v2/get/flow/active.lua` | Active flows |
| `POST /lua/rest/v2/get/db/flows.lua` | Historical flows (DB) |
| `POST /lua/rest/v2/get/flow/l4/counters.lua` | L4 protocol counters |
| `POST /lua/rest/v2/get/flow/l7/counters.lua` | L7 protocol counters |
| `POST /lua/rest/v2/get/alert/severity/consts.lua` | Alert severity constants |
| `POST /lua/rest/v2/get/alert/type/consts.lua` | Alert type constants |
| `POST /lua/rest/v2/get/alert/<severity\|type>/counters.lua` | Alert counters |
| `POST /lua/rest/v2/get/<entity>/alert/list.lua` | Alert list |
| `POST /lua/rest/v2/get/timeseries/ts.lua` | Timeseries data |
| `POST /lua/rest/v2/get/l4/protocol/consts.lua` | L4 protocol constants |
| `POST /lua/rest/v2/get/l7/<type>/consts.lua` | L7 protocol constants |
| `POST /lua/pro/rest/v2/get/interface/top/<local\|remote>/talkers.lua` | Top talkers (Pro) |

---

## Setup

### 1. Start the VM

```bash
cd /home/anastasios/vagrant/mockup-apps/ntop-mock
vagrant up
```

### 2. Configure Checkmk (Global Settings > ntopng)

| Field | Value |
|-------|-------|
| Activate | yes |
| Protocol | http |
| Hostname / IP | 192.168.128.10 |
| Port | 3000 |
| Admin username | admin |
| Admin password | admin |
| No certificate check | — (not needed for HTTP) |

### 3. Verify

```bash
# Version check
curl -u admin:admin http://192.168.128.10:3000/lua/rest/version.lua | python3 -m json.tool

# Get session cookie
curl -s -u admin:admin -X POST \
  http://192.168.128.10:3000/lua/rest/v2/create/ntopng/session.lua | python3 -m json.tool

# Get interfaces (with cookie)
SESSION=$(curl -s -u admin:admin -X POST \
  http://192.168.128.10:3000/lua/rest/v2/create/ntopng/session.lua | python3 -c \
  "import sys,json; print(json.load(sys.stdin)['rsp']['session'])")
curl -s -X POST --cookie "session=$SESSION" \
  http://192.168.128.10:3000/lua/rest/v2/get/ntopng/interfaces.lua | python3 -m json.tool
```

---

## Multiple instances

Set `NUM_MOCKS` in the Vagrantfile:
```ruby
NUM_MOCKS = 2  # → 192.168.128.10, 192.168.128.11
```
Each instance is a fully independent ntopng server.

---

## Updating mock data

```bash
scp docker/ntop-mock/app.py vagrant@192.168.128.10:/home/vagrant/docker/ntop-mock/app.py
ssh vagrant@192.168.128.10 "cd /home/vagrant/docker/ntop-mock && docker compose up --build -d"
```

## Viewing logs

```bash
ssh vagrant@192.168.128.10 "docker logs ntop-mock-1 -f"
```

Unknown endpoints log:
```
WARNING UNIMPLEMENTED: POST /lua/rest/v2/get/...
```
