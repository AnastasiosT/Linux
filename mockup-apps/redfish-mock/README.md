# Redfish API v1 — Mock Server

A self-hosted mock of the Redfish REST API, built with Flask and deployed via
Vagrant + Docker. Designed for testing the Checkmk built-in Redfish special agent
(`agent_redfish`, included in Checkmk 2.4+) without requiring real server hardware
or a BMC/iLO.

Simulates an **HPE ProLiant DL360 Gen10 with iLO 5** — covering both the generic
Redfish code path and the HPE-specific SmartStorage/OEM path.

---

## Architecture

```
Checkmk server
  └── agent_redfish
        └── HTTPS → 192.168.123.114:443
                        └── Vagrant VM (bento/ubuntu-24.04)
                              └── Docker container (redfish-mock)
                                    └── Flask + Gunicorn (port 443, SSL)
```

The agent connects directly to the VM IP. The self-signed cert is generated at
build time and must be imported into Checkmk's trusted CA store.

---

## Mock data — HPE ProLiant DL360 Gen10

| Component | Details |
|---|---|
| System | ProLiant DL360 Gen10, Serial: MOCK0001337 |
| iLO | iLO 5, Firmware 3.06 |
| CPUs | 2x Intel Xeon Gold 6226R, 16 cores / 32 threads each |
| Memory | 4x 16GB DDR4 DIMMs = 64GB total |
| Storage (generic) | HPE Smart Array P408i-a, 2x 1.2TB SAS HDD, RAID1 volume |
| Storage (HPE SmartStorage) | ArrayController → LogicalDrive (RAID1) + 2x DiskDrive |
| Network | HPE 1Gb 4-port 331i Adapter, 2x EthernetInterface |
| Power supplies | 2x 800W PSU |
| Chassis | RackMount, 5 temperature sensors, 3 fans |
| Firmware inventory | iLO 5, BIOS, NIC, SmartArray |

### Randomised metrics (changes on every poll)
- CPU temperatures
- Fan RPM
- Power consumed (watts)
- PSU output watts
- Voltages

### Intentional states for testing
- All components healthy (OK) by default
- `health()` helper returns `Warning` ~25% of the time — useful for alert testing

---

## Checkmk sections produced

| Section | Source endpoint |
|---|---|
| `redfish_system` | GET /redfish/v1/Systems/1 |
| `redfish_manager` | GET /redfish/v1/Managers/1 |
| `redfish_processors` | GET /redfish/v1/Systems/1/Processors/{id} |
| `redfish_memory` | GET /redfish/v1/Systems/1/Memory/{id} |
| `redfish_ethernetinterfaces` | GET /redfish/v1/Systems/1/EthernetInterfaces/{id} |
| `redfish_networkinterfaces` | GET /redfish/v1/Systems/1/NetworkInterfaces/{id} |
| `redfish_storage` | GET /redfish/v1/Systems/1/Storage/1 |
| `redfish_drives` | GET /redfish/v1/Systems/1/Storage/1/Drives/{id} |
| `redfish_volumes` | GET /redfish/v1/Systems/1/Storage/1/Volumes/1 |
| `redfish_smartstorage` | GET /redfish/v1/Systems/1/SmartStorage |
| `redfish_arraycontrollers` | GET /redfish/v1/Systems/1/SmartStorage/ArrayControllers/0 |
| `redfish_logicaldrives` | GET /redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/LogicalDrives/1 |
| `redfish_physicaldrives` | GET /redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/DiskDrives/{id} |
| `redfish_power` | GET /redfish/v1/Chassis/1/Power |
| `redfish_thermal` | GET /redfish/v1/Chassis/1/Thermal |
| `redfish_networkadapters` | GET /redfish/v1/Chassis/1/NetworkAdapters/1 |
| `redfish_firmwareinventory` | GET /redfish/v1/UpdateService/FirmwareInventory?$expand=. |

---

## Project structure

```
redfish-mock/
├── Vagrantfile
└── docker/
    └── redfish-mock/
        ├── app.py              # Flask mock — all endpoints and seed data
        ├── Dockerfile          # python:3.12-slim + gunicorn + self-signed SSL cert
        ├── docker-compose.yml  # single service, port 443
        └── requirements.txt    # flask, gunicorn
```

---

## Setup

### 1. Start the VM

```bash
cd /home/anastasios/vagrant/kvm/redfish-mock
vagrant up
```

At the end of provisioning the cert will be printed automatically:
```
>>> SSL cert for Checkmk import:
-----
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
-----
```

Copy everything between and including the `-----BEGIN` and `-----END` lines.

### 2. Import the cert into Checkmk

**Setup → Global settings → Trusted certificate authorities for SSL**

Paste the cert and save. This allows the agent (which uses the Checkmk Python
environment) to trust the mock's self-signed certificate.

### 3. Verify connectivity

```bash
/omd/sites/<site>/bin/python3 -c \
  "import requests; print(requests.get('https://192.168.123.114/redfish/v1').text[:100])"
```

Should return the root JSON starting with `{"@odata.id": "/redfish/v1"...`.

---

## Checkmk WATO configuration

In **Setup → Other integrations → Redfish compatible management boards**:

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `dummy` (any string) |
| Protocol | `https` |
| Port | `443` |

The host IP should be `192.168.123.114`.

---

## Running the agent manually

```bash
/omd/sites/<site>/lib/python3/cmk/plugins/redfish/libexec/agent_redfish \
  --user admin \
  --password dummy \
  --proto https \
  --port 443 \
  192.168.123.114
```

With debug output:

```bash
/omd/sites/<site>/lib/python3/cmk/plugins/redfish/libexec/agent_redfish \
  --user admin \
  --password dummy \
  --proto https \
  --port 443 \
  --debug \
  192.168.123.114 2>&1 | head -50
```

---

## Updating mock data

Edit `docker/redfish-mock/app.py` locally then deploy:

```bash
scp docker/redfish-mock/app.py vagrant@192.168.123.114:/home/vagrant/docker/redfish-mock/app.py
ssh vagrant@192.168.123.114 "cd /home/vagrant/docker/redfish-mock && docker compose up --build -d"
```

Note: rebuilding regenerates the SSL cert. Re-import it into Checkmk after any rebuild.

---

## Viewing mock logs

```bash
ssh vagrant@192.168.123.114 "docker logs redfish-mock -f"
```

Any unimplemented endpoint appears as:
```
WARNING UNIMPLEMENTED: GET /redfish/...
```

---

## Stopping / destroying

```bash
# Stop VM (preserves disk)
vagrant halt

# Destroy VM completely
vagrant destroy
```

---

## Notes

- The HPE OEM block in `/redfish/v1` (`"Oem": {"Hpe": {...}}`) is what triggers
  the HPE-specific code path in the agent, including SmartStorage traversal and
  the ResourceDirectory firmware path.
- The `?$expand=.` query parameter on the FirmwareInventory endpoint is handled
  explicitly — without it the HW/SW inventory section would show empty.
- The self-signed cert SAN includes `IP:192.168.123.114` so the agent can verify
  it against the IP address directly without a DNS entry.
