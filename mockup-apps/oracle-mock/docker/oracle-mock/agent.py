#!/usr/bin/env python3
"""
Oracle mock — Checkmk agent (TCP 6556) with mk_oracle sections.

Simulates a realistic Oracle 19c environment:
  +ASM      — ASM instance (diskgroups DATA, REDO, FRA)
  ORCL      — CDB primary (ARCHIVELOG) with PDBs: ORCLPDB1, ORCLPDB2, ORCLPDB3
  STDBY     — Physical standby (DataGuard)
  DEVDB     — Standalone dev database (non-CDB)

Intentional alerts:
  ORCLPDB2   DATA tablespace ~94 % used         → WARN/CRIT
  FRA        ASM diskgroup 85 % used             → WARN
  STDBY      apply lag 7200s                     → WARN
  ORCL       lock held 1950s                     → CRIT
  ORCLPDB3   ETL_LOAD_JOB BROKEN                → CRIT
  STDBY      no RMAN backup on record            → CRIT
  DEVDB      TEMP tablespace OFFLINE             → WARN
  DEVDB      long active session 3600s           → WARN

Section formats match Checkmk 2.4 / mk_oracle plugin output exactly.

Run inside Docker:  python agent.py [--port 6556] [--host 0.0.0.0]
"""

import argparse
import datetime
import socketserver
import time

# ── Constants ─────────────────────────────────────────────────────────────────
BLOCK_SIZE = 8192          # bytes per Oracle block (8 KiB)
MB = 1024 * 1024


def _blk(megabytes: int) -> int:
    """Convert MiB to Oracle blocks (8 KiB blocks)."""
    return megabytes * MB // BLOCK_SIZE


# ── Uptime helper ─────────────────────────────────────────────────────────────

def _up() -> int:
    """Static 25-day uptime (reproducible across restarts)."""
    return int(time.time()) - 1_700_000_000


def _up_short() -> int:
    """3-day uptime (for standby / dev instances)."""
    return int(time.time()) - 1_700_230_000


# ── Section: oracle_instance ──────────────────────────────────────────────────

def _oracle_instance(hostname: str) -> str:
    """
    Two formats emitted together:

    13-field non-CDB (STDBY, DEVDB):
      SID|VERSION|OPENMODE|LOGINS|ARCHIVER|UP_SECONDS|DBID|LOG_MODE|
      DATABASE_ROLE|FORCE_LOGGING|NAME|DB_CREATION_TIME|HOST_NAME

    22-field CDB+PDB (ORCL with its PDBs) — one row per PDB:
      SID|VERSION|OPENMODE|LOGINS|ARCHIVER|UP_SECONDS|_DBID|LOG_MODE|
      DATABASE_ROLE|FORCE_LOGGING|NAME|DB_CREATION_TIME|PLUGGABLE|CON_ID|
      PNAME|_PDBID|POPENMODE|PRESTRICTED|PTOTAL_SIZE|_PRERECOVERY_STATUS|
      PUPS|_PBLOCK_SIZE

    ASM instance uses 6-field format (no host / DB info):
      +ASM|VERSION|STARTED|ALLOWED|STARTED|UP_SECONDS
    """
    up  = _up()
    ups = _up_short()

    rows = [
        # +ASM — 6-field ASM instance row
        f"+ASM|19.3.0.0.0|STARTED|ALLOWED|STARTED|{up}",

        # ORCL CDB — 3 PDB rows (22-field)
        # ORCLPDB1 — healthy
        f"ORCL|19.3.0.0.0|OPEN|ALLOWED|STARTED|{up}|1481122484"
        f"|ARCHIVELOG|PRIMARY|NO|ORCL|20200115120000|YES|0"
        f"|ORCLPDB1|1|READ WRITE|NO|10737418240|0|{up}|8192",
        # ORCLPDB2 — healthy (tablespace nearly full is the alert, not instance)
        f"ORCL|19.3.0.0.0|OPEN|ALLOWED|STARTED|{up}|1481122484"
        f"|ARCHIVELOG|PRIMARY|NO|ORCL|20200115120000|YES|0"
        f"|ORCLPDB2|2|READ WRITE|NO|10737418240|0|{up}|8192",
        # ORCLPDB3 — open read write (job is the alert)
        f"ORCL|19.3.0.0.0|OPEN|ALLOWED|STARTED|{up}|1481122484"
        f"|ARCHIVELOG|PRIMARY|NO|ORCL|20200115120000|YES|0"
        f"|ORCLPDB3|3|READ WRITE|NO|5368709120|0|{up}|8192",

        # STDBY — 13-field physical standby
        f"STDBY|19.3.0.0.0|MOUNTED|ALLOWED|STARTED|{ups}|2591873321"
        f"|ARCHIVELOG|PHYSICAL STANDBY|NO|STDBY|20210601090000|{hostname}",

        # DEVDB — 13-field non-CDB standalone dev
        f"DEVDB|19.3.0.0.0|OPEN|ALLOWED|STARTED|{ups}|3714085920"
        f"|NOARCHIVELOG|PRIMARY|NO|DEVDB|20230301080000|{hostname}",
    ]
    return "<<<oracle_instance:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_tablespaces ───────────────────────────────────────────────

def _oracle_tablespaces() -> str:
    """
    14-field format:
      SID|DATAFILE_PATH|TS_NAME|DATAFILE_STATUS|AUTOEXTENSIBLE|
      SIZE_BLOCKS|MAX_SIZE_BLOCKS|USED_BLOCKS|INCREMENT_SIZE_BLOCKS|
      FILE_ONLINE_STATUS|BLOCK_SIZE_BYTES|TS_STATUS|FREE_SPACE_BLOCKS|TS_TYPE
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
        # ── ORCL (CDB root — container-level tablespaces) ──────────────────
        row("ORCL", "/u01/oradata/orcl/system01.dbf",  "SYSTEM",   "PERMANENT", True,   820,  32768,  616,  128, "ONLINE", "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/sysaux01.dbf",  "SYSAUX",   "PERMANENT", True,   540,  16384,  278,  128, "ONLINE", "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/undotbs01.dbf", "UNDOTBS1", "UNDO",      True,   512,   8192,  314,   64, "ONLINE", "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/temp01.dbf",    "TEMP",     "TEMPORARY", True,  2048,  32768,  128,  128,  "TEMP",  "ONLINE"),
        row("ORCL", "/u01/oradata/orcl/users01.dbf",   "USERS",    "PERMANENT", True,   128,  32768,   64,  128, "ONLINE", "ONLINE"),

        # ── ORCLPDB1 — healthy PDB ─────────────────────────────────────────
        row("ORCL.ORCLPDB1", "/u01/oradata/orcl/pdb1/system01.dbf",  "SYSTEM",   "PERMANENT", True,   410,   8192,  280,  128, "ONLINE", "ONLINE"),
        row("ORCL.ORCLPDB1", "/u01/oradata/orcl/pdb1/sysaux01.dbf",  "SYSAUX",   "PERMANENT", True,   280,   8192,  196,  128, "ONLINE", "ONLINE"),
        row("ORCL.ORCLPDB1", "/u01/oradata/orcl/pdb1/data01.dbf",    "DATA",     "PERMANENT", True,  3200,  65536, 1600,  256, "ONLINE", "ONLINE"),
        row("ORCL.ORCLPDB1", "/u01/oradata/orcl/pdb1/idx01.dbf",     "IDX",      "PERMANENT", True,  1024,  16384,  512,  128, "ONLINE", "ONLINE"),
        row("ORCL.ORCLPDB1", "/u01/oradata/orcl/pdb1/temp01.dbf",    "TEMP",     "TEMPORARY", True,   512,   4096,   64,   64,  "TEMP",  "ONLINE"),

        # ── ORCLPDB2 — DATA ~94 % → WARN/CRIT ─────────────────────────────
        row("ORCL.ORCLPDB2", "/u01/oradata/orcl/pdb2/system01.dbf",  "SYSTEM",   "PERMANENT", True,   410,   8192,  340,  128, "ONLINE", "ONLINE"),
        row("ORCL.ORCLPDB2", "/u01/oradata/orcl/pdb2/sysaux01.dbf",  "SYSAUX",   "PERMANENT", True,   280,   8192,  200,  128, "ONLINE", "ONLINE"),
        row("ORCL.ORCLPDB2", "/u01/oradata/orcl/pdb2/data01.dbf",    "DATA",     "PERMANENT", False, 7936,   7936, 7526,    0, "ONLINE", "ONLINE"),  # ~94 %, autoextend OFF
        row("ORCL.ORCLPDB2", "/u01/oradata/orcl/pdb2/temp01.dbf",    "TEMP",     "TEMPORARY", True,   512,   4096,   64,   64,  "TEMP",  "ONLINE"),

        # ── ORCLPDB3 — healthy (job is the alert) ─────────────────────────
        row("ORCL.ORCLPDB3", "/u01/oradata/orcl/pdb3/system01.dbf",  "SYSTEM",   "PERMANENT", True,   410,   8192,  260,  128, "ONLINE", "ONLINE"),
        row("ORCL.ORCLPDB3", "/u01/oradata/orcl/pdb3/sysaux01.dbf",  "SYSAUX",   "PERMANENT", True,   280,   8192,  180,  128, "ONLINE", "ONLINE"),
        row("ORCL.ORCLPDB3", "/u01/oradata/orcl/pdb3/etl01.dbf",     "ETL_DATA", "PERMANENT", True,  4096,  32768, 2048,  256, "ONLINE", "ONLINE"),
        row("ORCL.ORCLPDB3", "/u01/oradata/orcl/pdb3/temp01.dbf",    "TEMP",     "TEMPORARY", True,   512,   4096,   32,   64,  "TEMP",  "ONLINE"),

        # ── STDBY — standby tablespaces (MOUNTED — no tablespace data expected,
        #            but mk_oracle still queries and may return rows) ─────────
        row("STDBY", "/u01/oradata/stdby/system01.dbf",  "SYSTEM",   "PERMANENT", True,   820,  32768,  616,  128, "ONLINE", "ONLINE"),
        row("STDBY", "/u01/oradata/stdby/sysaux01.dbf",  "SYSAUX",   "PERMANENT", True,   540,  16384,  278,  128, "ONLINE", "ONLINE"),
        row("STDBY", "/u01/oradata/stdby/data01.dbf",    "DATA",     "PERMANENT", True,  3200,  65536, 1800,  256, "ONLINE", "ONLINE"),
        row("STDBY", "/u01/oradata/stdby/undotbs01.dbf", "UNDOTBS1", "UNDO",      True,   512,   8192,  280,   64, "ONLINE", "ONLINE"),
        row("STDBY", "/u01/oradata/stdby/temp01.dbf",    "TEMP",     "TEMPORARY", True,  2048,  32768,   96,  128,  "TEMP",  "ONLINE"),

        # ── DEVDB — TEMP tablespace OFFLINE → WARN ────────────────────────
        row("DEVDB", "/u01/oradata/devdb/system01.dbf",  "SYSTEM",   "PERMANENT", True,   410,   8192,  300,  128, "ONLINE", "ONLINE"),
        row("DEVDB", "/u01/oradata/devdb/sysaux01.dbf",  "SYSAUX",   "PERMANENT", True,   280,   8192,  190,  128, "ONLINE", "ONLINE"),
        row("DEVDB", "/u01/oradata/devdb/data01.dbf",    "DATA",     "PERMANENT", True,  2048,  32768,  900,  256, "ONLINE", "ONLINE"),
        row("DEVDB", "/u01/oradata/devdb/users01.dbf",   "USERS",    "PERMANENT", True,   128,   4096,   60,   64, "ONLINE", "ONLINE"),
        row("DEVDB", "/u01/oradata/devdb/temp01.dbf",    "TEMP",     "TEMPORARY", True,   512,   4096,    0,   64,  "TEMP",  "OFFLINE"),  # OFFLINE → alert
    ]
    return "<<<oracle_tablespaces:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_sessions ──────────────────────────────────────────────────

def _oracle_sessions() -> str:
    """
    4-field format:
      SID|CURRENT_SESSIONS|SESSIONS_LIMIT|MAX_UTILIZATION
    """
    rows = [
        "ORCL|82|300|110",
        "STDBY|14|150|20",
        "DEVDB|9|100|15",
    ]
    return "<<<oracle_sessions:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_logswitches ───────────────────────────────────────────────

def _oracle_logswitches() -> str:
    """
    2-field format:
      SID|LOGSWITCHES_LAST_60_MINUTES
    """
    rows = [
        "ORCL|8",
        "DEVDB|1",
    ]
    return "<<<oracle_logswitches:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_undostat ──────────────────────────────────────────────────

def _oracle_undostat() -> str:
    """
    6-field format:
      SID|ACTIVEBLKS|MAXCONCURRENCY|TUNED_UNDORETENTION|MAXQUERYLEN|NOSPACEERRCNT
    """
    rows = [
        "ORCL|320|12|900|480|0",
        "STDBY|40|3|900|180|0",
        "DEVDB|48|4|600|240|0",
    ]
    return "<<<oracle_undostat:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_recovery_area ─────────────────────────────────────────────

def _oracle_recovery_area() -> str:
    """
    6-field format:
      SID|USED_PCT|SPACE_LIMIT_MB|SPACE_USED_MB|SPACE_RECLAIMABLE_MB|FLASHBACK_ON

    FRA diskgroup separate in oracle_asm_diskgroup.
    """
    rows = [
        "ORCL|42|51200|21504|4096|YES",
        "STDBY|38|51200|19456|2048|NO",
        "DEVDB|15|10240|1536|512|NO",
    ]
    return "<<<oracle_recovery_area:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_processes ─────────────────────────────────────────────────

def _oracle_processes() -> str:
    """
    3-field format:
      SID|CURRENT_PROCESSES|PROCESSES_LIMIT
    """
    rows = [
        "+ASM|32|100",
        "ORCL|148|300",
        "STDBY|58|150",
        "DEVDB|24|100",
    ]
    return "<<<oracle_processes:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_rman ──────────────────────────────────────────────────────

def _oracle_rman() -> str:
    """
    8-field format:
      SID|STATUS|START_TIME|END_TIME|BACKUPTYPE|INCREMENTAL_LEVEL|
      BACKUPAGE_MINUTES|INCREMENTAL_CHANGE_SCN

    STDBY has no backup entries → Checkmk raises CRIT for missing backup.
    """
    now = datetime.datetime.now()
    fmt = "%Y-%m-%d_%H:%M:%S"

    def ts(delta_hours: float = 0) -> str:
        return (now - datetime.timedelta(hours=delta_hours)).strftime(fmt)

    def age(delta_hours: float) -> int:
        return int(delta_hours * 60)

    rows = [
        # ORCL — healthy: full last weekend, incr last night, archlog recent
        f"ORCL|COMPLETED|{ts(49)}|{ts(48)}|DB_FULL||{age(49)}|8485000",
        f"ORCL|COMPLETED|{ts(21)}|{ts(20.5)}|DB_INCR|1|{age(21)}|8490000",
        f"ORCL|COMPLETED||{ts(1)}|ARCHIVELOG||{age(1)}|",
        f"ORCL|COMPLETED||{ts(12)}|CONTROLFILE||{age(12)}|0",
        # DEVDB — only incremental, no full backup on record → may WARN
        f"DEVDB|COMPLETED|{ts(22)}|{ts(21.5)}|DB_INCR|1|{age(22)}|5000000",
        f"DEVDB|COMPLETED||{ts(2)}|ARCHIVELOG||{age(2)}|",
        # STDBY — intentionally NO rows → CRIT: no backup
    ]
    return "<<<oracle_rman:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_jobs ──────────────────────────────────────────────────────

def _oracle_jobs() -> str:
    """
    10-field format:
      SID|JOB_OWNER|JOB_NAME|JOB_STATE|LAST_RUN_DURATION_SEC|RUN_COUNT|
      ENABLED|NEXT_RUN_DATE|SCHEDULE_NAME|LAST_RUN_STATUS
    """
    now = datetime.datetime.now()

    def next_run(delta_hours: float) -> str:
        dt = now + datetime.timedelta(hours=delta_hours)
        return dt.strftime("%d-%b-%y %I.%M.%S.000000 %p EUROPE/BERLIN").upper()

    rows = [
        # ORCL jobs — all healthy
        f"ORCL|SYS|GATHER_STATS_JOB|SCHEDULED|52|900|TRUE|{next_run(16)}|-|SUCCEEDED",
        f"ORCL|SYS|AUTO_OPTIMIZER_STATS_COLLECTION|SCHEDULED|38|1300|TRUE|{next_run(22)}|-|SUCCEEDED",
        f"ORCL|SYS|PURGE_LOG|SCHEDULED|4|400|TRUE|{next_run(0.5)}|-|SUCCEEDED",
        f"ORCL|SYS|ARCHIVE_LOG_BACKUP|SCHEDULED|10|760|TRUE|{next_run(4)}|-|SUCCEEDED",
        f"ORCL|SYS|SPACE_ADVISOR_TASK|SCHEDULED|90|180|TRUE|{next_run(20)}|-|SUCCEEDED",
        # ORCLPDB1 — healthy
        f"ORCL.ORCLPDB1|APP_OWNER|NIGHTLY_REPORT|SCHEDULED|120|365|TRUE|{next_run(6)}|NIGHTLY_SCH|SUCCEEDED",
        # ORCLPDB3 — ETL job BROKEN → CRIT
        f"ORCL.ORCLPDB3|ETL_OWNER|ETL_LOAD_JOB|BROKEN|0|214|TRUE|{next_run(8)}|ETL_SCHEDULE|FAILED",
        # DEVDB
        f"DEVDB|SYS|GATHER_STATS_JOB|SCHEDULED|18|200|TRUE|{next_run(18)}|-|SUCCEEDED",
    ]
    return "<<<oracle_jobs:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_dataguard_stats ──────────────────────────────────────────

def _oracle_dataguard_stats() -> str:
    """
    5-field format:
      SID|STATUS_DEST|TARGET_DEST|ARCHIVER_DEST|APPLY_DELAY_SEC

    STDBY apply lag intentionally 7200s → WARN in Checkmk.
    """
    rows = [
        # ORCL is primary — it reports the standby destination status
        "ORCL|VALID|STANDBY|SUCCEEDED|0",
        # STDBY reports its own apply stats — 2-hour lag
        "STDBY|VALID|LOCAL|SUCCEEDED|7200",
    ]
    return "<<<oracle_dataguard_stats:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_locks ─────────────────────────────────────────────────────

def _oracle_locks() -> str:
    """
    7-field format:
      SID|INST_ID|OS_USER|ORACLE_USER|SID_LOCK|DURATION_SECS|SQL_TEXT_SNIPPET

    Lock held 1950s in ORCL → CRIT (default threshold is 1800s).
    """
    rows = [
        # Normal short-lived lock in ORCL
        "ORCL|1|oracle|APP_OWNER|1245|12|UPDATE orders SET status=:1 WHERE id=:2",
        # Long lock → CRIT
        "ORCL|1|appuser|APP_OWNER|1301|1950|UPDATE inventory SET qty=qty-:1 WHERE sku=:2",
        # Short lock in DEVDB
        "DEVDB|1|devuser|SCOTT|55|8|INSERT INTO test_table VALUES (:1,:2,:3)",
    ]
    return "<<<oracle_locks:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_longactivesessions ───────────────────────────────────────

def _oracle_longactivesessions() -> str:
    """
    9-field format:
      SID|INST_ID|OS_USER|ORACLE_USER|MACHINE|PROCESS|SQL_ID|LAST_CALL_ET|STATUS

    DEVDB session active 3600s → WARN.
    """
    rows = [
        # DEVDB — long running session 3600s
        "DEVDB|1|devuser|SCOTT|devhost.local|12345|6j3b8xkqv1mzd|3600|ACTIVE",
        # ORCL — normal medium-duration session
        "ORCL|1|appuser|APP_OWNER|apphost01|23456|g8r2ftpqzs9wy|420|ACTIVE",
    ]
    return "<<<oracle_longactivesessions:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_performance ───────────────────────────────────────────────

def _oracle_performance() -> str:
    """
    4-field format:
      SID|CATEGORY|METRIC_NAME|VALUE

    Categories: sys_time_model, buffer_pool_statistics, librarycache, sga,
                wait_class, ios
    """
    rows = []

    def perf(sid, category, metric, value):
        rows.append(f"{sid}|{category}|{metric}|{value}")

    # ORCL
    perf("ORCL", "sys_time_model", "DB time",              15420000000)
    perf("ORCL", "sys_time_model", "sql execute elapsed time", 9800000000)
    perf("ORCL", "sys_time_model", "parse time elapsed",    420000000)
    perf("ORCL", "sys_time_model", "hard parse elapsed time", 38000000)

    perf("ORCL", "buffer_pool_statistics", "DEFAULT|consistent gets", 9874320)
    perf("ORCL", "buffer_pool_statistics", "DEFAULT|db block gets",    184920)
    perf("ORCL", "buffer_pool_statistics", "DEFAULT|physical reads",    58420)
    perf("ORCL", "buffer_pool_statistics", "DEFAULT|physical writes",   12840)

    perf("ORCL", "librarycache", "SQL AREA|pins",      245000)
    perf("ORCL", "librarycache", "SQL AREA|pin_hits",  243800)
    perf("ORCL", "librarycache", "SQL AREA|reloads",      180)
    perf("ORCL", "librarycache", "SQL AREA|invalidations",  12)

    perf("ORCL", "sga", "total SGA",            4294967296)
    perf("ORCL", "sga", "Database Buffers",     3221225472)
    perf("ORCL", "sga", "Redo Buffers",          536870912)
    perf("ORCL", "sga", "Fixed SGA Size",           112640)

    perf("ORCL", "wait_class", "User I/O|wait_count",          5842)
    perf("ORCL", "wait_class", "User I/O|time_waited",       184200)
    perf("ORCL", "wait_class", "Concurrency|wait_count",        320)
    perf("ORCL", "wait_class", "Concurrency|time_waited",      9800)
    perf("ORCL", "wait_class", "System I/O|wait_count",        1240)
    perf("ORCL", "wait_class", "System I/O|time_waited",      18400)

    perf("ORCL", "ios", "DATA|READS|large",         420)
    perf("ORCL", "ios", "DATA|READS|small",        8400)
    perf("ORCL", "ios", "DATA|WRITES|large",         90)
    perf("ORCL", "ios", "DATA|WRITES|small",         840)

    # DEVDB — lighter load
    perf("DEVDB", "sys_time_model", "DB time",             1240000000)
    perf("DEVDB", "sys_time_model", "sql execute elapsed time", 820000000)
    perf("DEVDB", "buffer_pool_statistics", "DEFAULT|consistent gets", 284000)
    perf("DEVDB", "buffer_pool_statistics", "DEFAULT|physical reads",   18400)
    perf("DEVDB", "sga", "total SGA",           1073741824)
    perf("DEVDB", "sga", "Database Buffers",     805306368)

    return "<<<oracle_performance:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_asm_diskgroup ─────────────────────────────────────────────

def _oracle_asm_diskgroup() -> str:
    """
    12-field format (stripped_line count = 10 after removing +ASM prefix):
      +ASM|MOUNTED|{DGTYPE}|{REBAL}|{SECTOR}|{BLOCK}|{AU}|{TOTAL_MB}|
      {FREE_MB}|{REQ_MIR_FREE_MB}|{USABLE_FILE_MB}|{OFFLINE_DISKS}|{DGNAME}

    Actual parser key: (12, False) in oracle_asm_diskgroup check.
    FRA at 85 % → WARN.
    """
    rows = [
        # DATA — healthy, ~60 % used, NORMAL redundancy
        "+ASM|MOUNTED|NORMAL|N|512|4096|1048576|409600|163840|81920|81920|0|DATA",
        # REDO — small, low utilization
        "+ASM|MOUNTED|NORMAL|N|512|4096|1048576|51200|38400|10240|28160|0|REDO",
        # FRA — 85 % used → WARN
        "+ASM|MOUNTED|EXTERN|N|512|4096|1048576|204800|30720|0|30720|0|FRA",
    ]
    return "<<<oracle_asm_diskgroup:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_recovery_status ──────────────────────────────────────────

def _oracle_recovery_status() -> str:
    """
    6-field format:
      SID|STATUS|TARGET|ARCHIVER|APPLIED_LOG_SEQ|APPLIED_THREAD

    Checkmk check: oracle_recovery_status.
    """
    rows = [
        "ORCL|ENABLED|APPLY|STARTED|8492|1",
        "STDBY|ENABLED|APPLY|STARTED|8490|1",
    ]
    return "<<<oracle_recovery_status:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_crs_version ───────────────────────────────────────────────

def _oracle_crs_version() -> str:
    """
    Single line: CRS_VERSION
    Emitted only on RAC/Grid; included here for completeness.
    """
    return "<<<oracle_crs_version:sep(124)>>>\n19.3.0.0.0\n"


# ── Section: oracle_crs_voting ────────────────────────────────────────────────

def _oracle_crs_voting() -> str:
    """
    3-field format:
      VOTING_DISK|STATUS|SPACE_MB
    Emitted only on Grid with voting disks.
    """
    rows = [
        "VOTING01|ONLINE|1024",
        "VOTING02|ONLINE|1024",
        "VOTING03|ONLINE|1024",
    ]
    return "<<<oracle_crs_voting:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Section: oracle_crs_res ───────────────────────────────────────────────────

def _oracle_crs_res() -> str:
    """
    Resource status lines from crsctl:
      NAME|TARGET|STATE

    Checkmk check: oracle_crs_res.
    """
    rows = [
        "ora.orcl.db|ONLINE|ONLINE",
        "ora.stdby.db|ONLINE|ONLINE",
        "ora.asm|ONLINE|ONLINE",
        "ora.listener.lsnr|ONLINE|ONLINE",
        "ora.scan1.vip|ONLINE|ONLINE",
        "ora.ons|ONLINE|ONLINE",
    ]
    return "<<<oracle_crs_res:sep(124)>>>\n" + "\n".join(rows) + "\n"


# ── Agent header ──────────────────────────────────────────────────────────────

def _check_mk_header(hostname: str) -> str:
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


# ── Build full agent output ───────────────────────────────────────────────────

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
        _oracle_dataguard_stats(),
        _oracle_locks(),
        _oracle_longactivesessions(),
        _oracle_performance(),
        _oracle_asm_diskgroup(),
        _oracle_recovery_status(),
        _oracle_crs_version(),
        _oracle_crs_voting(),
        _oracle_crs_res(),
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
    print(
        "SIDs: +ASM | ORCL (CDB+PDB1/2/3) | STDBY (standby) | DEVDB (dev)\n"
        "Alerts: ORCLPDB2 DATA ~94% | FRA 85% | STDBY lag 7200s | "
        "ORCL lock 1950s | ORCLPDB3 ETL BROKEN | STDBY no RMAN | "
        "DEVDB TEMP OFFLINE | DEVDB long session 3600s",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
