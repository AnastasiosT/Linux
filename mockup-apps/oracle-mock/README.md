# Oracle mk_oracle — Checkmk Agent Mock

A self-hosted mock of the Checkmk agent (`mk_oracle` plugin) output, deployed
via Vagrant + Docker. Designed for testing the **Checkmk CEE Oracle integration**
without a real Oracle instance.

The mock is a plain TCP server on port **6556** that returns Checkmk agent
sections exactly as the `mk_oracle` agent plugin would produce them.

---

## Simulated databases

| SID | Role | Mode | Notes |
|-----|------|------|-------|
| ORCL | PRIMARY | OPEN / ARCHIVELOG | Healthy CDB, all services OK |
| ORCLPDB | PRIMARY | READ WRITE | PDB inside ORCL — tablespace DATA near capacity (WARN) |

---

## Sections produced

| Section | Description |
|---------|-------------|
| `<<<check_mk>>>` | Standard agent header |
| `<<<oracle_instance:sep(124)>>>` | DB open-mode, version, archiver, role |
| `<<<oracle_tablespaces:sep(124)>>>` | Tablespace usage (bytes, autoextend) |
| `<<<oracle_sessions:sep(124)>>>` | Active / max sessions |
| `<<<oracle_logswitches:sep(124)>>>` | Log switch counts per hour (24 h) |
| `<<<oracle_undostat:sep(124)>>>` | Undo space stats |
| `<<<oracle_recovery_area:sep(124)>>>` | Fast Recovery Area (FRA) usage |
| `<<<oracle_processes:sep(124)>>>` | Current / max background processes |
| `<<<oracle_rman:sep(124)>>>` | RMAN backup history |
| `<<<oracle_jobs:sep(124)>>>` | Scheduled job status |

### Intentional alerts

- `ORCLPDB.DATA` tablespace: ~93 % used → **WARN** threshold in Checkmk
- `ORCLPDB.ETL_LOAD_JOB`: job status `FAILED`, 3 consecutive failures → **CRIT**

---

## Setup

### 1. Start the VM

```bash
cd /home/anastasios/vagrant/mockup-apps/oracle-mock
vagrant up
```

### 2. Configure Checkmk

#### a. Disable agent TLS for this host (or globally for test)

```
Setup > Global Settings > Monitoring Core > Agent TLS > No encryption
```

Or per-host rule:
```
Setup > Agents > Access to Agents > Checkmk Agent > Encryption
  → No encryption (for host 192.168.126.10)
```

#### b. Add host

```
Setup > Hosts > Add host
  Hostname : oracle-mock
  IPv4     : 192.168.126.10
  Agent    : Checkmk agent
```

#### c. Apply mk_oracle rule

```
Setup > Agents > Agent rules > Oracle databases (Linux, Solaris, AIX, Windows)
  → Deploy mk_oracle plugin to: oracle-mock
```

#### d. Run service discovery

```
oracle-mock > Service Discovery → activate all discovered services
```

### 3. Verify connectivity

```bash
# Raw agent output
nc 192.168.126.10 6556 | head -40

# Or with socat
socat - TCP:192.168.126.10:6556 | head -40
```

Expected output starts with:
```
<<<check_mk>>>
Version: 2.3.0p1
AgentOS: linux
Hostname: oracle-mock
...
<<<oracle_instance:sep(124)>>>
ORCL|19.3.0.0.0|OPEN|ALLOWED|STARTED|...
```

---

## Multiple instances

Set `NUM_MOCKS` in the Vagrantfile:
```ruby
NUM_MOCKS = 2  # → 192.168.126.10, 192.168.126.11
```
Each instance runs a fully independent agent with its own hostname.

---

## Updating mock data

```bash
scp docker/oracle-mock/agent.py vagrant@192.168.126.10:/home/vagrant/docker/oracle-mock/agent.py
ssh vagrant@192.168.126.10 "cd /home/vagrant/docker/oracle-mock && docker compose up --build -d"
```

## Viewing logs

```bash
ssh vagrant@192.168.126.10 "docker logs oracle-mock-1 -f"
```

Each connection logs:
```
[OK]   192.168.x.x:PORT  sent 2048 bytes
```
