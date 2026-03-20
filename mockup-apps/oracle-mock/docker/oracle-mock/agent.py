#!/usr/bin/env python3
"""
Oracle mock — Checkmk agent (TCP 6556) with mk_oracle sections.

Simulates two Oracle 19c databases on the same host:
  SID: ORCL     (non-CDB primary, ARCHIVELOG, healthy)
  SID: ORCLPDB  (non-CDB standby, DATA tablespace near-full + failing job)

Section formats match Checkmk 2.4 / mk_oracle plugin output exactly.

Run inside Docker:  python agent.py [--port 6556] [--host 0.0.0.0]
"""

import argparse
import datetime
import socketserver
import time

# ── Constants ─────────────────────────────────────────────────────────────────
BLOCK_SIZE = 8192          # bytes per Oracle block
MB = 1024 * 1024
GB = 1024 * MB

def _blk(megabytes: int) -> int:
    """Convert MiB to Oracle blocks (8 KiB blocks)."""
    return megabytes * MB // BLOCK_SIZE


# ── Section builders ──────────────────────────────────────────────────────────

def _oracle_instance(hostname: str) -> str:
    """
    13-field non-CDB format (Oracle >= 12.1.0.2, with host_name):
      SID | VERSION | OPENMODE | LOGINS | ARCHIVER | UP_SECONDS |
      DBID | LOG_MODE | DATABASE_ROLE | FORCE_LOGGING | NAME |
      DB_CREATION_TIME | HOST_NAME

    Checkmk parser: oracle_instance_section.py — 13-field branch.
    """
    # Static uptime: ~25 days (reproducible across restarts)
    up = int(time.time()) - 1_700_000_000

    rows = [
        # Healthy primary — all checks green
        f"ORCL|19.3.0.0.0|OPEN|ALLOWED|STARTED|{up}|1481122484"
        f"|ARCHIVELOG|PRIMARY|NO|ORCL|20200115|{hostname}",
        # Secondary — treated as independent instance in mock
        f"ORCLPDB|19.3.0.0.0|OPEN|ALLOWED|STARTED|{up}|1481122485"
        f"|ARCHIVELOG|PRIMARY|NO|ORCLPDB|20200201|{hostname}",
    ]
    return "<<<oracle_instance:sep(124)>>>\n" + "\n".join(rows) + "\n"


def _oracle_tablespaces() -> str:
    """
    14-field format (standard Checkmk 2.4 format):
      SID | DATAFILE_PATH | TS_NAME | DATAFILE_STATUS | AUTOEXTENSIBLE |
      SIZE_BLOCKS | MAX_SIZE_BLOCKS | USED_BLOCKS | INCREMENT_SIZE_BLOCKS |
      FILE_ONLINE_STATUS | BLOCK_SIZE_BYTES | TS_STATUS | FREE_SPACE_BLOCKS |
      TS_TYPE

    All block counts use BLOCK_SIZE = 8192 bytes.
    FILE_ONLINE_STATUS: ONLINE for permanent/undo, TEMP for temporary.
    TS_STATUS: ONLINE, OFFLINE, READONLY.
    TS_TYPE: PERMANENT, UNDO, TEMPORARY.

    Checkmk check: oracle_tablespaces.py.
    """
    def row(sid, datafile, ts_name, ts_type, autoext,
            size_mb, max_mb, used_mb, inc_mb, file_status, ts_status):
        sz  = _blk(size_mb)
        mx  = _blk(max_mb)
        us  = _blk(used_mb)
        inc = _blk(inc_mb)
        fr  = sz - us
        return (f"{sid}|{datafile}|{ts_name}|AVAILABLE|"
                f"{'YES' if autoext else 'NO'}|{sz}|{mx}|{us}|{inc}|"
                f"{file_status}|{BLOCK_SIZE}|{ts_status}|{fr}|{ts_type}")

    rows = [
        # ORCL ── healthy CDB
        row("ORCL", "/u01/oradata/orcl/system01.dbf",  "SYSTEM",   "PERMANENT", True,  820,  32768,  616,  128, "ONLINE", "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/sysaux01.dbf",  "SYSAUX",   "PERMANENT", True,  540,  16384,  278,  128, "ONLINE", "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/undotbs01.dbf", "UNDOTBS1", "UNDO",      True,  512,   8192,  314,   64, "ONLINE", "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/temp01.dbf",    "TEMP",     "TEMPORARY", True, 2048,  32768,  128,  128,  "TEMP",  "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/users01.dbf",   "USERS",    "PERMANENT", True,  128,  32768,   64,  128, "ONLINE", "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/data01.dbf",    "DATA",     "PERMANENT", True, 3200,  65536, 2560,  256, "ONLINE", "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/idx01.dbf",     "IDX",      "PERMANENT", True, 1024,  32768,  512,  128, "ONLINE", "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/audit01.dbf",   "AUDIT_TS", "PERMANENT", True,   64,   8192,    8,   64, "ONLINE", "ONLINE"),
        # ORCLPDB ── DATA tablespace intentionally near-full → WARN in Checkmk
        row("ORCLPDB", "/u01/oradata/orclpdb/system01.dbf",  "SYSTEM",   "PERMANENT", True,  410,   8192,  348,  128, "ONLINE", "ONLINE"),
        row("ORCLPDB", "/u01/oradata/orclpdb/sysaux01.dbf",  "SYSAUX",   "PERMANENT", True,  280,   8192,  196,  128, "ONLINE", "ONLINE"),
        row("ORCLPDB", "/u01/oradata/orclpdb/data01.dbf",    "DATA",     "PERMANENT", True, 7936,   8192, 7526,  128, "ONLINE", "ONLINE"),  # ~94 %
        row("ORCLPDB", "/u01/oradata/orclpdb/temp01.dbf",    "TEMP",     "TEMPORARY", True,  512,   4096,   64,   64,  "TEMP",  "ONLINE"),
        row("ORCLPDB", "/u01/oradata/orclpdb/users01.dbf",   "USERS",    "PERMANENT", True,   64,   2048,   32,   64, "ONLINE", "ONLINE"),
    ]
    return "<<<oracle_tablespaces:sep(124)>>>\n" + "\n".join(rows) + "\n"


def _oracle_sessions() -> str:
    """
    4-field format (Oracle >= 12.1):
      SID | CURRENT_SESSIONS | SESSIONS_LIMIT | MAX_UTILIZATION

    Checkmk legacy check: oracle_sessions — uses line[1] (current) and line[2] (limit).
    """
    rows = [
        "ORCL|47|300|65",
        "ORCLPDB|12|150|25",
    ]
    return "<<<oracle_sessions:sep(124)>>>\n" + "\n".join(rows) + "\n"


def _oracle_logswitches() -> str:
    """
    2-field format:
      SID | LOGSWITCHES_LAST_60_MINUTES

    Query counts v$loghist entries for the last hour per instance.
    Checkmk legacy check: oracle_logswitches.
    """
    rows = [
        "ORCL|6",
        "ORCLPDB|2",
    ]
    return "<<<oracle_logswitches:sep(124)>>>\n" + "\n".join(rows) + "\n"


def _oracle_undostat() -> str:
    """
    6-field format:
      SID | ACTIVEBLKS | MAXCONCURRENCY | TUNED_UNDORETENTION |
      MAXQUERYLEN | NOSPACEERRCNT

    TUNED_UNDORETENTION: seconds (-1 for Oracle <= 9.2).
    Checkmk legacy check: oracle_undostat.
    """
    rows = [
        "ORCL|160|8|900|300|0",
        "ORCLPDB|64|4|900|120|0",
    ]
    return "<<<oracle_undostat:sep(124)>>>\n" + "\n".join(rows) + "\n"


def _oracle_recovery_area() -> str:
    """
    6-field format:
      SID | USED_PCT | SPACE_LIMIT_MB | SPACE_USED_MB |
      SPACE_RECLAIMABLE_MB | FLASHBACK_ON

    All space values in MiB (integer).
    Checkmk legacy check: oracle_recovery_area — uses line[2:5].
    Inventory plugin: stores line[-1] (FLASHBACK_ON).
    """
    rows = [
        f"ORCL|39|20480|8192|2048|YES",
        f"ORCLPDB|28|10240|3072|512|NO",
    ]
    return "<<<oracle_recovery_area:sep(124)>>>\n" + "\n".join(rows) + "\n"


def _oracle_processes() -> str:
    """
    3-field format:
      SID | CURRENT_PROCESSES | PROCESSES_LIMIT

    Sourced from v$resource_limit where RESOURCE_NAME = 'processes'.
    Checkmk check: oracle_processes.py.
    """
    rows = [
        "ORCL|85|300",
        "ORCLPDB|32|150",
    ]
    return "<<<oracle_processes:sep(124)>>>\n" + "\n".join(rows) + "\n"


def _oracle_rman() -> str:
    """
    8-field current format:
      SID | STATUS | START_TIME | END_TIME | BACKUPTYPE |
      INCREMENTAL_LEVEL | BACKUPAGE_MINUTES | INCREMENTAL_CHANGE_SCN

    Timestamps: YYYY-mm-dd_HH:MM:SS  (underscore between date and time).
    START_TIME / END_TIME are empty for ARCHIVELOG and CONTROLFILE rows.
    BACKUPAGE_MINUTES: integer minutes since last backup.
    Checkmk check: oracle_rman.py — service items: SID.BACKUPTYPE_LEVEL.
    """
    now  = datetime.datetime.now()
    fmt  = "%Y-%m-%d_%H:%M:%S"

    def ts(delta_hours: float = 0) -> str:
        return (now - datetime.timedelta(hours=delta_hours)).strftime(fmt)

    def age(delta_hours: float) -> int:
        return int(delta_hours * 60)

    rows = [
        # ORCL — full backup two days ago, incremental last night, archivelog recent
        f"ORCL|COMPLETED|{ts(48)}|{ts(47)}|DB_FULL||{age(48)}|8485000",
        f"ORCL|COMPLETED|{ts(20)}|{ts(19.5)}|DB_INCR|1|{age(20)}|8490000",
        f"ORCL|COMPLETED||{ts(1)}|ARCHIVELOG||{age(1)}|",
        f"ORCL|COMPLETED||{ts(12)}|CONTROLFILE||{age(12)}|0",
        # ORCLPDB — incremental only
        f"ORCLPDB|COMPLETED|{ts(20)}|{ts(19.7)}|DB_INCR|1|{age(20)}|7200000",
        f"ORCLPDB|COMPLETED||{ts(1)}|ARCHIVELOG||{age(1)}|",
    ]
    return "<<<oracle_rman:sep(124)>>>\n" + "\n".join(rows) + "\n"


def _oracle_jobs() -> str:
    """
    10-field format (non-CDB):
      SID | JOB_OWNER | JOB_NAME | JOB_STATE | LAST_RUN_DURATION_SEC |
      RUN_COUNT | ENABLED | NEXT_RUN_DATE | SCHEDULE_NAME | LAST_RUN_STATUS

    NEXT_RUN_DATE: Oracle date string (e.g. '02-AUG-15 12.00.00.500000 AM EUROPE/VIENNA').
    JOB_STATE: SCHEDULED | RUNNING | COMPLETED | BROKEN | DISABLED.
    LAST_RUN_STATUS: SUCCEEDED | FAILED | STOPPED | (empty).
    Checkmk legacy check: oracle_jobs — item: SID.OWNER.JOB_NAME.
    """
    now = datetime.datetime.now()

    def next_run(delta_hours: float) -> str:
        dt = now + datetime.timedelta(hours=delta_hours)
        return dt.strftime("%d-%b-%y %I.%M.%S.000000 %p EUROPE/BERLIN").upper()

    rows = [
        f"ORCL|SYS|GATHER_STATS_JOB|SCHEDULED|45|877|TRUE|{next_run(18)}|-|SUCCEEDED",
        f"ORCL|SYS|AUTO_OPTIMIZER_STATS_COLLECTION|SCHEDULED|30|1204|TRUE|{next_run(22)}|-|SUCCEEDED",
        f"ORCL|SYS|PURGE_LOG|SCHEDULED|5|365|TRUE|{next_run(0)}|-|SUCCEEDED",
        f"ORCL|SYS|ARCHIVE_LOG_BACKUP|SCHEDULED|12|730|TRUE|{next_run(5)}|-|SUCCEEDED",
        f"ORCLPDB|SYS|GATHER_STATS_JOB|SCHEDULED|20|440|TRUE|{next_run(16)}|-|SUCCEEDED",
        # Failing job — 3 consecutive failures → CRIT in Checkmk
        f"ORCLPDB|APP_OWNER|ETL_LOAD_JOB|BROKEN|0|127|TRUE|{next_run(9)}|ETL_SCHEDULE|FAILED",
    ]
    return "<<<oracle_jobs:sep(124)>>>\n" + "\n".join(rows) + "\n"


def _check_mk_header(hostname: str) -> str:
    """Standard Checkmk 2.4 agent header."""
    return (
        "<<<check_mk>>>\n"
        "Version: 2.4.0p22\n"
        "AgentOS: linux\n"
        f"Hostname: {hostname}\n"
        "AgentDirectory: /etc/check_mk\n"
        "DataDirectory: /var/lib/check_mk_agent\n"
        "SpoolDirectory: /var/lib/check_mk_agent/spool\n"
        "PluginsDirectory: /usr/lib/check_mk_agent/plugins\n"
        "LocalDirectory: /usr/lib/check_mk_agent/local\n"
        "OSType: linux\n"
        "OSPlatform: ubuntu\n"
        "OSName: Ubuntu\n"
        "OSVersion: 22.04\n"
    )


def build_agent_output(hostname: str = "oracle-mock") -> bytes:
    sections = [
        _check_mk_header(hostname),
        _oracle_instance(hostname),
        _oracle_tablespaces(),
        _oracle_sessions(),
        _oracle_logswitches(),
        _oracle_undostat(),
        _oracle_recovery_area(),
        _oracle_processes(),
        _oracle_rman(),
        _oracle_jobs(),
    ]
    return "\n".join(sections).encode("utf-8")


# ── TCP server ────────────────────────────────────────────────────────────────

class AgentHandler(socketserver.BaseRequestHandler):
    """Sends the agent output to each connecting client, then closes."""

    hostname: str = "oracle-mock"

    def handle(self):
        client = f"{self.client_address[0]}:{self.client_address[1]}"
        try:
            data = build_agent_output(self.hostname)
            self.request.sendall(data)
            print(f"[OK]   {client}  sent {len(data)} bytes", flush=True)
        except Exception as exc:
            print(f"[ERR]  {client}  {exc}", flush=True)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Oracle Checkmk agent mock")
    parser.add_argument("--host",     default="0.0.0.0", help="Bind address")
    parser.add_argument("--port",     type=int, default=6556, help="TCP port")
    parser.add_argument("--hostname", default="oracle-mock",
                        help="Hostname reported in <<<check_mk>>> header")
    args = parser.parse_args()

    AgentHandler.hostname = args.hostname

    server = ThreadedTCPServer((args.host, args.port), AgentHandler)
    print(f"Oracle mock agent listening on {args.host}:{args.port}  "
          f"(hostname={args.hostname})", flush=True)
    print("SIDs: ORCL (primary), ORCLPDB (secondary, near-full DATA + broken job)",
          flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
