#!/usr/bin/env python3
"""
NetApp ONTAP REST API Mock for CheckMK special agent testing.

Simulates a 2-node AFF cluster running ONTAP 9.14.1.
Endpoints are derived from the CheckMK 2.4.x special agent
(cmk/plugins/netapp) which uses the netapp-ontap-cmk library.

Non-OK components for alert testing
  • Aggregate  : aggr1_node01  – 87 % used  (warning threshold 85 %)
  • Disk        : 1.0.13        – state=broken
  • Volume      : vol_legacy_offline – state=offline
  • LUN         : vol_data02/legacy_lun_offline – state=offline
  • Network port : node-02 / e0d – state=down
  • FC port      : node-01 / 0d  – state=error
  • Fan          : shelf-1 node-01, fan-2 – 550 rpm (warning)
  • Temp sensor  : shelf-3 node-02, sensor-3 – 62 °C (warning ≥ 58 °C)
  • SVM          : svm_backup    – state=stopped
  • SnapMirror   : vol_data02 → vol_backup_dest – unhealthy, 2d+ lag

Usage:
  python app.py                  # dev server (HTTP 8080)
  gunicorn --certfile=... app:app  # HTTPS (entrypoint.sh handles this)
"""

import logging
import math
import random
import time
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  [netapp-mock]  %(message)s",
)
logger = logging.getLogger("netapp-mock")

app = Flask(__name__)


# ─── Request logging ──────────────────────────────────────────────────────────
@app.before_request
def _log_request():
    logger.info("→ %s %s  args=%s", request.method, request.path, dict(request.args))


# ─── Randomisation engine ─────────────────────────────────────────────────────
# All metric generators use time-based wave functions so values drift smoothly
# across polls and produce visible peaks/troughs in CheckMK graphs.
# Spike probability per poll: ~8 %  (brief 2-4× surge)

_T0 = time.time()   # process start epoch


def _now_phase(period_s: float, offset: float = 0.0) -> float:
    """Return a [0, 1) phase based on wall-clock time and a period in seconds."""
    return ((time.time() - _T0 + offset) % period_s) / period_s


def _wave(period_s: float, offset: float = 0.0) -> float:
    """Smooth sine wave in [0, 1] over *period_s* seconds."""
    return (1 + math.sin(2 * math.pi * _now_phase(period_s, offset))) / 2


def rng(base: float, pct: float = 0.08) -> float:
    """
    Randomise *base* with:
      • gaussian noise   ± pct
      • slow sine drift  (5-min period)
      • occasional spike (8 % chance → 2-4× base)
    Always returns a non-negative value.
    """
    noise  = random.gauss(0, pct)
    drift  = _wave(300) * pct          # 5-minute gentle wave
    value  = base * (1 + noise + drift)

    # Spike: short 2–4× burst
    if random.random() < 0.08:
        value *= random.uniform(2.0, 4.0)

    return max(0.0, value)


def rng_counter(base: int, per_second: float, pct: float = 0.15) -> int:
    """
    Monotonically-growing counter: base + elapsed * rate + noise.
    *per_second* is the average increment rate.
    Use for bytes_read, total_ops, etc. so graphs show real slopes.
    """
    elapsed = time.time() - _T0
    trend   = elapsed * per_second * (1 + _wave(600) * 0.4)   # 10-min throughput wave
    noise   = random.gauss(0, pct) * per_second * elapsed * 0.05
    spike   = (per_second * random.uniform(30, 120)) if random.random() < 0.06 else 0
    return int(max(0, base + trend + noise + spike))


def rng_cpu(base_pct: float) -> int:
    """
    CPU utilisation as a raw integer percentage.
    Includes a 15-min busy-period wave plus random spikes up to 95 %.
    """
    wave_val = _wave(900, offset=base_pct * 10) * 30   # ±30 % swing over 15 min
    noise    = random.gauss(0, 5)
    spike    = random.uniform(40, 95) if random.random() < 0.05 else 0
    return int(min(99, max(1, base_pct + wave_val + noise + spike)))


def rng_latency(base_us: int) -> int:
    """Latency in microseconds — spikes to 10× on ~5 % of polls."""
    val = base_us * (1 + _wave(120) * 0.5 + random.gauss(0, 0.1))
    if random.random() < 0.05:
        val *= random.uniform(5, 10)
    return int(max(1, val))


def rng_temp(base_c: float) -> int:
    """Temperature as integer °C with slow 20-min thermal drift."""
    return int(max(0, base_c + _wave(1200) * 8 + random.gauss(0, 1)))


def rng_fan(base_rpm: int) -> int:
    """Fan RPM — occasional brief dip to ~60 % of normal."""
    rpm = base_rpm * (1 + _wave(240) * 0.1 + random.gauss(0, 0.03))
    if random.random() < 0.04:
        rpm *= random.uniform(0.55, 0.70)   # brief dip
    return int(max(100, rpm))



def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def collection(records: list, href: str) -> dict:
    """Standard ONTAP REST paginated collection envelope."""
    return {
        "records": records,
        "num_records": len(records),
        "_links": {"self": {"href": href}},
    }


# ─── Seed UUIDs (stable across requests) ─────────────────────────────────────
CL_UUID    = "aabbccdd-0000-0000-0000-000000000000"
NODE1_UUID = "node0001-0000-0000-0000-000000000001"
NODE2_UUID = "node0002-0000-0000-0000-000000000002"
AGGR1_UUID = "aggr0001-0000-0000-0000-000000000001"   # root node-01
AGGR2_UUID = "aggr0002-0000-0000-0000-000000000002"   # data node-01 (WARNING)
AGGR3_UUID = "aggr0003-0000-0000-0000-000000000003"   # data node-02
SVM1_UUID  = "svm00001-0000-0000-0000-000000000001"   # svm_data01
SVM2_UUID  = "svm00002-0000-0000-0000-000000000002"   # svm_backup (STOPPED)

GB = 1_073_741_824  # 1 GiB in bytes

# Stable FC WWPNs — must match fcp_lif:port counter rows
FC_WWPNS = {
    ("node-01", "0a"): ("20:aa:bb:cc:dd:ee:ff:01", "20:00:aa:bb:cc:dd:ee:01"),
    ("node-01", "0b"): ("20:aa:bb:cc:dd:ee:ff:02", "20:00:aa:bb:cc:dd:ee:02"),
    ("node-01", "0c"): ("20:aa:bb:cc:dd:ee:ff:03", "20:00:aa:bb:cc:dd:ee:03"),
    ("node-01", "0d"): ("20:aa:bb:cc:dd:ee:ff:04", "20:00:aa:bb:cc:dd:ee:04"),
    ("node-02", "0a"): ("20:aa:bb:cc:dd:ee:ff:05", "20:00:aa:bb:cc:dd:ee:05"),
    ("node-02", "0b"): ("20:aa:bb:cc:dd:ee:ff:06", "20:00:aa:bb:cc:dd:ee:06"),
    ("node-02", "0c"): ("20:aa:bb:cc:dd:ee:ff:07", "20:00:aa:bb:cc:dd:ee:07"),
    ("node-02", "0d"): ("20:aa:bb:cc:dd:ee:ff:08", "20:00:aa:bb:cc:dd:ee:08"),
}

GB = 1_073_741_824  # 1 GiB in bytes


# ══════════════════════════════════════════════════════════════════════════════
#  /api/cluster
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/cluster")
def get_cluster():
    return jsonify({
        "uuid":          CL_UUID,
        "name":          "cl-mock-01",
        "version": {
            "full":       "NetApp Release 9.14.1RC2: Mon Jan 15 18:00:00 UTC 2024",
            "generation": 9,
            "major":      14,
            "minor":      1,
        },
        "serial_number": "1-80-000001",
        "location":      "DC-East Rack-07",
        "contact":       "storage-admin@example.com",
        "dns_domains":   ["example.com", "storage.example.com"],
        "ntp_servers":   ["10.0.0.1", "10.0.0.2"],
        "_links": {"self": {"href": "/api/cluster"}},
    })


# ══════════════════════════════════════════════════════════════════════════════
#  /api/cluster/nodes
# ══════════════════════════════════════════════════════════════════════════════
def _node(uuid, name, partner_uuid, partner_name, cpu_base_pct=35):
    cpu_pct      = rng_cpu(cpu_base_pct)
    cpu_base_raw = 100_000_000
    cpu_raw      = int(cpu_pct / 100 * cpu_base_raw)
    return {
        "uuid":                uuid,
        "name":                name,
        "model":               "AFF-A400",
        "system_machine_type": "AFF-A400",
        "serial_number":       f"SN-{name.upper()}-001",
        "system_id":           str(random.randint(1000000000, 9999999999)),
        "uptime":              int(time.time() - _T0 + 5_184_000),   # stable uptime
        "state":               "up",
        "membership":          "available",
        "date":                now_iso(),
        "nvram": {
            "battery_state": "battery_ok",
        },
        "controller": {
            "over_temperature":            "false",
            "failed_fan_count":            0,
            "failed_fan_message":          "",
            "failed_power_supply_count":   0,
            "failed_power_supply_message": "",
            "cpu": {
                "count":     16,
                "processor": "Intel Xeon Silver 4216",
            },
        },
        "ha": {
            "enabled":  True,
            "takeover": {"state": "ready"},
            "partners": [{"name": partner_name, "uuid": partner_uuid}],
        },
        "metric": {
            "processor_utilization": cpu_pct,
            "timestamp":             now_iso(),
            "status":                "ok",
        },
        "statistics": {
            "processor_utilization_raw":  cpu_raw,
            "processor_utilization_base": cpu_base_raw,
            "timestamp":                  now_iso(),
            "status":                     "ok",
        },
        "version": {
            "full":       "NetApp Release 9.14.1RC2",
            "generation": 9,
            "major":      14,
            "minor":      1,
        },
        "_links": {"self": {"href": f"/api/cluster/nodes/{uuid}"}},
    }



@app.route("/api/cluster/nodes")
def get_nodes():
    return jsonify(collection(
        [
            _node(NODE1_UUID, "node-01", NODE2_UUID, "node-02"),
            _node(NODE2_UUID, "node-02", NODE1_UUID, "node-01", cpu_base_pct=45),
        ],
        "/api/cluster/nodes",
    ))


@app.route("/api/cluster/nodes/<node_uuid>")
def get_node(node_uuid):
    if node_uuid == NODE1_UUID:
        return jsonify(_node(NODE1_UUID, "node-01", NODE2_UUID, "node-02"))
    if node_uuid == NODE2_UUID:
        return jsonify(_node(NODE2_UUID, "node-02", NODE1_UUID, "node-01", cpu_base_pct=45))
    return jsonify({"error": {"code": "4", "message": "Node not found"}}), 404


# ══════════════════════════════════════════════════════════════════════════════
#  /api/svm/svms
# ══════════════════════════════════════════════════════════════════════════════
def _svm_stats():
    rx = int(rng(50_000_000))
    tx = int(rng(30_000_000))
    return {
        "iops_raw": {
            "read":  int(rng(8_000)),
            "write": int(rng(4_000)),
            "other": int(rng(200)),
            "total": int(rng(12_200)),
        },
        "throughput_raw": {
            "read":  rx,
            "write": tx,
            "other": int(rng(500_000)),
            "total": rx + tx,
        },
        "latency_raw": {
            "read":  int(rng(1_200)),
            "write": int(rng(800)),
            "other": int(rng(300)),
            "total": int(rng(2_300)),
        },
        "timestamp": now_iso(),
        "status":    "ok",
    }


@app.route("/api/svm/svms")
def get_svms():
    records = [
        {
            "uuid":  SVM1_UUID,
            "name":  "svm_data01",
            "state": "running",
            "subtype": "default",
            "allowed_protocols": ["nfs", "cifs", "iscsi"],
            "aggregates": [{"name": "aggr1_node01", "uuid": AGGR2_UUID}],
            "statistics": _svm_stats(),
            "_links": {"self": {"href": f"/api/svm/svms/{SVM1_UUID}"}},
        },
        {
            "uuid":  SVM2_UUID,
            "name":  "svm_backup",
            "state": "stopped",          # ← NON-OK: stopped SVM
            "subtype": "dp_destination",
            "allowed_protocols": ["nfs"],
            "aggregates": [{"name": "aggr1_node02", "uuid": AGGR3_UUID}],
            "statistics": {"status": "error", "timestamp": now_iso()},
            "_links": {"self": {"href": f"/api/svm/svms/{SVM2_UUID}"}},
        },
    ]
    return jsonify(collection(records, "/api/svm/svms"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/storage/aggregates
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/storage/aggregates")
def get_aggregates():
    records = [
        {   # Root aggregate – node-01
            "uuid":  AGGR1_UUID,
            "name":  "aggr0_node01",
            "state": "online",
            "node":      {"name": "node-01", "uuid": NODE1_UUID},
            "home_node": {"name": "node-01", "uuid": NODE1_UUID},
            "block_storage": {"primary": {"disk_count": 3, "raid_type": "raid_dp"}},
            "space": {
                "block_storage": {
                    "size":                   int(rng(200 * GB)),
                    "available":              int(rng(130 * GB)),
                    "used":                   int(rng(70  * GB)),
                    "full_threshold_percent": 98,
                },
                "efficiency": {"savings": int(rng(5 * GB)), "ratio": 1.3},
            },
            "_links": {"self": {"href": f"/api/storage/aggregates/{AGGR1_UUID}"}},
        },
        {   # Data aggregate node-01 – HIGH UTILISATION (warning at 85 %)
            "uuid":  AGGR2_UUID,
            "name":  "aggr1_node01",
            "state": "online",
            "node":      {"name": "node-01", "uuid": NODE1_UUID},
            "home_node": {"name": "node-01", "uuid": NODE1_UUID},
            "block_storage": {"primary": {"disk_count": 12, "raid_type": "raid_dp"}},
            "space": {
                "block_storage": {
                    "size":                   int(rng(20_000 * GB)),
                    "available":              int(rng(2_600  * GB)),   # ~87 % used ← WARNING
                    "used":                   int(rng(17_400 * GB)),
                    "full_threshold_percent": 85,
                },
                "efficiency": {"savings": int(rng(3_000 * GB)), "ratio": 2.1},
            },
            "_links": {"self": {"href": f"/api/storage/aggregates/{AGGR2_UUID}"}},
        },
        {   # Data aggregate node-02 – healthy
            "uuid":  AGGR3_UUID,
            "name":  "aggr1_node02",
            "state": "online",
            "node":      {"name": "node-02", "uuid": NODE2_UUID},
            "home_node": {"name": "node-02", "uuid": NODE2_UUID},
            "block_storage": {"primary": {"disk_count": 12, "raid_type": "raid_dp"}},
            "space": {
                "block_storage": {
                    "size":                   int(rng(20_000 * GB)),
                    "available":              int(rng(10_800 * GB)),   # ~46 % used
                    "used":                   int(rng(9_200  * GB)),
                    "full_threshold_percent": 85,
                },
                "efficiency": {"savings": int(rng(1_500 * GB)), "ratio": 1.8},
            },
            "_links": {"self": {"href": f"/api/storage/aggregates/{AGGR3_UUID}"}},
        },
    ]
    return jsonify(collection(records, "/api/storage/aggregates"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/storage/volumes
# ══════════════════════════════════════════════════════════════════════════════
def _vol(uuid, name, svm_name, svm_uuid, aggr_name, state="online",
         size_gb=1024, avail_pct=0.50, snap_reserve_pct=5,
         files_max=1_000_000, files_used_pct=0.10):
    size  = size_gb * GB
    avail = int(size * avail_pct)
    used  = size - avail
    snap_res   = int(size * snap_reserve_pct / 100)
    snap_used  = int(snap_res * rng(0.6))
    return {
        "uuid":  uuid,
        "name":  name,
        "state": state,
        "msid":  random.randint(2_000_000_000, 2_100_000_000),
        "svm":   {"name": svm_name, "uuid": svm_uuid},
        "aggregates": [{"name": aggr_name}],
        "type":  "rw",
        "space": {
            "available":    int(rng(avail)),
            "afs_total":    size,
            "used":         int(rng(used)),
            "logical_space": {
                "enforcement": False,
                "used":        int(rng(used * 1.05)),
                "available":   int(rng(avail)),
            },
            "snapshot": {
                "reserve_size":    snap_res,
                "used":            int(rng(snap_used)),
                "reserve_percent": snap_reserve_pct,
            },
        },
        "files": {
            "maximum": files_max,
            "used":    int(files_max * rng(files_used_pct)),
        },
        "is_constituent": False,
        "_links": {"self": {"href": f"/api/storage/volumes/{uuid}"}},
    }


@app.route("/api/storage/volumes")
def get_volumes():
    # Respect ?is_constituent filter (agent passes this)
    is_constituent = request.args.get("is_constituent", "").lower()

    records = [
        _vol("vol-0001", "vol_root_node01",   "svm_data01", SVM1_UUID, "aggr0_node01",
             size_gb=30,     avail_pct=0.72),
        _vol("vol-0002", "vol_data01",         "svm_data01", SVM1_UUID, "aggr1_node01",
             size_gb=5_000,  avail_pct=0.42),
        _vol("vol-0003", "vol_data02",         "svm_data01", SVM1_UUID, "aggr1_node01",
             size_gb=8_000,  avail_pct=0.18, snap_reserve_pct=20),
        _vol("vol-0004", "vol_nfs_home",       "svm_data01", SVM1_UUID, "aggr1_node01",
             size_gb=2_000,  avail_pct=0.55),
        _vol("vol-0005", "vol_cifs_share",     "svm_data01", SVM1_UUID, "aggr1_node02",
             size_gb=3_000,  avail_pct=0.37),
        _vol("vol-0006", "vol_oracle_data",    "svm_data01", SVM1_UUID, "aggr1_node02",
             size_gb=10_000, avail_pct=0.47),
        _vol("vol-0007", "vol_oracle_redo",    "svm_data01", SVM1_UUID, "aggr1_node02",
             size_gb=500,    avail_pct=0.68),
        _vol("vol-0008", "vol_backup_dest",    "svm_backup", SVM2_UUID, "aggr1_node02",
             size_gb=15_000, avail_pct=0.33),
        _vol("vol-0009", "vol_snapvault_dest", "svm_backup", SVM2_UUID, "aggr1_node02",
             size_gb=10_000, avail_pct=0.51),
        # NON-OK: offline volume
        {**_vol("vol-000A", "vol_legacy_offline", "svm_data01", SVM1_UUID, "aggr1_node01",
                size_gb=500, avail_pct=0.60), "state": "offline"},
    ]

    # Filter by is_constituent if specified
    if is_constituent in ("true", "false"):
        want = is_constituent == "true"
        records = [v for v in records if v.get("is_constituent") == want]

    return jsonify(collection(records, "/api/storage/volumes"))


@app.route("/api/storage/volumes/<vol_uuid>")
def get_volume(vol_uuid):
    # Proxy through the list and filter — simple for a mock
    all_resp = get_volumes()
    for rec in all_resp.get_json()["records"]:
        if rec["uuid"] == vol_uuid:
            return jsonify(rec)
    return jsonify({"error": {"code": "4", "message": "Volume not found"}}), 404


@app.route("/api/storage/volumes/<vol_uuid>/snapshots")
def get_volume_snapshots(vol_uuid):
    snaps = [
        {
            "uuid":        f"{vol_uuid}-snap-001",
            "name":        "nightly.2024-01-15_0005",
            "create_time": (datetime.now(timezone.utc) - timedelta(hours=18)).isoformat(timespec="seconds"),
            "size":        int(rng(2 * GB)),
            "state":       "valid",
        },
        {
            "uuid":        f"{vol_uuid}-snap-002",
            "name":        "nightly.2024-01-14_0005",
            "create_time": (datetime.now(timezone.utc) - timedelta(hours=42)).isoformat(timespec="seconds"),
            "size":        int(rng(2.5 * GB)),
            "state":       "valid",
        },
    ]
    return jsonify(collection(snaps, f"/api/storage/volumes/{vol_uuid}/snapshots"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/storage/disks
# ══════════════════════════════════════════════════════════════════════════════
def _disk(name, node, dtype="SAS", state="present", base_rpm=10_000,
          vendor="SEAGATE", model="X422A-R6", capacity_gb=1_800):
    bay = int(name.split(".")[-1])
    capacity_bytes = capacity_gb * GB
    bytes_per_sector = 512
    return {
        "name":  name,
        "uid":   f"5000c500:{name.replace('.', '').upper()}0000",
        "state": state,
        "type":  dtype,
        "node":      {"name": node},
        "home_node": {"name": node},
        "rpm":       int(rng(base_rpm)) if dtype not in ("SSD", "NVME") else 0,
        "vendor":    vendor,
        "model":     model,
        "bay":       bay,
        "shelf":     {"uid": f"SHELF-{name.split('.')[0]}"},
        "container_type": "aggregate" if state == "present" else state,
        "bytes_per_sector": bytes_per_sector,
        "sector_count":     capacity_bytes // bytes_per_sector,
        "capacity":  {"size": capacity_bytes},
        "_links": {"self": {"href": f"/api/storage/disks/{name}"}},
    }


@app.route("/api/storage/disks")
def get_disks():
    disks = []
    for i in range(1, 13):
        disks.append(_disk(f"1.0.{i:02d}", "node-01", base_rpm=10_000))
    for i in range(1, 13):
        disks.append(_disk(f"2.0.{i:02d}", "node-02", base_rpm=10_000))
    # Flash Pool SSDs
    for n, node in [("1.1", "node-01"), ("2.1", "node-02")]:
        disks.append(_disk(f"{n}.01", node, dtype="SSD", base_rpm=0,
                           vendor="SAMSUNG", model="X806A-R6", capacity_gb=960))
        disks.append(_disk(f"{n}.02", node, dtype="SSD", base_rpm=0,
                           vendor="SAMSUNG", model="X806A-R6", capacity_gb=960))
    # NON-OK: broken disk on node-01
    disks.append(_disk("1.0.13", "node-01", state="broken"))
    return jsonify(collection(disks, "/api/storage/disks"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/storage/luns
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/storage/luns")
def get_luns():
    records = [
        {
            "uuid": "lun00001-0000-0000-0000-000000000001",
            "name": "/vol/vol_oracle_data/oracle_lun01",
            "svm":     {"name": "svm_data01", "uuid": SVM1_UUID},
            "location": {
                "volume": {"name": "vol_oracle_data"},
                "qtree":  {"name": ""},
                "logical_unit": "oracle_lun01",
            },
            "enabled":   True,
            "state":     "online",
            "read_only": False,
            "os_type":   "linux",
            "space": {
                "size": int(rng(2_000 * GB)),
                "used": int(rng(1_200 * GB)),
                "guarantee": {"requested": False, "reserved": False},
            },
            "_links": {"self": {"href": "/api/storage/luns/lun00001-0000-0000-0000-000000000001"}},
        },
        {
            "uuid": "lun00002-0000-0000-0000-000000000002",
            "name": "/vol/vol_oracle_redo/oracle_lun02",
            "svm":     {"name": "svm_data01", "uuid": SVM1_UUID},
            "location": {
                "volume": {"name": "vol_oracle_redo"},
                "qtree":  {"name": ""},
                "logical_unit": "oracle_lun02",
            },
            "enabled":   True,
            "state":     "online",
            "read_only": False,
            "os_type":   "linux",
            "space": {
                "size": int(rng(200 * GB)),
                "used": int(rng(80  * GB)),
                "guarantee": {"requested": True, "reserved": True},
            },
            "_links": {"self": {"href": "/api/storage/luns/lun00002-0000-0000-0000-000000000002"}},
        },
        {
            "uuid": "lun00003-0000-0000-0000-000000000003",
            "name": "/vol/vol_data01/windows_lun01",
            "svm":     {"name": "svm_data01", "uuid": SVM1_UUID},
            "location": {
                "volume": {"name": "vol_data01"},
                "qtree":  {"name": ""},
                "logical_unit": "windows_lun01",
            },
            "enabled":   True,
            "state":     "online",
            "read_only": False,
            "os_type":   "windows_2008",
            "space": {
                "size": int(rng(500 * GB)),
                "used": int(rng(310 * GB)),
                "guarantee": {"requested": False, "reserved": False},
            },
            "_links": {"self": {"href": "/api/storage/luns/lun00003-0000-0000-0000-000000000003"}},
        },
        {   # NON-OK: offline LUN
            "uuid": "lun00004-0000-0000-0000-000000000004",
            "name": "/vol/vol_data02/legacy_lun_offline",
            "svm":     {"name": "svm_data01", "uuid": SVM1_UUID},
            "location": {
                "volume": {"name": "vol_data02"},
                "qtree":  {"name": ""},
                "logical_unit": "legacy_lun_offline",
            },
            "enabled":   False,
            "state":     "offline",
            "read_only": False,
            "os_type":   "linux",
            "space": {
                "size": int(rng(100 * GB)),
                "used": 0,
                "guarantee": {"requested": False, "reserved": False},
            },
            "_links": {"self": {"href": "/api/storage/luns/lun00004-0000-0000-0000-000000000004"}},
        },
    ]
    return jsonify(collection(records, "/api/storage/luns"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/network/ethernet/ports
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/network/ethernet/ports")
def get_ethernet_ports():
    records = []
    for node_name, node_uuid in [("node-01", NODE1_UUID), ("node-02", NODE2_UUID)]:
        for iface in ("e0a", "e0b", "e0c", "e0d"):
            # NON-OK: e0d on node-02 is down
            state = "down" if (node_name == "node-02" and iface == "e0d") else "up"
            records.append({
                "uuid":             f"port-{node_name}-{iface}",
                "name":             iface,
                "node":             {"name": node_name, "uuid": node_uuid},
                "state":            state,
                "enabled":          state == "up",
                "type":             "physical",
                "speed":            25_000,
                "port_speed":       25_000,
                "mtu":              9000,
                "broadcast_domain": {"name": "Default", "uuid": "bd-default-001"},
                "mac_address":      "00:50:56:%02x:%02x:%02x" % (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                ),
                "_links": {"self": {"href": f"/api/network/ethernet/ports/{node_name}/{iface}"}},
            })
    return jsonify(collection(records, "/api/network/ethernet/ports"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/network/ethernet/interfaces   (IP LIFs)
# ══════════════════════════════════════════════════════════════════════════════
def _lif_stats():
    rx = rng_counter(100_000_000_000, 50_000_000)
    tx = rng_counter(60_000_000_000,  30_000_000)
    return {
        "received_raw": {"bytes": rx, "packets": rx // 1500},
        "sent_raw":     {"bytes": tx, "packets": tx // 1500},
        "throughput": {
            "read":  int(rng(50_000_000)),
            "write": int(rng(30_000_000)),
        },
        "timestamp":    now_iso(),
        "status":       "ok",
    }


LIF_SEED = [
    ("iface-0001", "data_lif_01",   SVM1_UUID, "svm_data01", "192.168.10.100", "node-01", "e0a"),
    ("iface-0002", "data_lif_02",   SVM1_UUID, "svm_data01", "192.168.10.101", "node-01", "e0b"),
    ("iface-0003", "nfs_lif_01",    SVM1_UUID, "svm_data01", "192.168.10.102", "node-02", "e0a"),
    ("iface-0004", "nfs_lif_02",    SVM1_UUID, "svm_data01", "192.168.10.103", "node-02", "e0b"),
    ("iface-0005", "iscsi_lif_01",  SVM1_UUID, "svm_data01", "192.168.20.100", "node-01", "e0c"),
    ("iface-0006", "cluster_mgmt",  None,      None,          "192.168.10.50",  "node-01", "e0c"),
]


@app.route("/api/network/ethernet/interfaces")
def get_ethernet_interfaces():
    records = []
    for uuid, name, svm_uuid, svm_name, ip, node, port in LIF_SEED:
        rec = {
            "uuid":    uuid,
            "name":    name,
            "state":   "up",
            "enabled": True,
            "speed":   25000,
            "ip": {"address": ip, "netmask": "255.255.255.0", "family": "ipv4"},
            "broadcast_domain": {"name": "Default"},
            "location": {
                "node":      {"name": node},
                "home_node": {"name": node},
                "port":      {"name": port, "node": {"name": node}, "speed": 25000},
                "home_port": {"name": port, "node": {"name": node}, "speed": 25000},
                "failover":     "broadcast_domain_only",
                "auto_revert":  True,
                "is_home":      True,
            },
            "statistics": _lif_stats(),
            "_links": {"self": {"href": f"/api/network/ethernet/interfaces/{uuid}"}},
        }
        if svm_uuid:
            rec["svm"] = {"name": svm_name, "uuid": svm_uuid}
        records.append(rec)
    return jsonify(collection(records, "/api/network/ethernet/interfaces"))


# Legacy alias used by older agent versions
@app.route("/api/network/ip/interfaces")
def get_ip_interfaces():
    return get_ethernet_interfaces()


# ══════════════════════════════════════════════════════════════════════════════
#  /api/network/fc/ports
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/network/fc/ports")
def get_fc_ports():
    records = []
    for node_name, node_uuid in [("node-01", NODE1_UUID), ("node-02", NODE2_UUID)]:
        for port_id in ("0a", "0b", "0c", "0d"):
            # NON-OK: port 0d on node-01 is in error state
            state = "offlined_by_system" if (node_name == "node-01" and port_id == "0d") else "online"
            records.append({
                "name":  port_id,
                "node":  {"name": node_name, "uuid": node_uuid},
                "state": state,
                "enabled": state != "error",
                "description": f"Fibre Channel Adapter {port_id}",
                "speed": {"configured": "8_gbit", "maximum": "16_gbit"},
                "physical_protocol": "fibre_channel",
                "supported_protocols": ["fcp"],
                "wwpn": FC_WWPNS[(node_name, port_id)][0],
                "wwnn": FC_WWPNS[(node_name, port_id)][1],
                "_links": {"self": {"href": f"/api/network/fc/ports/{node_name}/{port_id}"}},
            })
    return jsonify(collection(records, "/api/network/fc/ports"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/storage/shelves   (fans, temperatures, voltage, current)
# ══════════════════════════════════════════════════════════════════════════════
def _shelf(shelf_id: str, node_name: str, model: str = "DS224C"):
    fans = []
    for i in range(1, 5):
        # NON-OK: fan 2 on shelf "1" (node-01) has dangerously low RPM
        if shelf_id == "1" and node_name == "node-01" and i == 2:
            rpm   = int(rng(550, 0.05))
            state = "error"
        else:
            rpm   = rng_fan(3_200)
            state = "ok"
        fans.append({
            "id":       i,
            "location": ("front" if i <= 2 else "rear") + (" left" if i % 2 else " right"),
            "rpm":      rpm,
            "state":    state,
        })

    temp_sensors = []
    for i in range(1, 4):
        # NON-OK: sensor 3 on shelf "3" (node-02) – temperature above warning
        if shelf_id == "3" and node_name == "node-02" and i == 3:
            temp  = rng_temp(62.0)
            state = "error"
        else:
            temp  = rng_temp(28.0 + i * 2)
            state = "ok"
        temp_sensors.append({
            "id":          i,
            "location":    f"module {i}",
            "temperature": temp,
            "threshold": {
                "high": {"critical": 75, "warning": 58},
                "low":  {"critical":  0, "warning":  5},
            },
            "state":   state,
            "ambient": (i == 1),
        })

    voltage_sensors = []
    for i, (loc, nominal) in enumerate(
        [("12V Rail", 12.0), ("3.3V Rail", 3.3), ("5V Rail", 5.0)], start=1
    ):
        voltage_sensors.append({
            "id":       i,
            "location": loc,
            "voltage":  round(rng(nominal, 0.03), 3),
            "threshold": {
                "high": {"critical": nominal * 1.15, "warning": nominal * 1.10},
                "low":  {"critical": nominal * 0.85, "warning": nominal * 0.90},
            },
            "state": "ok",
        })

    current_sensors = []
    for i in range(1, 3):
        current_sensors.append({
            "id":       i,
            "location": f"PSU {i} input",
            "current":  int(rng(2.8, 0.05) * 1000),
            "threshold": {
                "high": {"critical": 10.0, "warning": 8.0},
                "low":  {"critical":  0.0, "warning": 0.1},
            },
            "state": "ok",
        })

    psus = []
    for i in range(1, 3):
        psus.append({
            "id":            i,
            "state":         "ok",
            "serial_number": f"PSU-SH{shelf_id}-{i:02d}",
            "model":         "X670-R6",
            "type":          "ac",
        })

    return {
        "id":            shelf_id,
        "serial_number": f"SH-{node_name.upper()}-{shelf_id}",
        "model":         model,
        "state":         "ok",
        "internal":      False,
        "disk_count":    24,
        "fans":              fans,
        "temperature_sensors": temp_sensors,
        "voltage_sensors":   voltage_sensors,
        "current_sensors":   current_sensors,
        "power_supply_units": psus,
        "module_status":     [{"id": "A", "status": "normal"}, {"id": "B", "status": "normal"}],
        "_links": {"self": {"href": f"/api/storage/shelves/{shelf_id}"}},
    }


@app.route("/api/storage/shelves")
def get_shelves():
    return jsonify(collection(
        [
            _shelf("1", "node-01"),
            _shelf("2", "node-01"),
            _shelf("3", "node-02"),    # ← shelf with hot temp sensor
            _shelf("4", "node-02"),
        ],
        "/api/storage/shelves",
    ))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/snapmirror/relationships
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/snapmirror/relationships")
def get_snapmirror():
    now = datetime.now(timezone.utc)
    records = [
        {   # Healthy SnapVault
            "uuid":    "smr00001-0000-0000-0000-000000000001",
            "state":   "snapmirrored",
            "healthy": True,
            "unhealthy_reason": [],
            "type":    "vault",
            "policy":  {"name": "XDPDefault", "type": "vault"},
            "source": {
                "path":   "svm_data01:vol_data01",
                "svm":    {"name": "svm_data01", "uuid": SVM1_UUID},
                "volume": {"name": "vol_data01"},
            },
            "destination": {
                "path":   "svm_backup:vol_snapvault_dest",
                "svm":    {"name": "svm_backup",  "uuid": SVM2_UUID},
                "volume": {"name": "vol_snapvault_dest"},
            },
            "lag_time": "PT8H32M4S",
            "transfer": {
                "state":    "success",
                "end_time": (now - timedelta(hours=8, minutes=32)).isoformat(timespec="seconds"),
            },
            "_links": {"self": {"href": "/api/snapmirror/relationships/smr00001-0000-0000-0000-000000000001"}},
        },
        {   # NON-OK: unhealthy async mirror, 2+ day lag
            "uuid":    "smr00002-0000-0000-0000-000000000002",
            "state":   "snapmirrored",
            "healthy": False,
            "unhealthy_reason": [
                {"code": "108090279", "message": "Transfer failed: network error after 3 retries"}
            ],
            "type":    "async_mirror",
            "policy":  {"name": "MirrorAllSnapshots", "type": "async_mirror"},
            "source": {
                "path":   "svm_data01:vol_data02",
                "svm":    {"name": "svm_data01", "uuid": SVM1_UUID},
                "volume": {"name": "vol_data02"},
            },
            "destination": {
                "path":   "svm_backup:vol_backup_dest",
                "svm":    {"name": "svm_backup",  "uuid": SVM2_UUID},
                "volume": {"name": "vol_backup_dest"},
            },
            "lag_time": "P2DT14H5M",
            "transfer": {
                "state":    "failed",
                "end_time": (now - timedelta(days=2, hours=14)).isoformat(timespec="seconds"),
            },
            "_links": {"self": {"href": "/api/snapmirror/relationships/smr00002-0000-0000-0000-000000000002"}},
        },
    ]
    return jsonify(collection(records, "/api/snapmirror/relationships"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/storage/qtrees
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/storage/qtrees")
def get_qtrees():
    records = [
        {
            "id": 0, "name": "",
            "volume": {"name": "vol_data01", "uuid": "vol-0002"},
            "svm":    {"name": "svm_data01", "uuid": SVM1_UUID},
            "security_style": "unix", "unix_permissions": 755,
            "path": "/vol/vol_data01",
            "_links": {"self": {"href": "/api/storage/qtrees/svm_data01/vol_data01/0"}},
        },
        {
            "id": 1, "name": "qtree_eng",
            "volume": {"name": "vol_data01", "uuid": "vol-0002"},
            "svm":    {"name": "svm_data01", "uuid": SVM1_UUID},
            "security_style": "unix", "unix_permissions": 755,
            "path": "/vol/vol_data01/qtree_eng",
            "_links": {"self": {"href": "/api/storage/qtrees/svm_data01/vol_data01/1"}},
        },
        {
            "id": 2, "name": "qtree_finance",
            "volume": {"name": "vol_data01", "uuid": "vol-0002"},
            "svm":    {"name": "svm_data01", "uuid": SVM1_UUID},
            "security_style": "ntfs", "unix_permissions": 0,
            "path": "/vol/vol_data01/qtree_finance",
            "_links": {"self": {"href": "/api/storage/qtrees/svm_data01/vol_data01/2"}},
        },
    ]
    return jsonify(collection(records, "/api/storage/qtrees"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/storage/quota/reports
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/storage/quota/reports")
def get_quota_reports():
    records = [
        {
            "svm":    {"name": "svm_data01", "uuid": SVM1_UUID},
            "volume": {"name": "vol_data01"},
            "qtree":  {"name": "qtree_eng"},
            "type":   "tree",
            "space": {
                "hard_limit":  int(rng(500 * GB)),
                "soft_limit":  int(rng(450 * GB)),
                "used": {
                    "total": int(rng(310 * GB)),
                    "hard_limit_percent": 62,
                    "soft_limit_percent": 69,
                },
            },
            "files": {
                "hard_limit":  500_000,
                "soft_limit":  450_000,
                "used": {
                    "total": int(rng(150_000)),
                    "hard_limit_percent": 30,
                    "soft_limit_percent": 33,
                },
            },
        },
        {   # Soft limit exceeded
            "svm":    {"name": "svm_data01", "uuid": SVM1_UUID},
            "volume": {"name": "vol_data01"},
            "qtree":  {"name": "qtree_finance"},
            "type":   "tree",
            "space": {
                "hard_limit":  int(rng(300 * GB)),
                "soft_limit":  int(rng(270 * GB)),
                "used": {
                    "total": int(rng(282 * GB)),   # ~94 % — soft limit exceeded
                    "hard_limit_percent": 94,
                    "soft_limit_percent": 104,     # ← over soft limit
                },
            },
            "files": {
                "hard_limit":  300_000,
                "soft_limit":  270_000,
                "used": {
                    "total": int(rng(200_000)),
                    "hard_limit_percent": 66,
                    "soft_limit_percent": 74,
                },
            },
        },
    ]
    return jsonify(collection(records, "/api/storage/quota/reports"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/cluster/licensing/licenses
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/cluster/licensing/licenses")
def get_licenses():
    return jsonify(collection(
        [
            {"name": "base",        "state": "compliant", "scope": "cluster"},
            {"name": "nfs",         "state": "compliant", "scope": "cluster"},
            {"name": "cifs",        "state": "compliant", "scope": "cluster"},
            {"name": "iscsi",       "state": "compliant", "scope": "cluster"},
            {"name": "fcp",         "state": "compliant", "scope": "cluster"},
            {"name": "snapmirror",  "state": "compliant", "scope": "cluster"},
            {"name": "snapvault",   "state": "compliant", "scope": "cluster"},
            {"name": "flexclone",   "state": "compliant", "scope": "cluster"},
            {"name": "dedup",       "state": "compliant", "scope": "cluster"},
            {"name": "compression", "state": "compliant", "scope": "cluster"},
        ],
        "/api/cluster/licensing/licenses",
    ))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/cluster/counter/tables/{table}/rows
# ══════════════════════════════════════════════════════════════════════════════
def _counter_row(row_id: str, counters: dict) -> dict:
    return {
        "id":       row_id,
        "counters": [{"name": k, "value": v} for k, v in counters.items()],
        "_links":   {"self": {"href": f"/api/cluster/counter/tables/volume/rows/{row_id}"}},
    }


def _volume_counters(row_id: str) -> dict:
    return _counter_row(row_id, {
        "bytes_read":           rng_counter(10_000_000_000, 8_000_000),
        "bytes_written":        rng_counter(6_000_000_000,  4_000_000),
        "total_read_ops":       rng_counter(1_000_000,      800),
        "total_write_ops":      rng_counter(600_000,        400),
        "read_latency":         rng_latency(500),
        "write_latency":        rng_latency(700),
        "nfs.read_ops":         rng_counter(400_000,        300),
        "nfs.write_ops":        rng_counter(200_000,        150),
        "nfs.read_data":        rng_counter(4_000_000_000,  3_000_000),
        "nfs.write_data":       rng_counter(2_000_000_000,  1_500_000),
        "nfs.read_latency":     rng_latency(400),
        "nfs.write_latency":    rng_latency(600),
        "cifs.read_ops":        rng_counter(100_000,        80),
        "cifs.write_ops":       rng_counter(60_000,         40),
        "cifs.read_data":       rng_counter(1_000_000_000,  700_000),
        "cifs.write_data":      rng_counter(600_000_000,    400_000),
        "cifs.read_latency":    rng_latency(800),
        "cifs.write_latency":   rng_latency(900),
        "iscsi.read_ops":       rng_counter(200_000,        150),
        "iscsi.write_ops":      rng_counter(160_000,        120),
        "iscsi.read_data":      rng_counter(2_000_000_000,  1_500_000),
        "iscsi.write_data":     rng_counter(1_600_000_000,  1_200_000),
        "iscsi.read_latency":   rng_latency(300),
        "iscsi.write_latency":  rng_latency(400),
        "fcp.read_ops":         rng_counter(100_000,        80),
        "fcp.write_ops":        rng_counter(80_000,         60),
        "fcp.read_data":        rng_counter(1_000_000_000,  800_000),
        "fcp.write_data":       rng_counter(800_000_000,    600_000),
        "fcp.read_latency":     rng_latency(200),
        "fcp.write_latency":    rng_latency(250),
    })


def _fcp_port_counters(node_name: str, port_name: str, wwpn: str) -> dict:
    row_id = f"port.{port_name}"
    return {
        "id":       row_id,
        "name":     row_id,
        "port_wwpn": wwpn,
        "svm_name": "none",
        "table":    "fcp_lif:port",
        "properties": [
            {"name": "svm.name",   "value": "svm_data01"},
            {"name": "name",       "value": f"{node_name}.{port_name}"},
            {"name": "port.wwpn",  "value": wwpn},
        ],
        "counters": [
            {"name": "read_ops",               "value": rng_counter(100_000, 80)},
            {"name": "write_ops",              "value": rng_counter(80_000,  60)},
            {"name": "total_ops",              "value": rng_counter(180_000, 140)},
            {"name": "read_data",              "value": rng_counter(1_000_000_000, 800_000)},
            {"name": "write_data",             "value": rng_counter(800_000_000,  600_000)},
            {"name": "average_read_latency",   "value": rng_latency(200)},
            {"name": "average_write_latency",  "value": rng_latency(250)},
        ],
        "_links": {"self": {"href": f"/api/cluster/counter/tables/fcp_lif:port/rows/{row_id}"}},
    }


@app.route("/api/cluster/counter/tables/<path:table>/rows")
def get_counter_table_rows(table: str):
    if table == "volume":
        vol_ids = [
            "*:svm_data01:vol_root_node01:vol-0001",
            "*:svm_data01:vol_data01:vol-0002",
            "*:svm_data01:vol_data02:vol-0003",
            "*:svm_data01:vol_nfs_home:vol-0004",
            "*:svm_data01:vol_cifs_share:vol-0005",
            "*:svm_data01:vol_oracle_data:vol-0006",
            "*:svm_data01:vol_oracle_redo:vol-0007",
            "*:svm_backup:vol_backup_dest:vol-0008",
            "*:svm_backup:vol_snapvault_dest:vol-0009",
        ]
        id_filter = request.args.get("id", "")
        if id_filter:
            vol_ids = [v for v in vol_ids if id_filter.strip("*") in v]
        records = [_volume_counters(vid) for vid in vol_ids]
        return jsonify(collection(records, f"/api/cluster/counter/tables/{table}/rows"))

    if table == "fcp_lif:port":
        records = []
        wwpns = [
            ("node-01", "0a", "20:aa:bb:cc:dd:ee:ff:01"),
            ("node-01", "0b", "20:aa:bb:cc:dd:ee:ff:02"),
            ("node-01", "0c", "20:aa:bb:cc:dd:ee:ff:03"),
            ("node-01", "0d", "20:aa:bb:cc:dd:ee:ff:04"),
            ("node-02", "0a", "20:aa:bb:cc:dd:ee:ff:05"),
            ("node-02", "0b", "20:aa:bb:cc:dd:ee:ff:06"),
            ("node-02", "0c", "20:aa:bb:cc:dd:ee:ff:07"),
            ("node-02", "0d", "20:aa:bb:cc:dd:ee:ff:08"),
        ]
        for node_name, port_name, wwpn in wwpns:
            records.append(_fcp_port_counters(node_name, port_name, wwpn))
        return jsonify(collection(records, f"/api/cluster/counter/tables/{table}/rows"))

    if table == "lif":
        lif_seed = [
            ("node-01", "data_lif_01",  "iface-0001"),
            ("node-01", "data_lif_02",  "iface-0002"),
            ("node-02", "nfs_lif_01",   "iface-0003"),
            ("node-02", "nfs_lif_02",   "iface-0004"),
            ("node-01", "iscsi_lif_01", "iface-0005"),
            ("node-01", "cluster_mgmt", "iface-0006"),
        ]
        records = []
        for node_name, lif_name, uid in lif_seed:
            row_id = f"{node_name}:{lif_name}:{uid}"
            records.append({
                "id": row_id,
                "properties": [{"name": "svm.name", "value": "svm_data01"}],
                "counters": [
                    {"name": "received_data",    "value": rng_counter(100_000_000_000, 50_000_000)},
                    {"name": "sent_data",        "value": rng_counter(60_000_000_000,  30_000_000)},
                    {"name": "received_errors",  "value": rng_counter(10,  0.001)},
                    {"name": "sent_errors",      "value": rng_counter(5,   0.0005)},
                    {"name": "received_packets", "value": rng_counter(80_000_000, 40_000)},
                    {"name": "sent_packets",     "value": rng_counter(50_000_000, 25_000)},
                ],
                "_links": {"self": {"href": f"/api/cluster/counter/tables/lif/rows/{row_id}"}},
            })
        return jsonify(collection(records, f"/api/cluster/counter/tables/{table}/rows"))

    if table == "fcp_lif":
        records = []
        for node_name, port_id in [("node-01","0a"),("node-01","0b"),("node-01","0c"),("node-02","0a"),("node-02","0b"),("node-02","0c"),("node-02","0d")]:
            row_id = f"{node_name}:{port_id}:fcp"
            records.append({"id": row_id, "properties": [{"name": "svm.name", "value": "svm_data01"}], "counters": [{"name": "average_read_latency", "value": rng_latency(200)}, {"name": "average_write_latency", "value": rng_latency(250)}, {"name": "read_data", "value": rng_counter(1_000_000_000, 800_000)}, {"name": "write_data", "value": rng_counter(800_000_000, 600_000)}, {"name": "read_ops", "value": rng_counter(100_000, 80)}, {"name": "write_ops", "value": rng_counter(80_000, 60)}], "_links": {"self": {"href": f"/api/cluster/counter/tables/fcp_lif/rows/{row_id}"}}})
        return jsonify(collection(records, f"/api/cluster/counter/tables/{table}/rows"))

    if table == "svm_cifs":
        return jsonify(collection([{"id": "svm_data01:cifs:001", "properties": [{"name": "svm.name", "value": "svm_data01"}], "counters": [{"name": "average_read_latency", "value": rng_latency(800)}, {"name": "average_write_latency", "value": rng_latency(900)}, {"name": "total_read_ops", "value": rng_counter(100_000, 80)}, {"name": "total_write_ops", "value": rng_counter(60_000, 40)}]}], f"/api/cluster/counter/tables/{table}/rows"))

    if table == "iscsi_lif":
        return jsonify(collection([{"id": "node-01:iscsi_lif_01:iscsi", "properties": [{"name": "svm.name", "value": "svm_data01"}], "counters": [{"name": "average_read_latency", "value": rng_latency(300)}, {"name": "average_write_latency", "value": rng_latency(400)}, {"name": "read_data", "value": rng_counter(2_000_000_000, 1_500_000)}, {"name": "write_data", "value": rng_counter(1_600_000_000, 1_200_000)}, {"name": "iscsi_read_ops", "value": rng_counter(200_000, 150)}, {"name": "iscsi_write_ops", "value": rng_counter(160_000, 120)}]}], f"/api/cluster/counter/tables/{table}/rows"))

    if table == "svm_nfs_v3":
        return jsonify(collection([{"id": "svm_data01:nfs_v3:001", "properties": [{"name": "svm.name", "value": "svm_data01"}], "counters": [{"name": "read_throughput", "value": rng_counter(2_000_000_000, 1_500_000)}, {"name": "write_throughput", "value": rng_counter(1_000_000_000, 750_000)}, {"name": "read_ops", "value": rng_counter(400_000, 300)}, {"name": "write_ops", "value": rng_counter(200_000, 150)}, {"name": "ops", "value": rng_counter(600_000, 450)}]}], f"/api/cluster/counter/tables/{table}/rows"))

    if table in ("svm_nfs_v4", "svm_nfs_v41"):
        return jsonify(collection([{"id": f"svm_data01:{table}:001", "properties": [{"name": "svm.name", "value": "svm_data01"}], "counters": [{"name": "total.read_throughput", "value": rng_counter(500_000_000, 400_000)}, {"name": "total.write_throughput", "value": rng_counter(300_000_000, 200_000)}, {"name": "ops", "value": rng_counter(50_000, 40)}]}], f"/api/cluster/counter/tables/{table}/rows"))

    logger.warning("UNIMPLEMENTED counter table: %s", table)
    return jsonify(collection([], f"/api/cluster/counter/tables/{table}/rows"))


@app.route("/api/cluster/counter/tables")
def get_counter_tables():
    return jsonify(collection(
        [{"name": "volume"}, {"name": "svm"}, {"name": "node"}, {"name": "fcp_lif:port"}],
        "/api/cluster/counter/tables",
    ))



@app.route("/api/svm/peers")
def get_svm_peers():
    return jsonify(collection([], "/api/svm/peers"))


@app.route("/api/cluster/peers")
def get_cluster_peers():
    return jsonify(collection([], "/api/cluster/peers"))


@app.route("/api/protocols/nfs/connected-clients")
def get_nfs_clients():
    return jsonify(collection([], "/api/protocols/nfs/connected-clients"))


@app.route("/api/protocols/cifs/sessions")
def get_cifs_sessions():
    return jsonify(collection([], "/api/protocols/cifs/sessions"))


@app.route("/api/protocols/san/fcp/services")
def get_fcp_services():
    return jsonify(collection(
        [{"svm": {"name": "svm_data01", "uuid": SVM1_UUID}, "enabled": True, "status": {"state": "online"}}],
        "/api/protocols/san/fcp/services",
    ))


@app.route("/api/network/fc/interfaces")
def get_fc_interfaces():
    records = []
    for node_name, node_uuid in [("node-01", NODE1_UUID), ("node-02", NODE2_UUID)]:
        for port_id in ("0a", "0b", "0c", "0d"):
            is_bad = (node_name == "node-01" and port_id == "0d")
            records.append({
                "uuid":    f"fclif-{node_name}-{port_id}",
                "name":    f"{node_name}.{port_id}",
                "state":   "offline" if is_bad else "online",
                "enabled": not is_bad,
                "svm":     {"name": "svm_data01", "uuid": SVM1_UUID},
                "location": {
                    "node":      {"name": node_name, "uuid": node_uuid},
                    "port":      {"name": port_id, "node": {"name": node_name}},
                    "home_node": {"name": node_name, "uuid": node_uuid},
                    "home_port": {"name": port_id, "node": {"name": node_name}},
                    "is_home":   True,
                },
                "wwpn": FC_WWPNS[(node_name, port_id)][0],
                "wwnn": FC_WWPNS[(node_name, port_id)][1],
                "_links": {"self": {"href": f"/api/network/fc/interfaces/fclif-{node_name}-{port_id}"}},
            })
    return jsonify(collection(records, "/api/network/fc/interfaces"))


@app.route("/api/private/support/alerts")
def get_alerts():
    return jsonify(collection([
        {"name": "DiskFailedAlert", "message": "Disk 1.0.13 on node-01 has failed.", "severity": "critical", "state": "active", "acknowledge": False, "node": {"name": "node-01"}, "time": "2026-03-19T06:00:00+00:00"},
        {"name": "AggregateLowSpaceAlert", "message": "Aggregate aggr1_node01 is 87% full.", "severity": "warning", "state": "active", "acknowledge": False, "node": {"name": "node-01"}, "time": "2026-03-19T08:00:00+00:00"},
        {"name": "NetworkPortDownAlert", "message": "Port e0d on node-02 is down.", "severity": "warning", "state": "active", "acknowledge": False, "node": {"name": "node-02"}, "time": "2026-03-19T09:00:00+00:00"},
        {"name": "SnapMirrorTransferFailedAlert", "message": "SnapMirror for vol_data02 failed for 2+ days.", "severity": "critical", "state": "active", "acknowledge": False, "node": {"name": "node-01"}, "time": "2026-03-17T06:00:00+00:00"},
    ], "/api/private/support/alerts"))


# ══════════════════════════════════════════════════════════════════════════════
#  /api/cluster/sensors
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/cluster/sensors")
def get_cluster_sensors():
    sensor_type_filter = request.args.get("type", "")
    allowed_types = [t for t in sensor_type_filter.split("|")] if sensor_type_filter else []

    sensors = []
    sensor_id = 1

    def add_sensor(name, node, stype, value, units, warn_low, warn_high, crit_low, crit_high, state="normal"):
        nonlocal sensor_id
        if allowed_types and stype not in allowed_types:
            return
        sensors.append({
            "name":                    name,
            "node":                    {"name": node},
            "type":                    stype,
            "value":                   int(rng(value, 0.03)),
            "value_units":             units,
            "warning_low_threshold":   warn_low,
            "warning_high_threshold":  warn_high,
            "critical_low_threshold":  crit_low,
            "critical_high_threshold": crit_high,
            "threshold_state":         state,
            "discrete_state":          "normal",
            "discrete_value":          "true",
            "_links": {"self": {"href": f"/api/cluster/sensors/{sensor_id}"}},
        })
        sensor_id += 1

    for node in ("node-01", "node-02"):
        # Thermal sensors
        add_sensor("CPU Temp Margin",   node, "thermal", rng_temp(55),  "mC",  5000,  85000, 0,     95000)
        add_sensor("Inlet Temp",        node, "thermal", rng_temp(28),  "mC",  5000,  40000, 0,     45000)
        add_sensor("Outlet Temp",       node, "thermal", rng_temp(38),  "mC",  5000,  55000, 0,     60000)
        add_sensor("PCH Temp",          node, "thermal", rng_temp(45),  "mC",  5000,  80000, 0,     90000)
        # Fan sensors
        add_sensor("Fan1 Front",        node, "fan",     rng_fan(3200), "rpm", 500,   0,     300,   0)
        add_sensor("Fan2 Front",        node, "fan",     rng_fan(3100), "rpm", 500,   0,     300,   0)
        add_sensor("Fan1 Rear",         node, "fan",     rng_fan(3300), "rpm", 500,   0,     300,   0)
        add_sensor("Fan2 Rear",         node, "fan",     rng_fan(3250), "rpm", 500,   0,     300,   0)
        # Voltage sensors
        add_sensor("12V",               node, "voltage", int(rng(12000, 0.02)), "mV", 10800, 13200, 10200, 13800)
        add_sensor("5V",                node, "voltage", int(rng(5000,  0.02)), "mV", 4500,  5500,  4250,  5750)
        add_sensor("3.3V",              node, "voltage", int(rng(3300,  0.02)), "mV", 2970,  3630,  2805,  3795)
        add_sensor("1.8V",              node, "voltage", int(rng(1800,  0.02)), "mV", 1620,  1980,  1530,  2070)
        # Current sensors
        add_sensor("PSU1 Curr",         node, "current", int(rng(8000,  0.05)), "mA", 0,     15000, 0,     18000)
        add_sensor("PSU2 Curr",         node, "current", int(rng(7500,  0.05)), "mA", 0,     15000, 0,     18000)

    # NON-OK: one failed fan sensor on node-01
    if not allowed_types or "fan" in allowed_types:
        sensors.append({
            "name":                    "Fan3 Front",
            "node":                    {"name": "node-01"},
            "type":                    "fan",
            "value":                   int(rng(450, 0.05)),
            "value_units":             "rpm",
            "warning_low_threshold":   500,
            "warning_high_threshold":  0,
            "critical_low_threshold":  300,
            "critical_high_threshold": 0,
            "threshold_state":         "warn_low",
            "discrete_state":          "warn_low",
            "discrete_value":          "true",
            "_links": {"self": {"href": f"/api/cluster/sensors/{sensor_id}"}},
        })

    return jsonify(collection(sensors, "/api/cluster/sensors"))


# ══════════════════════════════════════════════════════════════════════════════
#  Catch-all — log + structured 404 for any unimplemented endpoint
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def catch_all(path: str):
    logger.warning(
        "UNIMPLEMENTED  %s /%s  args=%s  body=%s",
        request.method,
        path,
        dict(request.args),
        request.get_data(as_text=True)[:200] or "<empty>",
    )
    return (
        jsonify({
            "error": {
                "code":    "4",
                "message": f"API endpoint not found: /{path}",
                "target":  f"/{path}",
            }
        }),
        404,
    )


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Dev mode — plain HTTP on 8080
    app.run(host="0.0.0.0", port=8080, debug=True)
