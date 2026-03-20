# Oracle mk_oracle — Checkmk Agent Mock

A self-hosted mock of the Checkmk agent (`mk_oracle` plugin) output, deployed
via Vagrant + Docker. Designed for testing the **Checkmk 2.4 CEE Oracle integration**
without a real Oracle instance.

The mock is a plain TCP server on port **6556** that returns Checkmk agent
sections exactly as the `mk_oracle` agent plugin would produce them.
All numeric values (tablespace usage, session counts, performance counters, etc.)
are **randomised on every request** within realistic bounds, so Checkmk sees
naturally varying data. Intentional alert conditions are always preserved.

---

## Simulated databases

| SID | Role | Mode | Notes |
|-----|------|------|-------|
| `+ASM` | ASM instance | STARTED | 3 diskgroups: DATA, REDO, FRA |
| `ORCL` | CDB primary | OPEN / ARCHIVELOG | 3 PDBs: ORCLPDB1, ORCLPDB2, ORCLPDB3 |
| `STDBY` | Physical standby | MOUNTED | DataGuard replica of ORCL |
| `DEVDB` | Standalone dev | OPEN / NOARCHIVELOG | Non-CDB dev database |

---

## Sections produced

| Section | Description |
|---------|-------------|
| `<<<check_mk>>>` | Standard agent header (version 2.4.0p22) |
| `<<<oracle_instance:sep(124)>>>` | DB open-mode, version, archiver, role — 6-field (ASM), 13-field (non-CDB), 22-field (CDB+PDB) |
| `<<<oracle_tablespaces:sep(124)>>>` | Tablespace usage per SID and PDB |
| `<<<oracle_sessions:sep(124)>>>` | Active / max sessions |
| `<<<oracle_logswitches:sep(124)>>>` | Log switch counts last 60 minutes |
| `<<<oracle_undostat:sep(124)>>>` | Undo space stats |
| `<<<oracle_recovery_area:sep(124)>>>` | Fast Recovery Area usage |
| `<<<oracle_processes:sep(124)>>>` | Current / max background processes |
| `<<<oracle_rman:sep(124)>>>` | RMAN backup history (DB_FULL, DB_INCR, ARCHIVELOG, CONTROLFILE) |
| `<<<oracle_jobs:sep(124)>>>` | Scheduled job status |
| `<<<oracle_dataguard_stats:sep(124)>>>` | DataGuard apply lag |
| `<<<oracle_locks:sep(124)>>>` | Active TX locks with hold duration |
| `<<<oracle_longactivesessions:sep(124)>>>` | Sessions active beyond threshold |
| `<<<oracle_performance:sep(124)>>>` | sys_time_model, buffer pool, librarycache, SGA, wait_class, I/O stats |
| `<<<oracle_asm_diskgroup:sep(124)>>>` | ASM diskgroup free/used space |
| `<<<oracle_recovery_status:sep(124)>>>` | Archive/apply status |
| `<<<oracle_crs_version:sep(124)>>>` | Grid Infrastructure version |
| `<<<oracle_crs_voting:sep(124)>>>` | Voting disk status |
| `<<<oracle_crs_res:sep(124)>>>` | CRS resource state |

---

## Intentional alerts

These conditions are always present regardless of randomisation:

| Alert | SID | Expected Checkmk state |
|-------|-----|------------------------|
| DATA tablespace 92–97 % used, autoextend OFF | `ORCL.ORCLPDB2` | WARN / CRIT |
| FRA diskgroup 80–92 % used | `+ASM` (FRA) | WARN |
| DataGuard apply lag 5400–9000 s | `STDBY` | WARN |
| TX lock held 1850–2400 s (threshold 1800 s) | `ORCL` | CRIT |
| `ETL_LOAD_JOB` status BROKEN | `ORCL.ORCLPDB3` | CRIT |
| No RMAN backup rows | `STDBY` | CRIT |
| TEMP tablespace OFFLINE | `DEVDB` | WARN |
| Long active session 3600–5400 s | `DEVDB` | WARN |

---

## Setup

### 1. Start the VM

```bash
cd /home/anastasios/vagrant/mockup-apps/oracle-mock
vagrant up
```

### 2. Configure Checkmk

#### a. Disable agent TLS for this host

```
Setup > Agents > Access to Agents > Checkmk Agent > Encryption
  → No encryption  (for host 192.168.126.10)
```

#### b. Add host

```
Setup > Hosts > Add host
  Hostname : oracle-mock
  IPv4     : 192.168.126.10
  Agent    : Checkmk agent
```

#### c. Run service discovery

```
oracle-mock > Service Discovery → activate all discovered services
```

### 3. Verify connectivity

```bash
nc 192.168.126.10 6556 | head -60
```

Expected output starts with:
```
<<<check_mk>>>
Version: 2.4.0p22
AgentOS: linux
Hostname: oracle-mock
...
<<<oracle_instance:sep(124)>>>
+ASM|19.3.0.0.0|STARTED|ALLOWED|STARTED|2154832
ORCL|19.3.0.0.0|OPEN|ALLOWED|STARTED|...
```

---

## Deploying code changes

```bash
cd /home/anastasios/vagrant/mockup-apps/oracle-mock

# Upload updated agent.py and rebuild
vagrant upload docker/oracle-mock/agent.py /home/vagrant/docker/oracle-mock/agent.py
vagrant ssh -c "cd /home/vagrant/docker/oracle-mock && docker compose up --build -d"
```

## Viewing logs

```bash
vagrant ssh -c "docker logs oracle-mock -f"
```

Each connection logs:
```
[OK]   192.168.x.x:PORT  sent 4096 bytes
```

---

## Data randomisation

All metric values vary on every Checkmk poll within realistic ranges.
The following are fixed (to keep alert conditions stable):

- `ORCLPDB2.DATA`: `used_blocks` always 92–97 % of `max_blocks`, `AUTOEXTEND=NO`
- `DEVDB.TEMP`: always `OFFLINE`
- `STDBY`: no RMAN rows emitted
- ORCL lock duration: always 1850–2400 s
- DEVDB long session: always 3600–5400 s
- STDBY apply lag: always 5400–9000 s
- FRA free space: always 8–18 % of total

Everything else (session counts, tablespace used blocks, process counts, undo stats,
performance counters, RMAN ages, log switch counts, ASM free space) is randomised
each request.
