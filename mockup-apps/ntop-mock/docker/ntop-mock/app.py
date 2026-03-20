"""
ntopng REST API v2 — Mock Server
For testing Checkmk CEE ntop integration.

Auth flow:
  1. GET  /lua/rest/version.lua                     Basic Auth → API version
  2. POST /lua/rest/v2/create/ntopng/session.lua    Basic Auth → session cookie
  3. POST /lua/rest/v2/get/...                      Cookie: session=<token> → data

Configure in Checkmk Global Settings > ntopng connection:
  protocol      : http
  hostaddress   : 192.168.128.10
  port          : 3000
  admin_username: admin
  admin_password: admin
"""

import secrets
import time
import threading
import random
from functools import wraps
from flask import Flask, jsonify, request, make_response
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = Flask(__name__)

# ── Credentials ───────────────────────────────────────────────────────────────
ADMIN_USER = "admin"
ADMIN_PASS = "admin"

# ── Active sessions: {token: {"user": str, "created": float}} ─────────────────
SESSIONS: dict = {}
SESSION_TTL = 3600  # 1 hour


# ── Response helpers ─────────────────────────────────────────────────────────

def rsp(data):
    return jsonify({"rc": 0, "rc_str": "OK", "rsp": data})

def err(msg, code=401):
    return jsonify({"rc": -1, "rc_str": msg, "rsp": None}), code

def log_req():
    app.logger.info("%-6s %s", request.method, request.path)


# ── Auth decorators ───────────────────────────────────────────────────────────

def require_basic_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASS:
            app.logger.warning("Basic auth failed for %r", getattr(auth, "username", None))
            return err("Unauthorized")
        return f(*args, **kwargs)
    return decorated

def require_session(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("session")
        if not token:
            app.logger.warning("Missing session cookie")
            return err("Session expired or not found", code=403)
        if token not in SESSIONS:
            # Checkmk caches session tokens on disk; after a mock restart the token
            # is gone from our in-memory store but still valid in Checkmk's cookie file.
            # Auto-register it so Checkmk doesn't have to re-authenticate.
            app.logger.info("Auto-registering cached session %s", token)
            SESSIONS[token] = {"user": "admin", "created": time.time()}
        # Prune expired sessions
        if time.time() - SESSIONS[token]["created"] > SESSION_TTL:
            SESSIONS.pop(token, None)
            return err("Session expired", code=403)
        return f(*args, **kwargs)
    return decorated


# ── Mock data ─────────────────────────────────────────────────────────────────

INTERFACES = [
    {
        "ifid": 1, "ifname": "eth0", "name": "eth0",
        "speed": 1000, "mtu": 1500,
        "bytes_sent": 5_242_880_000, "bytes_rcvd": 12_884_901_888,
        "pkts_sent": 4_200_000, "pkts_rcvd": 9_800_000,
        "drops": 0, "num_hosts": 24, "num_local_hosts": 18,
        "uptime": 86400, "has_seen_vlan": False,
    },
    {
        "ifid": 2, "ifname": "eth1", "name": "eth1",
        "speed": 100, "mtu": 1500,
        "bytes_sent": 524_288_000, "bytes_rcvd": 1_073_741_824,
        "pkts_sent": 420_000, "pkts_rcvd": 980_000,
        "drops": 12, "num_hosts": 6, "num_local_hosts": 5,
        "uptime": 86400, "has_seen_vlan": True,
    },
]

HOSTS = [
    {"ip": "192.168.1.10", "vlan": "0", "ifid": "1", "name": "web-server",     "is_local": True},
    {"ip": "192.168.1.20", "vlan": "0", "ifid": "1", "name": "db-server",      "is_local": True},
    {"ip": "192.168.1.30", "vlan": "0", "ifid": "1", "name": "workstation-01", "is_local": True},
    {"ip": "192.168.1.40", "vlan": "0", "ifid": "1", "name": "workstation-02", "is_local": True},
    {"ip": "8.8.8.8",      "vlan": "0", "ifid": "1", "name": "dns.google",     "is_local": False},
]

HOST_DATA = {
    "192.168.1.10@0": {
        "ip": "192.168.1.10", "vlan": 0, "name": "web-server",
        "bytes_sent": 2_147_483_648, "bytes_rcvd": 536_870_912,
        "active_flows_as_client": 12, "active_flows_as_server": 45,
        "num_alerts": 0, "score": 0,
        "os": {"id": 0, "name": "Linux"},
        "country": "DE",
        "latitude": 48.137, "longitude": 11.575,
    },
    "192.168.1.20@0": {
        "ip": "192.168.1.20", "vlan": 0, "name": "db-server",
        "bytes_sent": 1_073_741_824, "bytes_rcvd": 268_435_456,
        "active_flows_as_client": 3, "active_flows_as_server": 28,
        "num_alerts": 1, "score": 10,
        "os": {"id": 0, "name": "Linux"},
        "country": "DE",
        "latitude": 48.137, "longitude": 11.575,
    },
    "192.168.1.30@0": {
        "ip": "192.168.1.30", "vlan": 0, "name": "workstation-01",
        "bytes_sent": 524_288_000, "bytes_rcvd": 1_073_741_824,
        "active_flows_as_client": 8, "active_flows_as_server": 0,
        "num_alerts": 0, "score": 0,
        "os": {"id": 1, "name": "Windows"},
        "country": "DE",
        "latitude": 48.137, "longitude": 11.575,
    },
}

_LOCAL = True
_REMOTE = False

# Each flow has "local_client" and "local_server" booleans for flowhosts_type filtering
ACTIVE_FLOWS = [
    # ── TCP / HTTP (local → local) ────────────────────────────────────────────
    {"key": "1",  "hash_id": "1",  "vlan": "0",
     "client": {"ip": "192.168.1.30", "port": 52341, "name": "workstation-01"},
     "server": {"ip": "192.168.1.10", "port": 80,    "name": "web-server"},
     "protocol": {"l4": "TCP",  "l7": "HTTP"},  "l4_proto_id": 6,  "l7_cat": "Web",
     "thpt": {"bps": 2_000_000, "pps": 200},
     "bytes": 1_048_576, "pkts": 1024, "duration": 30,  "score": 0,
     "breakdown": {"cli2srv": 20, "srv2cli": 80}, "local_client": True,  "local_server": True},
    # ── TCP / HTTPS (local → local) ───────────────────────────────────────────
    {"key": "2",  "hash_id": "2",  "vlan": "0",
     "client": {"ip": "192.168.1.40", "port": 61000, "name": "workstation-02"},
     "server": {"ip": "192.168.1.10", "port": 443,   "name": "web-server"},
     "protocol": {"l4": "TCP",  "l7": "HTTPS"}, "l4_proto_id": 6,  "l7_cat": "Web",
     "thpt": {"bps": 5_000_000, "pps": 450},
     "bytes": 3_145_728, "pkts": 2800, "duration": 62,  "score": 0,
     "breakdown": {"cli2srv": 30, "srv2cli": 70}, "local_client": True,  "local_server": True},
    # ── TCP / MySQL (local → local) ───────────────────────────────────────────
    {"key": "3",  "hash_id": "3",  "vlan": "0",
     "client": {"ip": "192.168.1.20", "port": 33060, "name": "db-server"},
     "server": {"ip": "192.168.1.10", "port": 3306,  "name": "web-server"},
     "protocol": {"l4": "TCP",  "l7": "MySQL"}, "l4_proto_id": 6,  "l7_cat": "Database",
     "thpt": {"bps": 500_000,   "pps": 50},
     "bytes": 262_144,  "pkts": 256,  "duration": 120, "score": 0,
     "breakdown": {"cli2srv": 60, "srv2cli": 40}, "local_client": True,  "local_server": True},
    # ── TCP / SSH (local → local) ─────────────────────────────────────────────
    {"key": "4",  "hash_id": "4",  "vlan": "0",
     "client": {"ip": "192.168.1.30", "port": 45001, "name": "workstation-01"},
     "server": {"ip": "192.168.1.20", "port": 22,    "name": "db-server"},
     "protocol": {"l4": "TCP",  "l7": "SSH"},   "l4_proto_id": 6,  "l7_cat": "Network",
     "thpt": {"bps": 52_428,    "pps": 10},
     "bytes": 65_536,   "pkts": 120,  "duration": 300, "score": 0,
     "breakdown": {"cli2srv": 50, "srv2cli": 50}, "local_client": True,  "local_server": True},
    # ── UDP / DNS (local → remote) ────────────────────────────────────────────
    {"key": "5",  "hash_id": "5",  "vlan": "0",
     "client": {"ip": "192.168.1.30", "port": 54321, "name": "workstation-01"},
     "server": {"ip": "8.8.8.8",     "port": 53,    "name": "dns.google"},
     "protocol": {"l4": "UDP",  "l7": "DNS"},   "l4_proto_id": 17, "l7_cat": "Network",
     "thpt": {"bps": 1_024,     "pps": 2},
     "bytes": 512,      "pkts": 4,    "duration": 1,   "score": 0,
     "breakdown": {"cli2srv": 70, "srv2cli": 30}, "local_client": True,  "local_server": False},
    # ── UDP / DNS (local → remote) ────────────────────────────────────────────
    {"key": "6",  "hash_id": "6",  "vlan": "0",
     "client": {"ip": "192.168.1.40", "port": 43210, "name": "workstation-02"},
     "server": {"ip": "8.8.8.8",     "port": 53,    "name": "dns.google"},
     "protocol": {"l4": "UDP",  "l7": "DNS"},   "l4_proto_id": 17, "l7_cat": "Network",
     "thpt": {"bps": 2_048,     "pps": 4},
     "bytes": 1_024,    "pkts": 8,    "duration": 2,   "score": 0,
     "breakdown": {"cli2srv": 65, "srv2cli": 35}, "local_client": True,  "local_server": False},
    # ── TCP / HTTPS (local → remote) ─────────────────────────────────────────
    {"key": "7",  "hash_id": "7",  "vlan": "0",
     "client": {"ip": "192.168.1.30", "port": 60001, "name": "workstation-01"},
     "server": {"ip": "1.1.1.1",     "port": 443,   "name": "one.one.one.one"},
     "protocol": {"l4": "TCP",  "l7": "HTTPS"}, "l4_proto_id": 6,  "l7_cat": "Web",
     "thpt": {"bps": 1_500_000, "pps": 150},
     "bytes": 786_432,  "pkts": 800,  "duration": 45,  "score": 0,
     "breakdown": {"cli2srv": 25, "srv2cli": 75}, "local_client": True,  "local_server": False},
    # ── TCP / HTTP (local → remote) ───────────────────────────────────────────
    {"key": "8",  "hash_id": "8",  "vlan": "0",
     "client": {"ip": "192.168.1.40", "port": 60010, "name": "workstation-02"},
     "server": {"ip": "93.184.216.34","port": 80,   "name": "example.com"},
     "protocol": {"l4": "TCP",  "l7": "HTTP"},  "l4_proto_id": 6,  "l7_cat": "Web",
     "thpt": {"bps": 800_000,   "pps": 90},
     "bytes": 409_600,  "pkts": 420,  "duration": 20,  "score": 0,
     "breakdown": {"cli2srv": 35, "srv2cli": 65}, "local_client": True,  "local_server": False},
    # ── UDP / NTP (local → remote) ────────────────────────────────────────────
    {"key": "9",  "hash_id": "9",  "vlan": "0",
     "client": {"ip": "192.168.1.10", "port": 34567, "name": "web-server"},
     "server": {"ip": "216.239.35.0", "port": 123,  "name": "time.google.com"},
     "protocol": {"l4": "UDP",  "l7": "NTP"},   "l4_proto_id": 17, "l7_cat": "Network",
     "thpt": {"bps": 512,       "pps": 1},
     "bytes": 256,      "pkts": 2,    "duration": 1,   "score": 0,
     "breakdown": {"cli2srv": 50, "srv2cli": 50}, "local_client": True,  "local_server": False},
    # ── TCP / SMTP (local → remote) ───────────────────────────────────────────
    {"key": "10", "hash_id": "10", "vlan": "0",
     "client": {"ip": "192.168.1.10", "port": 43000, "name": "web-server"},
     "server": {"ip": "74.125.24.27", "port": 587,  "name": "smtp.gmail.com"},
     "protocol": {"l4": "TCP",  "l7": "SMTP"},  "l4_proto_id": 6,  "l7_cat": "Email",
     "thpt": {"bps": 256_000,   "pps": 30},
     "bytes": 131_072,  "pkts": 160,  "duration": 10,  "score": 0,
     "breakdown": {"cli2srv": 80, "srv2cli": 20}, "local_client": True,  "local_server": False},
    # ── ICMP (local → remote) ─────────────────────────────────────────────────
    {"key": "11", "hash_id": "11", "vlan": "0",
     "client": {"ip": "192.168.1.30", "port": 0,    "name": "workstation-01"},
     "server": {"ip": "8.8.8.8",     "port": 0,    "name": "dns.google"},
     "protocol": {"l4": "ICMP", "l7": "ICMP"},  "l4_proto_id": 1,  "l7_cat": "Network",
     "thpt": {"bps": 8_192,     "pps": 1},
     "bytes": 4_096,    "pkts": 50,   "duration": 50,  "score": 0,
     "breakdown": {"cli2srv": 50, "srv2cli": 50}, "local_client": True,  "local_server": False},
    # ── TCP / BitTorrent (local → remote) ALERTED ────────────────────────────
    {"key": "12", "hash_id": "12", "vlan": "0",
     "client": {"ip": "192.168.1.40", "port": 51413, "name": "workstation-02"},
     "server": {"ip": "45.33.32.156", "port": 6881, "name": "bt-peer-1"},
     "protocol": {"l4": "TCP",  "l7": "BitTorrent"}, "l4_proto_id": 6, "l7_cat": "Unspecified",
     "thpt": {"bps": 3_000_000, "pps": 300},
     "bytes": 5_242_880, "pkts": 5000, "duration": 180, "score": 50,
     "breakdown": {"cli2srv": 45, "srv2cli": 55}, "local_client": True,  "local_server": False},
    # ── UDP / BitTorrent (local → remote) ALERTED ────────────────────────────
    {"key": "13", "hash_id": "13", "vlan": "0",
     "client": {"ip": "192.168.1.30", "port": 51414, "name": "workstation-01"},
     "server": {"ip": "192.0.2.100",  "port": 6882, "name": "bt-peer-2"},
     "protocol": {"l4": "UDP",  "l7": "BitTorrent"}, "l4_proto_id": 17, "l7_cat": "Unspecified",
     "thpt": {"bps": 1_500_000, "pps": 200},
     "bytes": 2_097_152, "pkts": 2200, "duration": 90,  "score": 40,
     "breakdown": {"cli2srv": 55, "srv2cli": 45}, "local_client": True,  "local_server": False},
    # ── TCP / HTTP from remote (remote → local) ───────────────────────────────
    {"key": "14", "hash_id": "14", "vlan": "0",
     "client": {"ip": "203.0.113.55", "port": 44444, "name": "remote-client"},
     "server": {"ip": "192.168.1.10", "port": 80,   "name": "web-server"},
     "protocol": {"l4": "TCP",  "l7": "HTTP"},  "l4_proto_id": 6,  "l7_cat": "Web",
     "thpt": {"bps": 400_000,   "pps": 45},
     "bytes": 204_800,  "pkts": 210,  "duration": 15,  "score": 0,
     "breakdown": {"cli2srv": 40, "srv2cli": 60}, "local_client": False, "local_server": True},
    # ── TCP / HTTPS from remote (remote → local) ──────────────────────────────
    {"key": "15", "hash_id": "15", "vlan": "0",
     "client": {"ip": "198.51.100.10","port": 55000, "name": "remote-host-2"},
     "server": {"ip": "192.168.1.10", "port": 443,  "name": "web-server"},
     "protocol": {"l4": "TCP",  "l7": "HTTPS"}, "l4_proto_id": 6,  "l7_cat": "Web",
     "thpt": {"bps": 2_500_000, "pps": 220},
     "bytes": 1_572_864, "pkts": 1500, "duration": 55,  "score": 0,
     "breakdown": {"cli2srv": 30, "srv2cli": 70}, "local_client": False, "local_server": True},
    # ── TCP / SSH from remote (remote → local) ALERTED ───────────────────────
    {"key": "16", "hash_id": "16", "vlan": "0",
     "client": {"ip": "203.0.113.99", "port": 58000, "name": "suspicious-host"},
     "server": {"ip": "192.168.1.20", "port": 22,   "name": "db-server"},
     "protocol": {"l4": "TCP",  "l7": "SSH"},   "l4_proto_id": 6,  "l7_cat": "Network",
     "thpt": {"bps": 128_000,   "pps": 20},
     "bytes": 32_768,   "pkts": 80,   "duration": 600, "score": 30,
     "breakdown": {"cli2srv": 60, "srv2cli": 40}, "local_client": False, "local_server": True},
    # ── UDP / DNS (local → local) ─────────────────────────────────────────────
    {"key": "17", "hash_id": "17", "vlan": "0",
     "client": {"ip": "192.168.1.20", "port": 53200, "name": "db-server"},
     "server": {"ip": "192.168.1.10", "port": 53,   "name": "web-server"},
     "protocol": {"l4": "UDP",  "l7": "DNS"},   "l4_proto_id": 17, "l7_cat": "Network",
     "thpt": {"bps": 4_096,     "pps": 5},
     "bytes": 2_048,    "pkts": 20,   "duration": 3,   "score": 0,
     "breakdown": {"cli2srv": 60, "srv2cli": 40}, "local_client": True,  "local_server": True},
    # ── TCP / HTTPS (local → local) ───────────────────────────────────────────
    {"key": "18", "hash_id": "18", "vlan": "0",
     "client": {"ip": "192.168.1.30", "port": 62000, "name": "workstation-01"},
     "server": {"ip": "192.168.1.20", "port": 8443,  "name": "db-server"},
     "protocol": {"l4": "TCP",  "l7": "HTTPS"}, "l4_proto_id": 6,  "l7_cat": "Web",
     "thpt": {"bps": 300_000,   "pps": 35},
     "bytes": 163_840,  "pkts": 180,  "duration": 40,  "score": 0,
     "breakdown": {"cli2srv": 45, "srv2cli": 55}, "local_client": True,  "local_server": True},
    # ── TCP / SSH (local → remote) ────────────────────────────────────────────
    {"key": "19", "hash_id": "19", "vlan": "0",
     "client": {"ip": "192.168.1.10", "port": 50022, "name": "web-server"},
     "server": {"ip": "198.51.100.50","port": 22,   "name": "remote-bastion"},
     "protocol": {"l4": "TCP",  "l7": "SSH"},   "l4_proto_id": 6,  "l7_cat": "Network",
     "thpt": {"bps": 80_000,    "pps": 12},
     "bytes": 40_960,   "pkts": 95,   "duration": 420, "score": 0,
     "breakdown": {"cli2srv": 55, "srv2cli": 45}, "local_client": True,  "local_server": False},
    # ── TCP / HTTP SYN flood (remote → local) ALERTED ────────────────────────
    {"key": "20", "hash_id": "20", "vlan": "0",
     "client": {"ip": "185.220.101.1","port": 0,    "name": "tor-exit-node"},
     "server": {"ip": "192.168.1.10", "port": 80,   "name": "web-server"},
     "protocol": {"l4": "TCP",  "l7": "HTTP"},  "l4_proto_id": 6,  "l7_cat": "Web",
     "thpt": {"bps": 10_000_000, "pps": 9000},
     "bytes": 8_388_608, "pkts": 75000, "duration": 600, "score": 80,
     "breakdown": {"cli2srv": 95, "srv2cli": 5},  "local_client": False, "local_server": True},
]

DB_FLOWS = [
    {
        "IPV4_SRC_ADDR": "192.168.1.30", "IPV4_DST_ADDR": "192.168.1.10",
        "L4_SRC_PORT": 52100, "L4_DST_PORT": 80,
        "PROTOCOL": 6, "L7_PROTO": 7, "L7_PROTO_NAME": "HTTP",
        "IN_BYTES": 2048, "OUT_BYTES": 8192,
        "FIRST_SWITCHED": int(time.time()) - 3600,
        "LAST_SWITCHED":  int(time.time()) - 3500,
    },
    {
        "IPV4_SRC_ADDR": "192.168.1.20", "IPV4_DST_ADDR": "192.168.1.10",
        "L4_SRC_PORT": 33100, "L4_DST_PORT": 3306,
        "PROTOCOL": 6, "L7_PROTO": 12, "L7_PROTO_NAME": "MySQL",
        "IN_BYTES": 512, "OUT_BYTES": 4096,
        "FIRST_SWITCHED": int(time.time()) - 7200,
        "LAST_SWITCHED":  int(time.time()) - 7100,
    },
]

# id must match the id values in L4_PROTOCOL_CONSTS — Checkmk looks up l4_counter["id"]
L4_COUNTERS = [
    {"id": 6,  "proto": "TCP",  "bytes_sent": 4_294_967_296, "bytes_rcvd": 8_589_934_592, "pkts_sent": 3_000_000, "pkts_rcvd": 6_000_000},
    {"id": 17, "proto": "UDP",  "bytes_sent": 536_870_912,   "bytes_rcvd": 268_435_456,   "pkts_sent": 500_000,   "pkts_rcvd": 250_000},
    {"id": 1,  "proto": "ICMP", "bytes_sent": 1_048_576,     "bytes_rcvd": 1_048_576,     "pkts_sent": 10_000,    "pkts_rcvd": 10_000},
]

# Flat list — Checkmk iterates this directly: for l7_counter in l7_counters: l7_counter["name"]
L7_COUNTERS = [
    {"name": "HTTP",       "proto_id": 7,   "bytes_sent": 2_147_483_648, "bytes_rcvd": 4_294_967_296, "num_flows": 1200},
    {"name": "HTTPS",      "proto_id": 91,  "bytes_sent": 1_073_741_824, "bytes_rcvd": 2_147_483_648, "num_flows": 3400},
    {"name": "DNS",        "proto_id": 5,   "bytes_sent": 10_485_760,    "bytes_rcvd": 20_971_520,    "num_flows": 8000},
    {"name": "MySQL",      "proto_id": 12,  "bytes_sent": 536_870_912,   "bytes_rcvd": 268_435_456,   "num_flows": 200},
    {"name": "SSH",        "proto_id": 92,  "bytes_sent": 52_428_800,    "bytes_rcvd": 26_214_400,    "num_flows": 15},
    {"name": "BitTorrent", "proto_id": 28,  "bytes_sent": 7_340_032,     "bytes_rcvd": 5_242_880,     "num_flows": 2},
    {"name": "SMTP",       "proto_id": 3,   "bytes_sent": 131_072,       "bytes_rcvd": 65_536,        "num_flows": 1},
    {"name": "NTP",        "proto_id": 61,  "bytes_sent": 256,           "bytes_rcvd": 256,           "num_flows": 1},
    {"name": "ICMP",       "proto_id": 257, "bytes_sent": 4_096,         "bytes_rcvd": 4_096,         "num_flows": 1},
]

L7_HOST_STATS = [
    {"proto": {"id": 7,  "name": "HTTP"},  "bytes_sent": 1_073_741_824, "bytes_rcvd": 2_147_483_648, "num_flows": 45},
    {"proto": {"id": 91, "name": "HTTPS"}, "bytes_sent": 536_870_912,   "bytes_rcvd": 1_073_741_824, "num_flows": 120},
    {"proto": {"id": 5,  "name": "DNS"},   "bytes_sent": 1_048_576,     "bytes_rcvd": 2_097_152,     "num_flows": 800},
]

ALERT_SEVERITY_CONSTS = [
    {"id": 0, "severity": "debug",     "label": "Debug",     "color": "#b0b0b0"},
    {"id": 1, "severity": "info",      "label": "Info",      "color": "#5bc0de"},
    {"id": 2, "severity": "notice",    "label": "Notice",    "color": "#aed6f1"},
    {"id": 3, "severity": "warning",   "label": "Warning",   "color": "#f0ad4e"},
    {"id": 4, "severity": "error",     "label": "Error",     "color": "#d9534f"},
    {"id": 5, "severity": "critical",  "label": "Critical",  "color": "#c0392b"},
    {"id": 6, "severity": "alert",     "label": "Alert",     "color": "#922b21"},
    {"id": 7, "severity": "emergency", "label": "Emergency", "color": "#7b241c"},
]

ALERT_TYPE_CONSTS = [
    # host alerts
    {"key": "alert_host_score",                    "type": "host_score",                   "alert_id": 105},
    {"key": "alert_login_failed",                  "type": "login_failed",                 "alert_id": 41},
    {"key": "alert_tcp_syn_flood",                 "type": "tcp_syn_flood",                "alert_id": 13},
    {"key": "alert_broadcast_non_unicast",         "type": "broadcast_non_unicast",        "alert_id": 85},
    {"key": "alert_port_scan",                     "type": "port_scan",                    "alert_id": 34},
    {"key": "alert_remote_to_local_insecure_proto","type": "remote_to_local_insecure_proto","alert_id": 73},
    {"key": "alert_suspicious_activity",           "type": "suspicious_activity",          "alert_id": 19},
    {"key": "alert_nmap_scan",                     "type": "nmap_scan",                    "alert_id": 56},
    # flow alerts
    {"key": "alert_ndpi_dns_suspicious_traffic",   "type": "dns_suspicious_traffic",       "alert_id": 60},
    {"key": "alert_potentially_dangerous_protocol","type": "potentially_dangerous_protocol","alert_id": 28},
    {"key": "alert_elephant_flow",                 "type": "elephant_flow",                "alert_id": 31},
    {"key": "alert_longlived_flow",                "type": "longlived_flow",               "alert_id": 32},
    {"key": "alert_ndpi_tls_certificate_expired",  "type": "tls_certificate_expired",      "alert_id": 102},
    {"key": "alert_udp_unidirectional",            "type": "udp_unidirectional",           "alert_id": 26},
]

_T = int(time.time())

ALERT_LIST = {
    # Checkmk calls get/host/alert/list.lua for host/engaged and host/historical
    "host": {
        "records": [
            # ── info (severity 1) ──────────────────────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_broadcast_non_unicast"},
                "score": {"value": 1}, "severity": {"value": 1},
                "ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                "flow": {}, "msg": {"description": "Broadcast/non-unicast traffic observed on workstation-02"},
                "tstamp": {"value": _T - 86400}, "tstamp_end": _T - 86200, "duration": 200, "count": 1,
            },
            {
                "family": "host", "alert_id": {"value": "alert_broadcast_non_unicast"},
                "score": {"value": 1}, "severity": {"value": 1},
                "ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                "flow": {}, "msg": {"description": "Broadcast/non-unicast traffic observed on workstation-01"},
                "tstamp": {"value": _T - 172800}, "tstamp_end": _T - 172600, "duration": 200, "count": 2,
            },
            {
                "family": "host", "alert_id": {"value": "alert_broadcast_non_unicast"},
                "score": {"value": 1}, "severity": {"value": 1},
                "ip": {"value": "192.168.1.10", "label": "web-server", "reference": ""},
                "flow": {}, "msg": {"description": "Broadcast/non-unicast traffic on web-server"},
                "tstamp": {"value": _T - 259200}, "tstamp_end": _T - 259000, "duration": 200, "count": 1,
            },
            # ── notice (severity 2) ────────────────────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_login_failed"},
                "score": {"value": 3}, "severity": {"value": 2},
                "ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                "flow": {}, "msg": {"description": "Failed login attempt on workstation-02"},
                "tstamp": {"value": _T - 43200}, "tstamp_end": _T - 43100, "duration": 100, "count": 2,
            },
            {
                "family": "host", "alert_id": {"value": "alert_login_failed"},
                "score": {"value": 3}, "severity": {"value": 2},
                "ip": {"value": "192.168.1.20", "label": "db-server", "reference": ""},
                "flow": {}, "msg": {"description": "Failed SSH login attempt on db-server"},
                "tstamp": {"value": _T - 129600}, "tstamp_end": _T - 129500, "duration": 100, "count": 1,
            },
            {
                "family": "host", "alert_id": {"value": "alert_broadcast_non_unicast"},
                "score": {"value": 2}, "severity": {"value": 2},
                "ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                "flow": {}, "msg": {"description": "Unusual multicast traffic from workstation-01"},
                "tstamp": {"value": _T - 216000}, "tstamp_end": _T - 215900, "duration": 100, "count": 3,
            },
            # ── warning (severity 3) ── recent ────────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_host_score"},
                "score": {"value": 10}, "severity": {"value": 3},
                "ip": {"value": "192.168.1.20", "label": "db-server", "reference": ""},
                "flow": {}, "msg": {"description": "Host db-server has score 10"},
                "tstamp": {"value": _T - 600}, "tstamp_end": _T - 300, "duration": 300, "count": 3,
            },
            {
                "family": "host", "alert_id": {"value": "alert_login_failed"},
                "score": {"value": 5}, "severity": {"value": 3},
                "ip": {"value": "192.168.1.10", "label": "web-server", "reference": ""},
                "flow": {}, "msg": {"description": "Multiple failed login attempts on web-server"},
                "tstamp": {"value": _T - 1200}, "tstamp_end": _T - 1000, "duration": 200, "count": 7,
            },
            {
                "family": "host", "alert_id": {"value": "alert_host_score"},
                "score": {"value": 12}, "severity": {"value": 3},
                "ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                "flow": {}, "msg": {"description": "Host workstation-02 has elevated score 12"},
                "tstamp": {"value": _T - 1800}, "tstamp_end": _T - 1500, "duration": 300, "count": 2,
            },
            {
                "family": "host", "alert_id": {"value": "alert_login_failed"},
                "score": {"value": 6}, "severity": {"value": 3},
                "ip": {"value": "192.168.1.20", "label": "db-server", "reference": ""},
                "flow": {}, "msg": {"description": "Repeated failed logins on db-server — possible brute force"},
                "tstamp": {"value": _T - 2400}, "tstamp_end": _T - 2100, "duration": 300, "count": 5,
            },
            {
                "family": "host", "alert_id": {"value": "alert_host_score"},
                "score": {"value": 8}, "severity": {"value": 3},
                "ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                "flow": {}, "msg": {"description": "Host workstation-01 score elevated to 8"},
                "tstamp": {"value": _T - 3000}, "tstamp_end": _T - 2700, "duration": 300, "count": 1,
            },
            # ── warning (severity 3) ── older ─────────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_host_score"},
                "score": {"value": 9}, "severity": {"value": 3},
                "ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                "flow": {}, "msg": {"description": "Workstation-02 score increased to 9"},
                "tstamp": {"value": _T - 28800}, "tstamp_end": _T - 28500, "duration": 300, "count": 2,
            },
            {
                "family": "host", "alert_id": {"value": "alert_login_failed"},
                "score": {"value": 5}, "severity": {"value": 3},
                "ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                "flow": {}, "msg": {"description": "Failed logins on workstation-01"},
                "tstamp": {"value": _T - 57600}, "tstamp_end": _T - 57300, "duration": 300, "count": 4,
            },
            {
                "family": "host", "alert_id": {"value": "alert_host_score"},
                "score": {"value": 11}, "severity": {"value": 3},
                "ip": {"value": "192.168.1.10", "label": "web-server", "reference": ""},
                "flow": {}, "msg": {"description": "web-server score elevated to 11"},
                "tstamp": {"value": _T - 115200}, "tstamp_end": _T - 114900, "duration": 300, "count": 1,
            },
            # ── error (severity 4) ── recent ──────────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_host_score"},
                "score": {"value": 25}, "severity": {"value": 4},
                "ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                "flow": {}, "msg": {"description": "Host workstation-01 has score 25"},
                "tstamp": {"value": _T - 900}, "tstamp_end": _T - 600, "duration": 300, "count": 1,
            },
            {
                "family": "host", "alert_id": {"value": "alert_login_failed"},
                "score": {"value": 18}, "severity": {"value": 4},
                "ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                "flow": {}, "msg": {"description": "High rate of failed logins — possible credential stuffing"},
                "tstamp": {"value": _T - 1500}, "tstamp_end": _T - 1200, "duration": 300, "count": 12,
            },
            {
                "family": "host", "alert_id": {"value": "alert_tcp_syn_flood"},
                "score": {"value": 20}, "severity": {"value": 4},
                "ip": {"value": "192.168.1.20", "label": "db-server", "reference": ""},
                "flow": {}, "msg": {"description": "SYN flood activity targeting db-server"},
                "tstamp": {"value": _T - 2100}, "tstamp_end": _T - 1800, "duration": 300, "count": 3,
            },
            # ── error (severity 4) ── older ───────────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_tcp_syn_flood"},
                "score": {"value": 22}, "severity": {"value": 4},
                "ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                "flow": {}, "msg": {"description": "SYN flood activity from workstation-02"},
                "tstamp": {"value": _T - 36000}, "tstamp_end": _T - 35700, "duration": 300, "count": 3,
            },
            {
                "family": "host", "alert_id": {"value": "alert_host_score"},
                "score": {"value": 30}, "severity": {"value": 4},
                "ip": {"value": "192.168.1.10", "label": "web-server", "reference": ""},
                "flow": {}, "msg": {"description": "web-server score hit threshold — score 30"},
                "tstamp": {"value": _T - 72000}, "tstamp_end": _T - 71700, "duration": 300, "count": 2,
            },
            {
                "family": "host", "alert_id": {"value": "alert_login_failed"},
                "score": {"value": 18}, "severity": {"value": 4},
                "ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                "flow": {}, "msg": {"description": "Credential stuffing attack detected on workstation-01"},
                "tstamp": {"value": _T - 144000}, "tstamp_end": _T - 143700, "duration": 300, "count": 12,
            },
            # ── critical (severity 5) ── recent ───────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_tcp_syn_flood"},
                "score": {"value": 50}, "severity": {"value": 5},
                "ip": {"value": "192.168.1.20", "label": "db-server", "reference": ""},
                "flow": {}, "msg": {"description": "TCP SYN flood detected on db-server"},
                "tstamp": {"value": _T - 2700}, "tstamp_end": _T - 2400, "duration": 300, "count": 2,
            },
            {
                "family": "host", "alert_id": {"value": "alert_host_score"},
                "score": {"value": 60}, "severity": {"value": 5},
                "ip": {"value": "192.168.1.10", "label": "web-server", "reference": ""},
                "flow": {}, "msg": {"description": "web-server score 60 — under active attack"},
                "tstamp": {"value": _T - 3300}, "tstamp_end": _T - 3000, "duration": 300, "count": 4,
            },
            # ── critical (severity 5) ── older ────────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_tcp_syn_flood"},
                "score": {"value": 45}, "severity": {"value": 5},
                "ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                "flow": {}, "msg": {"description": "Outbound SYN flood from workstation-01 — likely compromised"},
                "tstamp": {"value": _T - 100800}, "tstamp_end": _T - 100500, "duration": 300, "count": 6,
            },
            # ── alert (severity 6) ── recent ──────────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_tcp_syn_flood"},
                "score": {"value": 80}, "severity": {"value": 6},
                "ip": {"value": "192.168.1.10", "label": "web-server", "reference": ""},
                "flow": {}, "msg": {"description": "Sustained SYN flood attack on web-server — service degraded"},
                "tstamp": {"value": _T - 3600}, "tstamp_end": _T - 3000, "duration": 600, "count": 5,
            },
            {
                "family": "host", "alert_id": {"value": "alert_host_score"},
                "score": {"value": 90}, "severity": {"value": 6},
                "ip": {"value": "192.168.1.20", "label": "db-server", "reference": ""},
                "flow": {}, "msg": {"description": "db-server score 90 — ALERT level reached, immediate action required"},
                "tstamp": {"value": _T - 4200}, "tstamp_end": _T - 3600, "duration": 600, "count": 8,
            },
            # ── alert (severity 6) ── older ───────────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_tcp_syn_flood"},
                "score": {"value": 85}, "severity": {"value": 6},
                "ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                "flow": {}, "msg": {"description": "workstation-02 launching sustained SYN flood — isolate host"},
                "tstamp": {"value": _T - 79200}, "tstamp_end": _T - 78600, "duration": 600, "count": 10,
            },
            # ── new types (seed data) ──────────────────────────────────────────
            {
                "family": "host", "alert_id": {"value": "alert_port_scan"},
                "score": {"value": 20}, "severity": {"value": 4},
                "ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                "flow": {}, "msg": {"description": "Port scan detected from workstation-01"},
                "tstamp": {"value": _T - 1350}, "tstamp_end": _T - 1050, "duration": 300, "count": 1,
            },
            {
                "family": "host", "alert_id": {"value": "alert_nmap_scan"},
                "score": {"value": 35}, "severity": {"value": 5},
                "ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                "flow": {}, "msg": {"description": "Nmap scan activity detected from workstation-02"},
                "tstamp": {"value": _T - 2250}, "tstamp_end": _T - 1950, "duration": 300, "count": 2,
            },
            {
                "family": "host", "alert_id": {"value": "alert_suspicious_activity"},
                "score": {"value": 15}, "severity": {"value": 3},
                "ip": {"value": "192.168.1.20", "label": "db-server", "reference": ""},
                "flow": {}, "msg": {"description": "Suspicious activity pattern on db-server"},
                "tstamp": {"value": _T - 5100}, "tstamp_end": _T - 4800, "duration": 300, "count": 3,
            },
            {
                "family": "host", "alert_id": {"value": "alert_remote_to_local_insecure_proto"},
                "score": {"value": 25}, "severity": {"value": 4},
                "ip": {"value": "192.168.1.10", "label": "web-server", "reference": ""},
                "flow": {}, "msg": {"description": "Remote host using insecure protocol to reach web-server"},
                "tstamp": {"value": _T - 6300}, "tstamp_end": _T - 6000, "duration": 300, "count": 1,
            },
        ]
    },
    "flow": {
        "records": [
            # ── notice (severity 2) ────────────────────────────────────────────
            {
                "family": "flow", "alert_id": {"value": "alert_potentially_dangerous_protocol"},
                "score": {"value": 5}, "severity": {"value": 2},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                    "srv_ip": {"value": "8.8.8.8",      "label": "dns.google",     "reference": ""},
                },
                "description": {"descr": "Potentially dangerous protocol detected"}, "msg": {},
                "tstamp": {"value": _T - 1800}, "tstamp_end": _T - 1700, "duration": 100, "count": 1,
            },
            {
                "family": "flow", "alert_id": {"value": "alert_potentially_dangerous_protocol"},
                "score": {"value": 4}, "severity": {"value": 2},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                    "srv_ip": {"value": "8.8.8.8",      "label": "dns.google",     "reference": ""},
                },
                "description": {"descr": "Unusual outbound protocol from workstation-02"}, "msg": {},
                "tstamp": {"value": _T - 90000}, "tstamp_end": _T - 89900, "duration": 100, "count": 1,
            },
            # ── warning (severity 3) ───────────────────────────────────────────
            {
                "family": "flow", "alert_id": {"value": "alert_ndpi_dns_suspicious_traffic"},
                "score": {"value": 8}, "severity": {"value": 3},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                    "srv_ip": {"value": "8.8.8.8",      "label": "dns.google",     "reference": ""},
                },
                "description": {"descr": "Suspicious DNS traffic — possible DGA or tunneling"}, "msg": {},
                "tstamp": {"value": _T - 5400}, "tstamp_end": _T - 5200, "duration": 200, "count": 4,
            },
            {
                "family": "flow", "alert_id": {"value": "alert_ndpi_dns_suspicious_traffic"},
                "score": {"value": 7}, "severity": {"value": 3},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                    "srv_ip": {"value": "8.8.8.8",      "label": "dns.google",     "reference": ""},
                },
                "description": {"descr": "High-frequency DNS queries — possible data exfiltration"}, "msg": {},
                "tstamp": {"value": _T - 64800}, "tstamp_end": _T - 64500, "duration": 300, "count": 9,
            },
            {
                "family": "flow", "alert_id": {"value": "alert_potentially_dangerous_protocol"},
                "score": {"value": 9}, "severity": {"value": 3},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.20", "label": "db-server",      "reference": ""},
                    "srv_ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                },
                "description": {"descr": "db-server initiating unusual protocol to workstation"}, "msg": {},
                "tstamp": {"value": _T - 151200}, "tstamp_end": _T - 151000, "duration": 200, "count": 2,
            },
            # ── error (severity 4) ─────────────────────────────────────────────
            {
                "family": "flow", "alert_id": {"value": "alert_tcp_syn_flood"},
                "score": {"value": 30}, "severity": {"value": 4},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                    "srv_ip": {"value": "192.168.1.10", "label": "web-server",     "reference": ""},
                },
                "description": {"descr": "TCP SYN flood toward web-server"}, "msg": {},
                "tstamp": {"value": _T - 10800}, "tstamp_end": _T - 10500, "duration": 300, "count": 2,
            },
            {
                "family": "flow", "alert_id": {"value": "alert_ndpi_dns_suspicious_traffic"},
                "score": {"value": 20}, "severity": {"value": 4},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.20", "label": "db-server", "reference": ""},
                    "srv_ip": {"value": "8.8.8.8",      "label": "dns.google", "reference": ""},
                },
                "description": {"descr": "DNS tunneling detected from db-server — possible C2 channel"}, "msg": {},
                "tstamp": {"value": _T - 118800}, "tstamp_end": _T - 118500, "duration": 300, "count": 15,
            },
            {
                "family": "flow", "alert_id": {"value": "alert_tcp_syn_flood"},
                "score": {"value": 28}, "severity": {"value": 4},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                    "srv_ip": {"value": "192.168.1.20", "label": "db-server",      "reference": ""},
                },
                "description": {"descr": "SYN flood from workstation-02 targeting db-server"}, "msg": {},
                "tstamp": {"value": _T - 187200}, "tstamp_end": _T - 186900, "duration": 300, "count": 4,
            },
            # ── critical (severity 5) ──────────────────────────────────────────
            {
                "family": "flow", "alert_id": {"value": "alert_potentially_dangerous_protocol"},
                "score": {"value": 60}, "severity": {"value": 5},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.20", "label": "db-server",  "reference": ""},
                    "srv_ip": {"value": "8.8.8.8",      "label": "dns.google", "reference": ""},
                },
                "description": {"descr": "Critical: db-server communicating over dangerous protocol"}, "msg": {},
                "tstamp": {"value": _T - 18000}, "tstamp_end": _T - 17700, "duration": 300, "count": 1,
            },
            {
                "family": "flow", "alert_id": {"value": "alert_tcp_syn_flood"},
                "score": {"value": 55}, "severity": {"value": 5},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                    "srv_ip": {"value": "192.168.1.20", "label": "db-server",      "reference": ""},
                },
                "description": {"descr": "Critical SYN flood — db-server connection table nearly exhausted"}, "msg": {},
                "tstamp": {"value": _T - 234000}, "tstamp_end": _T - 233400, "duration": 600, "count": 7,
            },
            # ── new flow types (seed data) ─────────────────────────────────────
            {
                "family": "flow", "alert_id": {"value": "alert_elephant_flow"},
                "score": {"value": 6}, "severity": {"value": 2},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                    "srv_ip": {"value": "192.168.1.10", "label": "web-server",     "reference": ""},
                },
                "description": {"descr": "Elephant flow: unusually large data transfer"}, "msg": {},
                "tstamp": {"value": _T - 1650}, "tstamp_end": _T - 1350, "duration": 300, "count": 1,
            },
            {
                "family": "flow", "alert_id": {"value": "alert_longlived_flow"},
                "score": {"value": 4}, "severity": {"value": 2},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.20", "label": "db-server",  "reference": ""},
                    "srv_ip": {"value": "192.168.1.10", "label": "web-server", "reference": ""},
                },
                "description": {"descr": "Long-lived flow detected: db-server ↔ web-server"}, "msg": {},
                "tstamp": {"value": _T - 2550}, "tstamp_end": _T - 2250, "duration": 300, "count": 1,
            },
            {
                "family": "flow", "alert_id": {"value": "alert_ndpi_tls_certificate_expired"},
                "score": {"value": 12}, "severity": {"value": 3},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.40", "label": "workstation-02", "reference": ""},
                    "srv_ip": {"value": "93.184.216.34", "label": "example.com",   "reference": ""},
                },
                "description": {"descr": "TLS certificate expired on example.com"}, "msg": {},
                "tstamp": {"value": _T - 3450}, "tstamp_end": _T - 3150, "duration": 300, "count": 2,
            },
            {
                "family": "flow", "alert_id": {"value": "alert_udp_unidirectional"},
                "score": {"value": 5}, "severity": {"value": 2},
                "ip": {"value": "", "label": "", "reference": ""},
                "flow": {
                    "cli_ip": {"value": "192.168.1.30", "label": "workstation-01", "reference": ""},
                    "srv_ip": {"value": "8.8.8.8",      "label": "dns.google",     "reference": ""},
                },
                "description": {"descr": "UDP traffic with no response (unidirectional)"}, "msg": {},
                "tstamp": {"value": _T - 4350}, "tstamp_end": _T - 4050, "duration": 300, "count": 3,
            },
        ]
    },
}

ALERT_COUNTERS = {
    "severity": [
        {"entity_label": "Host", "name": "info",     "count": 3},
        {"entity_label": "Host", "name": "notice",   "count": 3},
        {"entity_label": "Host", "name": "warning",  "count": 8},
        {"entity_label": "Host", "name": "error",    "count": 7},
        {"entity_label": "Host", "name": "critical", "count": 5},
        {"entity_label": "Host", "name": "alert",    "count": 3},
        {"entity_label": "Flow", "name": "notice",   "count": 2},
        {"entity_label": "Flow", "name": "warning",  "count": 3},
        {"entity_label": "Flow", "name": "error",    "count": 3},
        {"entity_label": "Flow", "name": "critical", "count": 2},
    ],
    "type": [
        {"entity_label": "Host", "alert_id": "alert_host_score",                     "count": 8},
        {"entity_label": "Host", "alert_id": "alert_login_failed",                   "count": 6},
        {"entity_label": "Host", "alert_id": "alert_tcp_syn_flood",                  "count": 5},
        {"entity_label": "Host", "alert_id": "alert_broadcast_non_unicast",          "count": 3},
        {"entity_label": "Flow", "alert_id": "alert_potentially_dangerous_protocol", "count": 4},
        {"entity_label": "Flow", "alert_id": "alert_ndpi_dns_suspicious_traffic",    "count": 4},
        {"entity_label": "Flow", "alert_id": "alert_tcp_syn_flood",                  "count": 4},
    ],
}

# Checkmk expects a flat list[TopTalker] with keys: name, throughput (bps float), url, throughput_type
_NTOP_BASE = "http://192.168.128.10:3000"
TOP_TALKERS = {
    "local": [
        {"name": "web-server",     "throughput": 2_000_000.0, "throughput_type": "bps",
         "url": f"{_NTOP_BASE}/lua/host_details.lua?host=192.168.1.10&ifid=1"},
        {"name": "db-server",      "throughput": 1_000_000.0, "throughput_type": "bps",
         "url": f"{_NTOP_BASE}/lua/host_details.lua?host=192.168.1.20&ifid=1"},
        {"name": "workstation-01", "throughput": 500_000.0,   "throughput_type": "bps",
         "url": f"{_NTOP_BASE}/lua/host_details.lua?host=192.168.1.30&ifid=1"},
    ],
    "remote": [
        {"name": "dns.google",     "throughput": 20_000.0,    "throughput_type": "bps",
         "url": f"{_NTOP_BASE}/lua/host_details.lua?host=8.8.8.8&ifid=1"},
    ],
}

L4_PROTOCOL_CONSTS = [
    {"id": 6,   "name": "TCP",   "key": "tcp"},
    {"id": 17,  "name": "UDP",   "key": "udp"},
    {"id": 1,   "name": "ICMP",  "key": "icmp"},
    {"id": 58,  "name": "ICMPv6","key": "icmpv6"},
    {"id": 132, "name": "SCTP",  "key": "sctp"},
]

L7_CONSTS = {
    # cat_id is required: Checkmk builds a category→cat_id lookup from it
    "application": [
        {"id": 7,   "name": "HTTP",       "breed": "Safe",       "cat_id": 5},
        {"id": 91,  "name": "HTTPS",      "breed": "Safe",       "cat_id": 5},
        {"id": 5,   "name": "DNS",        "breed": "Acceptable", "cat_id": 14},
        {"id": 12,  "name": "MySQL",      "breed": "Acceptable", "cat_id": 12},
        {"id": 92,  "name": "SSH",        "breed": "Acceptable", "cat_id": 14},
        {"id": 28,  "name": "BitTorrent", "breed": "Unsafe",     "cat_id": 0},
        {"id": 3,   "name": "SMTP",       "breed": "Safe",       "cat_id": 3},
        {"id": 257, "name": "ICMP",       "breed": "Safe",       "cat_id": 14},
        {"id": 61,  "name": "NTP",        "breed": "Acceptable", "cat_id": 14},
    ],
    # cat_id must match the id values used in applications above
    "category": [
        {"id": 0,  "cat_id": 0,  "name": "Unspecified"},
        {"id": 3,  "cat_id": 3,  "name": "Email"},
        {"id": 5,  "cat_id": 5,  "name": "Web"},
        {"id": 12, "cat_id": 12, "name": "Database"},
        {"id": 14, "cat_id": 14, "name": "Network"},
    ],
}


def _build_alert_timeseries(ifid: str, schema: str) -> dict:
    """Alert timeseries for get/<entity>/alert/ts.lua (Checkmk passes by_24h=true).
    Format: {str(day_start_epoch): [h0, h1, ..., h23]} — 24 hourly counts per day.
    Checkmk's _parse_and_reduce_timeseries does:
        for date, counts in data.items():
            for idx, count in enumerate(counts):
                reduced.append((str(int(date) + idx*3600), count))
    So each list item corresponds to one hour of the day (idx=0..23).
    We seed the buckets from actual alert timestamps so the chart reflects real data.
    """
    now = int(time.time())
    midnight_today = (now // 86400) * 86400
    # Pre-populate day→hour buckets from all known alerts
    entity = schema.split(":")[0] if ":" in schema else schema
    all_records = _all_alert_records(entity) if entity in ("host", "flow") else []
    # day_start → [h0..h23]
    data: dict = {}
    for day_off in range(31):
        day_start = midnight_today - (30 - day_off) * 86400
        data[str(day_start)] = [0] * 24
    for rec in all_records:
        ts = rec["tstamp"]["value"]
        day_start = (ts // 86400) * 86400
        key = str(day_start)
        if key in data:
            hour = (ts % 86400) // 3600
            data[key][hour] += rec.get("count", 1)
    # Add synthetic background noise for days with no real alerts
    for key, hours in data.items():
        if sum(hours) == 0:
            for h in range(24):
                if 8 <= h <= 18 and random.random() < 0.6:
                    hours[h] = random.randint(1, 3)
                elif random.random() < 0.15:
                    hours[h] = 1
    return data


def _build_traffic_timeseries(ifid: str, schema: str) -> dict:
    """TrafficTimeSeriesResponse for get/timeseries/ts.lua.
    Checkmk reads: metadata.epoch_step, metadata.epoch_begin, series[].id,
    series[].tags, series[].data[]."""
    import random
    now = int(time.time())
    step = 300  # 5-minute steps
    start = now - 3600
    points = []
    t = start
    while t < now:
        points.append(t)
        t += step
    is_traffic = "traffic" in schema or "ndpi" in schema
    series = []
    if is_traffic:
        series.append({
            "id": "bytes",
            "tags": {"ifid": ifid},
            "data": [random.randint(500_000, 50_000_000) for _ in points],
        })
        series.append({
            "id": "bytes",
            "tags": {"ifid": ifid},
            "data": [random.randint(200_000, 25_000_000) for _ in points],
        })
    else:
        series.append({
            "id": "bytes",
            "tags": {"ifid": ifid},
            "data": [random.randint(0, 100) for _ in points],
        })
    return {
        "metadata": {"epoch_begin": start, "epoch_step": step},
        "series": series,
    }


# ── Dynamic alert generator ───────────────────────────────────────────────────
# New alerts are appended every ALERT_GEN_INTERVAL seconds.  The combined
# alert list (static seed + dynamic) is what the API serves.

ALERT_GEN_INTERVAL = 30   # seconds between batches
ALERT_DYNAMIC_MAX  = 200  # max dynamic records to keep per category

_dynamic_alerts: dict[str, list] = {"host": [], "flow": []}
_dynamic_lock = threading.Lock()

_HOST_TARGETS = [
    {"ip": "192.168.1.10", "name": "web-server"},
    {"ip": "192.168.1.20", "name": "db-server"},
    {"ip": "192.168.1.30", "name": "workstation-01"},
    {"ip": "192.168.1.40", "name": "workstation-02"},
]
_FLOW_PAIRS = [
    ({"ip": "192.168.1.30", "name": "workstation-01"}, {"ip": "8.8.8.8",      "name": "dns.google"}),
    ({"ip": "192.168.1.40", "name": "workstation-02"}, {"ip": "8.8.8.8",      "name": "dns.google"}),
    ({"ip": "192.168.1.20", "name": "db-server"},      {"ip": "8.8.8.8",      "name": "dns.google"}),
    ({"ip": "192.168.1.30", "name": "workstation-01"}, {"ip": "192.168.1.10", "name": "web-server"}),
    ({"ip": "192.168.1.40", "name": "workstation-02"}, {"ip": "192.168.1.20", "name": "db-server"}),
    ({"ip": "203.0.113.99", "name": "suspicious-host"},{"ip": "192.168.1.10", "name": "web-server"}),
]
_HOST_ALERT_TYPES = [
    ("alert_host_score",                     "Host score elevated",                  [3, 3, 4, 5, 6]),
    ("alert_login_failed",                   "Failed login attempt",                 [2, 3, 3, 4]),
    ("alert_tcp_syn_flood",                  "TCP SYN flood detected",               [4, 5, 5, 6]),
    ("alert_broadcast_non_unicast",          "Broadcast/non-unicast traffic",        [1, 2]),
    ("alert_port_scan",                      "Port scan detected",                   [3, 4, 4, 5]),
    ("alert_nmap_scan",                      "Nmap scan detected",                   [3, 4, 5]),
    ("alert_suspicious_activity",            "Suspicious activity",                  [2, 3, 4]),
    ("alert_remote_to_local_insecure_proto", "Remote to local insecure protocol",    [3, 4, 5]),
]
_FLOW_ALERT_TYPES = [
    ("alert_ndpi_dns_suspicious_traffic",    "Suspicious DNS traffic",               [3, 3, 4]),
    ("alert_potentially_dangerous_protocol", "Potentially dangerous protocol",       [2, 3, 4, 5]),
    ("alert_tcp_syn_flood",                  "TCP SYN flood",                        [4, 5]),
    ("alert_elephant_flow",                  "Elephant flow detected",               [2, 3]),
    ("alert_longlived_flow",                 "Long-lived flow",                      [2, 2, 3]),
    ("alert_ndpi_tls_certificate_expired",   "TLS certificate expired",              [3, 4]),
    ("alert_udp_unidirectional",             "UDP unidirectional traffic",           [2, 3]),
]


def _make_dynamic_alert(category: str) -> dict:
    now = int(time.time())
    duration = random.choice([60, 120, 300, 600])
    if category == "host":
        host = random.choice(_HOST_TARGETS)
        alert_type, msg_prefix, severities = random.choice(_HOST_ALERT_TYPES)
        sev = random.choice(severities)
        return {
            "family": "host",
            "alert_id":  {"value": alert_type},
            "score":     {"value": sev * random.randint(4, 12)},
            "severity":  {"value": sev},
            "ip":        {"value": host["ip"], "label": host["name"], "reference": ""},
            "flow": {},
            "msg":       {"description": f"{msg_prefix} on {host['name']}"},
            "tstamp":    {"value": now},
            "tstamp_end": now + duration,
            "duration":  duration,
            "count":     random.randint(1, 10),
        }
    else:
        cli, srv = random.choice(_FLOW_PAIRS)
        alert_type, msg_prefix, severities = random.choice(_FLOW_ALERT_TYPES)
        sev = random.choice(severities)
        return {
            "family": "flow",
            "alert_id":  {"value": alert_type},
            "score":     {"value": sev * random.randint(3, 10)},
            "severity":  {"value": sev},
            "ip":        {"value": "", "label": "", "reference": ""},
            "flow": {
                "cli_ip": {"value": cli["ip"], "label": cli["name"], "reference": ""},
                "srv_ip": {"value": srv["ip"], "label": srv["name"], "reference": ""},
            },
            "description": {"descr": f"{msg_prefix}: {cli['name']} → {srv['name']}"},
            "msg": {},
            "tstamp":    {"value": now},
            "tstamp_end": now + duration,
            "duration":  duration,
            "count":     random.randint(1, 5),
        }


def _alert_generator_loop():
    """Background thread: emit 2-4 new alerts every ALERT_GEN_INTERVAL seconds."""
    # Stagger startup so we have immediate data on first load
    time.sleep(5)
    while True:
        batch = random.randint(2, 4)
        new_alerts: dict[str, list] = {"host": [], "flow": []}
        for _ in range(batch):
            cat = random.choice(["host", "flow"])
            new_alerts[cat].append(_make_dynamic_alert(cat))
        with _dynamic_lock:
            for cat in ("host", "flow"):
                _dynamic_alerts[cat] = (new_alerts[cat] + _dynamic_alerts[cat])[:ALERT_DYNAMIC_MAX]
        time.sleep(ALERT_GEN_INTERVAL)


# Start generator thread (daemon so it stops with the process)
_gen_thread = threading.Thread(target=_alert_generator_loop, daemon=True)
_gen_thread.start()


def _all_alert_records(entity: str) -> list:
    """Merge static seed with live-generated alerts, newest first."""
    static = ALERT_LIST.get(entity, {}).get("records", [])
    with _dynamic_lock:
        dynamic = list(_dynamic_alerts.get(entity, []))
    # dynamic alerts have the most recent timestamps, put them first
    combined = dynamic + static
    combined.sort(key=lambda r: r["tstamp"]["value"], reverse=True)
    return combined


# ── Version endpoint (GET + Basic Auth) ──────────────────────────────────────

@app.route("/lua/rest/version.lua", methods=["GET"])
@require_basic_auth
def get_version():
    log_req()
    return rsp({
        "current_version": 2,
        "version_string": "2.0 (mock)",
        "supported_versions": [{"version": 1}, {"version": 2}],
    })


# ── Session creation (POST + Basic Auth) ──────────────────────────────────────

@app.route("/lua/rest/v2/create/ntopng/session.lua", methods=["POST"])
@require_basic_auth
def create_session():
    log_req()
    token = secrets.token_hex(16)
    user = request.args.get("run_as", ADMIN_USER)
    SESSIONS[token] = {"user": user, "created": time.time()}
    app.logger.info("Created session %s for user %s", token, user)
    response = make_response(rsp({"session": token}))
    response.set_cookie("session", token, httponly=True)
    return response


# ── Interfaces ────────────────────────────────────────────────────────────────

@app.route("/lua/rest/v2/get/ntopng/interfaces.lua", methods=["GET", "POST"])
@require_session
def get_ntopng_interfaces():
    log_req()
    return rsp(INTERFACES)

@app.route("/lua/rest/v2/get/interface/data.lua", methods=["GET", "POST"])
@require_session
def get_interface_data():
    log_req()
    ifid = int(request.args.get("ifid", 1))
    iface = next((i for i in INTERFACES if i["ifid"] == ifid), INTERFACES[0])
    return rsp(iface)


# ── Hosts ─────────────────────────────────────────────────────────────────────

@app.route("/lua/rest/v2/get/host/data.lua", methods=["GET", "POST"])
@require_session
def get_host_data():
    log_req()
    host = request.args.get("host", "192.168.1.10@0")
    # normalise: host=IP without @vlan → append @0
    if "@" not in host:
        host = f"{host}@0"
    data = HOST_DATA.get(host, {
        "ip": host.split("@")[0], "vlan": int(host.split("@")[1]),
        "bytes_sent": 0, "bytes_rcvd": 0,
        "active_flows_as_client": 0, "active_flows_as_server": 0,
        "num_alerts": 0, "score": 0,
    })
    return rsp(data)

@app.route("/lua/rest/v2/get/host/interfaces.lua", methods=["GET", "POST"])
@require_session
def get_host_interfaces():
    log_req()
    host = request.args.get("host", "192.168.1.10@0")
    ip = host.split("@")[0]
    vlan = host.split("@")[1] if "@" in host else "0"
    # Return ifid list for this host
    return rsp({f"{ip}@{vlan}": [{"ifid": 1}]})

@app.route("/lua/rest/v2/get/host/l7/stats.lua", methods=["GET", "POST"])
@require_session
def get_host_l7_stats():
    log_req()
    return rsp(L7_HOST_STATS)

@app.route("/lua/rest/v2/get/host/custom_data.lua", methods=["GET", "POST"])
@require_session
def get_host_custom_data():
    log_req()
    fields = request.args.get("field_alias", "ip,vlan")
    host_filter = request.args.get("host")
    field_list = [f.strip() for f in fields.split(",")]

    def _pick(h: dict) -> dict:
        return {f: h.get(f, "") for f in field_list}

    if host_filter:
        ip = host_filter.split("@")[0]
        matches = [_pick(h) for h in HOSTS if h["ip"] == ip]
    else:
        matches = [_pick(h) for h in HOSTS]

    return rsp(matches)


# ── Flows ─────────────────────────────────────────────────────────────────────

@app.route("/lua/rest/v2/get/flow/active.lua", methods=["GET", "POST"])
@require_session
def get_active_flows():
    log_req()
    flows = list(ACTIVE_FLOWS)

    # Filter by host IP
    host_filter = request.args.get("host")
    if host_filter:
        ip = host_filter.split("@")[0]
        flows = [f for f in flows if f["client"]["ip"] == ip or f["server"]["ip"] == ip]

    # flowhosts_type: local_only / remote_only / local_origin_remote_target / remote_origin_local_target
    fht = request.args.get("flowhosts_type", "-1")
    if fht == "local_only":
        flows = [f for f in flows if f.get("local_client") and f.get("local_server")]
    elif fht == "remote_only":
        flows = [f for f in flows if not f.get("local_client") and not f.get("local_server")]
    elif fht == "local_origin_remote_target":
        flows = [f for f in flows if f.get("local_client") and not f.get("local_server")]
    elif fht == "remote_origin_local_target":
        flows = [f for f in flows if not f.get("local_client") and f.get("local_server")]

    # flow_status: normal (score==0) / alerted (score>0)
    flow_status = request.args.get("flow_status", "-1")
    if flow_status == "normal":
        flows = [f for f in flows if not f.get("score")]
    elif flow_status == "alerted":
        flows = [f for f in flows if f.get("score")]

    # l4proto: numeric protocol id
    l4proto = request.args.get("l4proto", "-1")
    if l4proto != "-1":
        flows = [f for f in flows if str(f.get("l4_proto_id", "")) == l4proto]

    # application: L7 name
    application = request.args.get("application", "-1")
    if application != "-1":
        flows = [f for f in flows if f.get("protocol", {}).get("l7") == application]

    # category: L7 category name
    category = request.args.get("category", "-1")
    if category != "-1":
        flows = [f for f in flows if f.get("l7_cat") == category]

    per_page = int(request.args.get("perPage", 100))
    current_page = int(request.args.get("currentPage", 1))
    start = (current_page - 1) * per_page
    return rsp({"data": flows[start: start + per_page], "currentPage": current_page, "totalRows": len(flows)})

@app.route("/lua/rest/v2/get/db/flows.lua", methods=["GET", "POST"])
@require_session
def get_db_flows():
    log_req()
    max_hits = int(request.args.get("maxhits_clause", len(DB_FLOWS)))
    return rsp(DB_FLOWS[:max_hits])

@app.route("/lua/rest/v2/get/flow/l4/counters.lua", methods=["GET", "POST"])
@require_session
def get_l4_counters():
    log_req()
    return rsp(L4_COUNTERS)

@app.route("/lua/rest/v2/get/flow/l7/counters.lua", methods=["GET", "POST"])
@require_session
def get_l7_counters():
    log_req()
    return rsp(L7_COUNTERS)


# ── Alerts ────────────────────────────────────────────────────────────────────

@app.route("/lua/rest/v2/get/alert/severity/consts.lua", methods=["GET", "POST"])
@require_session
def get_alert_severity_consts():
    log_req()
    return rsp(ALERT_SEVERITY_CONSTS)

@app.route("/lua/rest/v2/get/alert/type/consts.lua", methods=["GET", "POST"])
@require_session
def get_alert_type_consts():
    log_req()
    return rsp(ALERT_TYPE_CONSTS)

@app.route("/lua/rest/v2/get/alert/<settings>/counters.lua", methods=["GET", "POST"])
@require_session
def get_alert_counters(settings):
    log_req()
    return rsp(ALERT_COUNTERS.get(settings, []))

@app.route("/lua/rest/v2/get/<entity>/alert/list.lua", methods=["GET", "POST"])
@require_session
def get_alert_list(entity):
    log_req()
    records = _all_alert_records(entity)

    # Filter by epoch_begin / epoch_end
    epoch_begin = request.args.get("epoch_begin")
    epoch_end   = request.args.get("epoch_end")
    if epoch_begin:
        records = [r for r in records if r["tstamp"]["value"] >= int(epoch_begin)]
    if epoch_end:
        records = [r for r in records if r["tstamp"]["value"] <= int(epoch_end)]

    # Filter by alert_severity (numeric string, matches severity.value)
    alert_severity = request.args.get("alert_severity")
    if alert_severity:
        records = [r for r in records if str(r["severity"]["value"]) == alert_severity]

    # Filter by alert_type (string key, matches alert_id.value)
    alert_type = request.args.get("alert_type")
    if alert_type:
        records = [r for r in records if r["alert_id"]["value"] == alert_type]

    # Sort by tstamp desc (matches sort=tstamp&order=desc)
    records.sort(key=lambda r: r["tstamp"]["value"], reverse=True)

    # Pagination
    start  = int(request.args.get("start", 0))
    length = int(request.args.get("length", 20))
    page   = records[start: start + length]

    return rsp({"records": page, "totalRows": len(records)})

@app.route("/lua/rest/v2/get/<entity>/alert/ts.lua", methods=["GET", "POST"])
@require_session
def get_alert_ts(entity):
    log_req()
    ifid = request.args.get("ifid", "1")
    return rsp(_build_alert_timeseries(ifid, f"{entity}:alerts"))


# ── Timeseries ────────────────────────────────────────────────────────────────

@app.route("/lua/rest/v2/get/timeseries/ts.lua", methods=["GET", "POST"])
@require_session
def get_timeseries():
    log_req()
    ts_schema = request.args.get("ts_schema", "iface:traffic")
    ts_query  = request.args.get("ts_query", "ifid:1")
    ifid = "1"
    for part in ts_query.split(","):
        if part.startswith("ifid:"):
            ifid = part.split(":")[1]
    return rsp(_build_traffic_timeseries(ifid, ts_schema))


# ── Protocol constants ────────────────────────────────────────────────────────

@app.route("/lua/rest/v2/get/l4/protocol/consts.lua", methods=["GET", "POST"])
@require_session
def get_l4_consts():
    log_req()
    return rsp(L4_PROTOCOL_CONSTS)

@app.route("/lua/rest/v2/get/l7/<settings>/consts.lua", methods=["GET", "POST"])
@require_session
def get_l7_consts(settings):
    log_req()
    return rsp(L7_CONSTS.get(settings, L7_CONSTS["application"]))


# ── Top talkers (Pro endpoint) ────────────────────────────────────────────────

@app.route("/lua/pro/rest/v2/get/interface/top/<type_>/talkers.lua", methods=["GET", "POST"])
@require_session
def get_top_talkers(type_):
    log_req()
    return rsp(TOP_TALKERS.get(type_, {}))


# ── ntopng Web UI stubs (browser navigation links embedded by Checkmk) ───────

@app.route("/lua/flows_stats.lua", methods=["GET"])
def flows_stats():
    log_req()
    ifid = request.args.get("ifid", "1")
    rows = "".join(
        f"<tr><td>{f['client']['ip']}</td><td>{f['server']['ip']}</td>"
        f"<td>{f['protocol']['l7']}</td><td>{f['thpt']['bps']:,} bps</td></tr>"
        for f in ACTIVE_FLOWS
    )
    return (
        f"<html><body><h2>ntopng mock — flows (ifid={ifid})</h2>"
        f"<table border=1><tr><th>Client</th><th>Server</th><th>App</th><th>Throughput</th></tr>{rows}</table></body></html>"
    ), 200, {"Content-Type": "text/html"}


@app.route("/lua/hosts_stats.lua", methods=["GET"])
def hosts_stats():
    log_req()
    mode = request.args.get("mode", "local")
    ifid = request.args.get("ifid", "1")
    hosts = [h for h in HOSTS if (h["is_local"] if mode == "local" else not h["is_local"])]
    rows = "".join(
        f"<tr><td>{h['ip']}</td><td>{h['name']}</td><td>{'local' if h['is_local'] else 'remote'}</td></tr>"
        for h in hosts
    )
    return (
        f"<html><body><h2>ntopng mock — hosts ({mode}, ifid={ifid})</h2>"
        f"<table border=1><tr><th>IP</th><th>Name</th><th>Type</th></tr>{rows}</table></body></html>"
    ), 200, {"Content-Type": "text/html"}


@app.route("/lua/host_details.lua", methods=["GET"])
def host_details():
    log_req()
    host_ip = request.args.get("host", "")
    ifid    = request.args.get("ifid", "1")
    page    = request.args.get("page", "")
    # Look up host name from mock data
    host_info = next((h for h in HOSTS if h["ip"] == host_ip), None)
    name = host_info["name"] if host_info else host_ip
    is_local = host_info["is_local"] if host_info else False
    host_data = HOST_DATA.get(f"{host_ip}@0", {})
    # Active alerts for this host
    alerts = [r for r in _all_alert_records("host") if r["ip"]["value"] == host_ip][:10]
    alert_rows = "".join(
        f"<tr><td>{a['alert_id']['value']}</td>"
        f"<td>{a['severity']['value']}</td>"
        f"<td>{a['msg'].get('description','')}</td></tr>"
        for a in alerts
    )
    # Active flows for this host
    flows = [f for f in ACTIVE_FLOWS if f["client"]["ip"] == host_ip or f["server"]["ip"] == host_ip]
    flow_rows = "".join(
        f"<tr><td>{f['client']['ip']}:{f['client']['port']}</td>"
        f"<td>{f['server']['ip']}:{f['server']['port']}</td>"
        f"<td>{f['protocol']['l7']}</td>"
        f"<td>{f['thpt']['bps']:,} bps</td>"
        f"<td>{'alerted' if f.get('score') else 'normal'}</td></tr>"
        for f in flows
    )
    html = f"""<html><head><title>ntopng mock — {name}</title>
<style>body{{font-family:monospace;background:#1a1a2e;color:#eee;padding:20px}}
h2{{color:#00d4aa}} table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #444;padding:6px 10px;text-align:left}}
th{{background:#333}} .badge{{padding:2px 8px;border-radius:3px;background:#555}}</style>
</head><body>
<h2>Host: {name} ({host_ip})</h2>
<table><tr><th>Field</th><th>Value</th></tr>
<tr><td>IP</td><td>{host_ip}</td></tr>
<tr><td>Name</td><td>{name}</td></tr>
<tr><td>Interface</td><td>ifid={ifid}</td></tr>
<tr><td>Type</td><td>{'Local' if is_local else 'Remote'}</td></tr>
<tr><td>Bytes sent</td><td>{host_data.get('bytes_sent',0):,}</td></tr>
<tr><td>Bytes rcvd</td><td>{host_data.get('bytes_rcvd',0):,}</td></tr>
<tr><td>Active flows (client)</td><td>{host_data.get('active_flows_as_client',0)}</td></tr>
<tr><td>Active flows (server)</td><td>{host_data.get('active_flows_as_server',0)}</td></tr>
<tr><td>Score</td><td>{host_data.get('score',0)}</td></tr>
<tr><td>Alerts</td><td>{host_data.get('num_alerts',0)}</td></tr>
</table>
<h2>Active Flows</h2>
<table><tr><th>Client</th><th>Server</th><th>App</th><th>Throughput</th><th>Status</th></tr>
{flow_rows if flow_rows else '<tr><td colspan=5>No active flows</td></tr>'}
</table>
<h2>Alerts</h2>
<table><tr><th>Type</th><th>Severity</th><th>Description</th></tr>
{alert_rows if alert_rows else '<tr><td colspan=3>No alerts</td></tr>'}
</table>
</body></html>"""
    return html, 200, {"Content-Type": "text/html"}


# ── Catch-all ─────────────────────────────────────────────────────────────────

@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def catch_all(path):
    app.logger.warning("UNIMPLEMENTED: %s /%s", request.method, path)
    return jsonify({"rc": -1, "rc_str": f"Endpoint not implemented: /{path}", "rsp": None}), 404


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
