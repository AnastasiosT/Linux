"""
Meraki Dashboard API v1 — Mock Server
Tailored for the thl-cmk Cisco Meraki Checkmk community plugin.

Multi-tenant: each API key maps to a separate organization with its own data.
Add a new customer by calling build_tenant() and registering a key in TENANTS.

API keys (configure these in your Checkmk special agent rules):
  key-customer-a  →  Org "Customer A"
  key-customer-b  →  Org "Customer B"

Endpoints implemented:
  /api/v1/organizations
  /api/v1/organizations/<orgId>/networks
  /api/v1/organizations/<orgId>/devices
  /api/v1/organizations/<orgId>/devices/statuses
  /api/v1/organizations/<orgId>/devices/uplinks/loss-and-latency
  /api/v1/organizations/<orgId>/devices/uplinks/addresses/byDevice
  /api/v1/organizations/<orgId>/licenses/overview
  /api/v1/organizations/<orgId>/appliance/uplink/statuses
  /api/v1/organizations/<orgId>/appliance/uplinks/usage/byNetwork
  /api/v1/organizations/<orgId>/appliance/vpn/statuses
  /api/v1/organizations/<orgId>/switch/ports/bySwitch
  /api/v1/organizations/<orgId>/wireless/devices/ethernet/statuses
  /api/v1/organizations/<orgId>/cellularGateway/uplink/statuses
  /api/v1/organizations/<orgId>/sensor/readings/latest
  /api/v1/organizations/<orgId>/apiRequests/overview/responseCodes/byInterval
  /api/v1/networks/<networkId>/devices
  /api/v1/devices/<serial>/switch/ports
  /api/v1/devices/<serial>/switch/ports/statuses
  /api/v1/devices/<serial>/appliance/uplinks/settings
  /api/v1/devices/<serial>/appliance/performance
  /api/v1/devices/<serial>/wireless/status
  /api/v1/devices/<serial>/management/interface
"""

from flask import Flask, jsonify, request
import logging, random

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = Flask(__name__)


# ── Tenant factory ────────────────────────────────────────────────────────────

def build_tenant(org_id, org_name, prefix, wan1_ip="203.0.113.10", branch_wan1="198.51.100.20"):
    """Build a full set of mock data for one Meraki organization."""

    net1 = f"N_{org_id}1111111111111111"
    net2 = f"N_{org_id}2222222222222222"

    mx1  = f"{prefix}-MX01"
    mx2  = f"{prefix}-MX02"
    sw1  = f"{prefix}-SW01"
    sw2  = f"{prefix}-SW02"
    ap1  = f"{prefix}-AP01"
    sn1  = f"{prefix}-SN01"
    mg1  = f"{prefix}-MG01"

    organizations = [{
        "id": org_id,
        "name": org_name,
        "url": f"https://n1.meraki.com/o/{org_id}/manage/organization/overview",
        "api": {"enabled": True},
        "licensing": {"model": "co-term"},
        "cloud": {"region": {"name": "North America"}},
    }]

    networks = [
        {
            "id": net1, "organizationId": org_id, "name": f"{org_name}-HQ",
            "productTypes": ["appliance", "switch", "wireless", "sensor", "cellularGateway"],
            "timeZone": "Europe/Berlin", "tags": ["checkmk-test"],
            "enrollmentString": None, "isBoundToConfigTemplate": False,
            "notes": "", "url": f"https://n1.meraki.com/o/{net1}/manage/nodes/list",
        },
        {
            "id": net2, "organizationId": org_id, "name": f"{org_name}-Branch",
            "productTypes": ["appliance", "switch"],
            "timeZone": "Europe/Berlin", "tags": [],
            "enrollmentString": None, "isBoundToConfigTemplate": False,
            "notes": "", "url": f"https://n1.meraki.com/o/{net2}/manage/nodes/list",
        },
    ]

    devices = [
        {"serial": mx1, "name": f"{org_name}-HQ-MX",     "model": "MX68",     "networkId": net1, "mac": "aa:bb:cc:dd:00:01", "lanIp": "192.168.1.1",  "wan1Ip": wan1_ip,      "wan2Ip": None,             "lat": 48.137154, "lng": 11.576124, "address": "Munich, Germany",  "productType": "appliance", "firmware": "wired-18-107-2"},
        {"serial": sw1, "name": f"{org_name}-HQ-SW",     "model": "MS220-8P", "networkId": net1, "mac": "aa:bb:cc:dd:00:02", "lanIp": "192.168.1.2",  "wan1Ip": None,         "wan2Ip": None,             "lat": 48.137154, "lng": 11.576124, "address": "Munich, Germany",  "productType": "switch",    "firmware": "switch-15-21-1"},
        {"serial": ap1, "name": f"{org_name}-HQ-AP",     "model": "MR46",     "networkId": net1, "mac": "aa:bb:cc:dd:00:03", "lanIp": "192.168.1.3",  "wan1Ip": None,         "wan2Ip": None,             "lat": 48.137154, "lng": 11.576124, "address": "Munich, Germany",  "productType": "wireless",  "firmware": "wireless-29-6-1"},
        {"serial": sn1, "name": f"{org_name}-HQ-Sensor", "model": "MT10",     "networkId": net1, "mac": "aa:bb:cc:dd:00:06", "lanIp": "192.168.1.4",  "wan1Ip": None,         "wan2Ip": None,             "lat": 48.137154, "lng": 11.576124, "address": "Munich, Germany",  "productType": "sensor",    "firmware": "sensor-1-2-3"},
        {"serial": mx2, "name": f"{org_name}-Branch-MX", "model": "MX65",     "networkId": net2, "mac": "aa:bb:cc:dd:00:04", "lanIp": "10.0.1.1",     "wan1Ip": branch_wan1,  "wan2Ip": f"{branch_wan1[:-2]}21", "lat": 52.520008, "lng": 13.404954, "address": "Berlin, Germany",  "productType": "appliance", "firmware": "wired-18-107-2"},
        {"serial": sw2, "name": f"{org_name}-Branch-SW", "model": "MS120-8",  "networkId": net2, "mac": "aa:bb:cc:dd:00:05", "lanIp": "10.0.1.2",     "wan1Ip": None,         "wan2Ip": None,             "lat": 52.520008, "lng": 13.404954, "address": "Berlin, Germany",  "productType": "switch",    "firmware": "switch-15-21-1"},
        {"serial": mg1, "name": f"{org_name}-HQ-MG",     "model": "MG21",     "networkId": net1, "mac": "aa:bb:cc:dd:00:07", "lanIp": "192.168.1.5",  "wan1Ip": None,         "wan2Ip": None,             "lat": 48.137154, "lng": 11.576124, "address": "Munich, Germany",  "productType": "cellularGateway", "firmware": "cellular-6-3-0"},
    ]

    device_statuses = [
        {"serial": mx1, "name": f"{org_name}-HQ-MX",     "status": "online",   "lastReportedAt": "2024-01-15T10:00:00Z", "productType": "appliance", "networkId": net1, "components": {"powerSupplies": []}},
        {"serial": sw1, "name": f"{org_name}-HQ-SW",     "status": "online",   "lastReportedAt": "2024-01-15T10:00:00Z", "productType": "switch",    "networkId": net1, "components": {"powerSupplies": [{"slot": 0, "serial": "MOCK-PSU-1", "model": "PWR-MS220-POE", "status": "connected", "poe": {"maximum": 370, "used": 120}}]}},
        {"serial": ap1, "name": f"{org_name}-HQ-AP",     "status": "online",   "lastReportedAt": "2024-01-15T10:00:00Z", "productType": "wireless",  "networkId": net1, "components": {"powerSupplies": []}},
        {"serial": mx2, "name": f"{org_name}-Branch-MX", "status": "online",   "lastReportedAt": "2024-01-15T09:55:00Z", "productType": "appliance", "networkId": net2, "components": {"powerSupplies": []}},
        {"serial": sw2, "name": f"{org_name}-Branch-SW", "status": "alerting", "lastReportedAt": "2024-01-15T09:50:00Z", "productType": "switch",    "networkId": net2, "components": {"powerSupplies": []}},
        {"serial": mg1, "name": f"{org_name}-HQ-MG",     "status": "online",   "lastReportedAt": "2024-01-15T10:00:00Z", "productType": "cellularGateway", "networkId": net1, "components": {"powerSupplies": []}},
    ]

    uplinks_loss_latency = [
        {"networkId": net1, "serial": mx1, "uplink": "wan1", "ip": "8.8.8.8", "timeSeries": [{"ts": "2024-01-15T10:00:00Z", "lossPercent": 0.0,  "latencyMs": 12.5}]},
        {"networkId": net2, "serial": mx2, "uplink": "wan1", "ip": "8.8.8.8", "timeSeries": [{"ts": "2024-01-15T10:00:00Z", "lossPercent": 2.5,  "latencyMs": 35.0}]},
        {"networkId": net2, "serial": mx2, "uplink": "wan2", "ip": "8.8.8.8", "timeSeries": [{"ts": "2024-01-15T10:00:00Z", "lossPercent": 0.0,  "latencyMs": 18.0}]},
    ]

    uplinks_addresses = [
        {
            "serial": mx1, "name": f"{org_name}-HQ-MX", "mac": "aa:bb:cc:dd:00:01",
            "network": {"id": net1}, "productType": "appliance",
            "uplinks": [{"interface": "wan1", "addresses": [{"assignmentMode": "static", "address": wan1_ip, "gateway": "203.0.113.1", "nameservers": {"addresses": ["8.8.8.8"]}}]}],
        },
        {
            "serial": mx2, "name": f"{org_name}-Branch-MX", "mac": "aa:bb:cc:dd:00:04",
            "network": {"id": net2}, "productType": "appliance",
            "uplinks": [
                {"interface": "wan1", "addresses": [{"assignmentMode": "dhcp", "address": branch_wan1, "gateway": "198.51.100.1", "nameservers": {"addresses": ["8.8.8.8"]}}]},
                {"interface": "wan2", "addresses": [{"assignmentMode": "dhcp", "address": f"{branch_wan1[:-2]}21", "gateway": "198.51.100.1", "nameservers": {"addresses": ["8.8.4.4"]}}]},
            ],
        },
    ]

    appliance_uplink_statuses = [
        {
            "networkId": net1, "serial": mx1, "model": "MX68",
            "highAvailability": {"enabled": False, "role": "not supported"},
            "lastReportedAt": "2024-01-15T10:00:00Z",
            "uplinks": [
                {"interface": "wan1",     "status": "active",        "ip": wan1_ip,     "gateway": "203.0.113.1",  "publicIp": wan1_ip,     "primaryDns": "8.8.8.8", "secondaryDns": "8.8.4.4", "ipAssignedBy": "static"},
                {"interface": "cellular", "status": "not connected", "ip": None,        "gateway": None,           "publicIp": None,        "primaryDns": None,      "secondaryDns": None,      "ipAssignedBy": "N/A"},
            ],
        },
        {
            "networkId": net2, "serial": mx2, "model": "MX65",
            "highAvailability": {"enabled": False, "role": "not supported"},
            "lastReportedAt": "2024-01-15T09:55:00Z",
            "uplinks": [
                {"interface": "wan1", "status": "active", "ip": branch_wan1,          "gateway": "198.51.100.1", "publicIp": branch_wan1,          "primaryDns": "8.8.8.8", "secondaryDns": "8.8.4.4", "ipAssignedBy": "dhcp"},
                {"interface": "wan2", "status": "active", "ip": f"{branch_wan1[:-2]}21", "gateway": "198.51.100.1", "publicIp": f"{branch_wan1[:-2]}21", "primaryDns": "8.8.4.4", "secondaryDns": "8.8.8.8", "ipAssignedBy": "dhcp"},
            ],
        },
    ]

    appliance_vpn_statuses = [
        {
            "networkId": net1, "networkName": f"{org_name}-HQ",
            "deviceSerial": mx1, "deviceStatus": "online", "vpnMode": "hub",
            "exportedSubnets": [{"name": "LAN", "subnet": "192.168.1.0/24"}],
            "merakiVpnPeers": [{"networkId": net2, "networkName": f"{org_name}-Branch", "reachability": "reachable"}],
        },
        {
            "networkId": net2, "networkName": f"{org_name}-Branch",
            "deviceSerial": mx2, "deviceStatus": "online", "vpnMode": "spoke",
            "exportedSubnets": [{"name": "LAN", "subnet": "10.0.1.0/24"}],
            "merakiVpnPeers": [{"networkId": net1, "networkName": f"{org_name}-HQ", "reachability": "reachable"}],
        },
    ]

    switch_ports = {
        sw1: [
            {"portId": "1", "name": "Server", "enabled": True,  "poeEnabled": True,  "type": "access", "vlan": 10, "voiceVlan": None, "allowedVlans": "all", "isolationEnabled": False, "rstpEnabled": True, "stpGuard": "disabled", "linkNegotiation": "Auto negotiate", "accessPolicyType": "Open", "stickyMacAllowList": [], "stickyMacAllowListLimit": 5, "stormControlEnabled": True},
            {"portId": "2", "name": "Uplink", "enabled": True,  "poeEnabled": False, "type": "trunk",  "vlan": 1,  "voiceVlan": None, "allowedVlans": "all", "isolationEnabled": False, "rstpEnabled": True, "stpGuard": "disabled", "linkNegotiation": "Auto negotiate", "accessPolicyType": "Open", "stickyMacAllowList": [], "stickyMacAllowListLimit": 5, "stormControlEnabled": False},
            {"portId": "3", "name": "AP",     "enabled": True,  "poeEnabled": True,  "type": "trunk",  "vlan": 1,  "voiceVlan": None, "allowedVlans": "all", "isolationEnabled": False, "rstpEnabled": True, "stpGuard": "disabled", "linkNegotiation": "Auto negotiate", "accessPolicyType": "Open", "stickyMacAllowList": [], "stickyMacAllowListLimit": 5, "stormControlEnabled": False},
            {"portId": "4", "name": "",       "enabled": False, "poeEnabled": False, "type": "access", "vlan": 1,  "voiceVlan": None, "allowedVlans": "all", "isolationEnabled": False, "rstpEnabled": True, "stpGuard": "disabled", "linkNegotiation": "Auto negotiate", "accessPolicyType": "Open", "stickyMacAllowList": [], "stickyMacAllowListLimit": 5, "stormControlEnabled": False},
        ],
        sw2: [
            {"portId": "1", "name": "Uplink", "enabled": True, "poeEnabled": False, "type": "trunk",  "vlan": 1,  "voiceVlan": None, "allowedVlans": "all", "isolationEnabled": False, "rstpEnabled": True, "stpGuard": "disabled", "linkNegotiation": "Auto negotiate", "accessPolicyType": "Open", "stickyMacAllowList": [], "stickyMacAllowListLimit": 5, "stormControlEnabled": False},
            {"portId": "2", "name": "PC",     "enabled": True, "poeEnabled": False, "type": "access", "vlan": 20, "voiceVlan": None, "allowedVlans": "all", "isolationEnabled": False, "rstpEnabled": True, "stpGuard": "disabled", "linkNegotiation": "Auto negotiate", "accessPolicyType": "Open", "stickyMacAllowList": [], "stickyMacAllowListLimit": 5, "stormControlEnabled": False},
        ],
    }

    switch_port_statuses = {
        sw1: [
            {"portId": "1", "enabled": True,  "status": "Connected",    "isUplink": False, "errors": [],                  "warnings": [], "speed": "1 Gbps",   "duplex": "full", "usageInKb": {"total": 102400, "sent": 51200,  "recv": 51200},  "cdp": None, "lldp": None, "clientCount": 2},
            {"portId": "2", "enabled": True,  "status": "Connected",    "isUplink": True,  "errors": [],                  "warnings": [], "speed": "1 Gbps",   "duplex": "full", "usageInKb": {"total": 512000, "sent": 256000, "recv": 256000}, "cdp": None, "lldp": None, "clientCount": 0},
            {"portId": "3", "enabled": True,  "status": "Connected",    "isUplink": False, "errors": [],                  "warnings": [], "speed": "1 Gbps",   "duplex": "full", "usageInKb": {"total": 204800, "sent": 102400, "recv": 102400}, "cdp": None, "lldp": None, "clientCount": 1},
            {"portId": "4", "enabled": False, "status": "Disconnected", "isUplink": False, "errors": [],                  "warnings": [], "speed": None,       "duplex": None,   "usageInKb": {"total": 0,      "sent": 0,     "recv": 0},     "cdp": None, "lldp": None, "clientCount": 0},
        ],
        sw2: [
            {"portId": "1", "enabled": True, "status": "Connected", "isUplink": True,  "errors": [],                  "warnings": [], "speed": "100 Mbps", "duplex": "full", "usageInKb": {"total": 10240, "sent": 5120, "recv": 5120}, "cdp": None, "lldp": None, "clientCount": 0},
            {"portId": "2", "enabled": True, "status": "Connected", "isUplink": False, "errors": ["CRC align errors"], "warnings": [], "speed": "100 Mbps", "duplex": "full", "usageInKb": {"total": 2048,  "sent": 1024, "recv": 1024}, "cdp": None, "lldp": None, "clientCount": 1},
        ],
    }

    switch_ports_by_switch = [
        {"serial": sw1, "name": f"{org_name}-HQ-SW",     "mac": "aa:bb:cc:dd:00:02", "network": {"id": net1, "name": f"{org_name}-HQ"},     "model": "MS220-8P", "ports": switch_port_statuses[sw1]},
        {"serial": sw2, "name": f"{org_name}-Branch-SW", "mac": "aa:bb:cc:dd:00:05", "network": {"id": net2, "name": f"{org_name}-Branch"}, "model": "MS120-8",  "ports": switch_port_statuses[sw2]},
    ]

    wireless_ethernet_statuses = [
        {
            "serial": ap1, "name": f"{org_name}-HQ-AP",
            "network": {"id": net1, "name": f"{org_name}-HQ"},
            "ports": [{"name": "eth0", "enabled": True, "poeEnabled": True, "speed": "1 Gbps", "duplex": "full", "linkNegotiation": {"duplex": "full", "speed": 1000}}],
            "aggregation": {"enabled": False, "speed": None},
        }
    ]

    wireless_device_status = {
        ap1: {
            "serial": ap1,
            "basicServiceSets": [
                {"ssidName": "Mock-SSID", "ssidNumber": 0, "enabled": True, "band": "2.4 GHz", "bssid": "aa:bb:cc:dd:00:10", "channel": 6,  "channelWidth": "20 MHz", "power": "18 dBm", "visible": True, "broadcasting": True},
                {"ssidName": "Mock-SSID", "ssidNumber": 0, "enabled": True, "band": "5 GHz",   "bssid": "aa:bb:cc:dd:00:11", "channel": 36, "channelWidth": "80 MHz", "power": "20 dBm", "visible": True, "broadcasting": True},
            ]
        }
    }

    appliance_performance = {
        mx1: {"perfScore": 95},
        mx2: {"perfScore": 78},
    }

    cellular_uplink_statuses = [
        {
            "serial": mg1,
            "networkId": net1,
            "model": "MG21",
            "lastReportedAt": "2024-01-15T10:00:00Z",
            "highAvailability": {"enabled": False, "role": "not supported"},
            "uplinks": [
                {
                    "interface": "cellular",
                    "status": "active",
                    "ip": "10.128.0.42",
                    "publicIp": "203.0.113.50",
                    "gateway": "10.128.0.1",
                    "dns1": "8.8.8.8",
                    "dns2": "8.8.4.4",
                    "apn": "internet",
                    "connectionType": "lte",
                    "iccid": "89014103211118510720",
                    "model": "integrated",
                    "provider": "T-Mobile",
                    "signalType": "LTE",
                    "signalStat": {"rsrp": "-95", "rsrq": "-12"},
                }
            ],
        }
    ]

    sensor_readings_latest = [
        {
            "serial": sn1,
            "network": {"id": net1, "name": f"{org_name}-HQ"},
            "readings": [
                {"ts": "2024-01-15T10:00:00Z", "metric": "temperature", "temperature": {"fahrenheit": 71.6, "celsius": 22.0}},
                {"ts": "2024-01-15T10:00:00Z", "metric": "humidity",    "humidity":    {"relativePercentage": 45}},
            ],
        }
    ]

    return {
        "org_id":                    org_id,
        "net1":                      net1,
        "net2":                      net2,
        "organizations":             organizations,
        "networks":                  networks,
        "devices":                   devices,
        "device_statuses":           device_statuses,
        "uplinks_loss_latency":      uplinks_loss_latency,
        "uplinks_addresses":         uplinks_addresses,
        "appliance_uplink_statuses": appliance_uplink_statuses,
        "appliance_vpn_statuses":    appliance_vpn_statuses,
        "switch_ports":              switch_ports,
        "switch_port_statuses":      switch_port_statuses,
        "switch_ports_by_switch":    switch_ports_by_switch,
        "wireless_ethernet_statuses": wireless_ethernet_statuses,
        "wireless_device_status":    wireless_device_status,
        "appliance_performance":     appliance_performance,
        "cellular_uplink_statuses":  cellular_uplink_statuses,
        "sensor_readings_latest":    sensor_readings_latest,
    }


# ── Tenant registry ───────────────────────────────────────────────────────────
# Add a new customer by adding an entry here and calling build_tenant().

TENANTS = {
    "key-customer-a": build_tenant(
        org_id="111111", org_name="Customer-A",
        prefix="CUSA", wan1_ip="203.0.113.10", branch_wan1="198.51.100.20",
    ),
    "key-customer-b": build_tenant(
        org_id="222222", org_name="Customer-B",
        prefix="CUSB", wan1_ip="203.0.114.10", branch_wan1="198.51.101.20",
    ),
}

# Build a flat serial→tenant lookup for device-level endpoints
_SERIAL_INDEX = {}
for _t in TENANTS.values():
    for _d in _t["devices"]:
        _SERIAL_INDEX[_d["serial"]] = _t


# ── Auth helper ───────────────────────────────────────────────────────────────

def get_tenant():
    api_key = request.headers.get("X-Cisco-Meraki-API-Key", "")
    if not api_key:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            api_key = auth[7:]
    tenant  = TENANTS.get(api_key)
    if tenant is None:
        app.logger.warning("Unknown API key: %r", api_key)
        return None, (jsonify({"errors": ["Invalid API key"]}), 401)
    return tenant, None

def log_request():
    app.logger.info("%-6s %s", request.method, request.path)


# ── Organization endpoints ────────────────────────────────────────────────────

@app.route("/api/v1/organizations")
def get_organizations():
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["organizations"])

@app.route("/api/v1/organizations/<org_id>")
def get_organization(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["organizations"][0])

@app.route("/api/v1/organizations/<org_id>/networks")
def get_networks(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["networks"])

@app.route("/api/v1/organizations/<org_id>/devices")
def get_org_devices(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["devices"])

@app.route("/api/v1/organizations/<org_id>/devices/statuses")
def get_device_statuses(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["device_statuses"])

@app.route("/api/v1/organizations/<org_id>/devices/uplinks/loss-and-latency")
def get_uplinks_loss_latency(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["uplinks_loss_latency"])

@app.route("/api/v1/organizations/<org_id>/devices/uplinks/addresses/byDevice")
def get_uplinks_addresses(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["uplinks_addresses"])

@app.route("/api/v1/organizations/<org_id>/licenses/overview")
def get_licenses_overview(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify({"status": "OK", "expirationDate": "Dec 1, 2026 UTC", "licensedDeviceCounts": {"MS": 2, "MX": 2, "MR": 1}})

@app.route("/api/v1/organizations/<org_id>/appliance/uplink/statuses")
def get_appliance_uplink_statuses(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["appliance_uplink_statuses"])

@app.route("/api/v1/organizations/<org_id>/appliance/uplinks/usage/byNetwork")
def get_appliance_uplinks_usage(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify([
        {
            "networkId": t["net1"], "networkName": t["organizations"][0]["name"] + "-HQ",
            "byUplink": [{"serial": t["devices"][0]["serial"], "interface": "wan1", "sent": random.randint(500000, 5000000), "received": random.randint(1000000, 10000000), "total": 0}],
        },
        {
            "networkId": t["net2"], "networkName": t["organizations"][0]["name"] + "-Branch",
            "byUplink": [
                {"serial": t["devices"][4]["serial"], "interface": "wan1", "sent": random.randint(200000, 2000000), "received": random.randint(400000, 4000000), "total": 0},
                {"serial": t["devices"][4]["serial"], "interface": "wan2", "sent": random.randint(100000, 1000000), "received": random.randint(200000, 2000000), "total": 0},
            ],
        },
    ])

@app.route("/api/v1/organizations/<org_id>/appliance/vpn/statuses")
def get_appliance_vpn_statuses(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["appliance_vpn_statuses"])

@app.route("/api/v1/organizations/<org_id>/switch/ports/statuses/bySwitch")
def get_switch_ports_by_switch(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify({"items": t["switch_ports_by_switch"]})

@app.route("/api/v1/organizations/<org_id>/wireless/devices/ethernet/statuses")
def get_wireless_ethernet_statuses(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["wireless_ethernet_statuses"])

@app.route("/api/v1/organizations/<org_id>/cellularGateway/uplink/statuses")
def get_cellular_uplinks(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["cellular_uplink_statuses"])

@app.route("/api/v1/organizations/<org_id>/sensor/readings/latest")
def get_sensor_readings_latest(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify(t["sensor_readings_latest"])

@app.route("/api/v1/organizations/<org_id>/apiRequests/overview/responseCodes/byInterval")
def get_api_requests_overview(org_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify([{"startTs": "2024-01-15T09:00:00Z", "endTs": "2024-01-15T10:00:00Z", "counts": [{"code": 200, "count": 142}, {"code": 404, "count": 3}]}])


# ── Network endpoints ─────────────────────────────────────────────────────────

@app.route("/api/v1/networks/<network_id>/devices")
def get_network_devices(network_id):
    log_request()
    t, err = get_tenant()
    if err: return err
    return jsonify([d for d in t["devices"] if d["networkId"] == network_id])


# ── Device endpoints (looked up by serial across all tenants) ─────────────────

@app.route("/api/v1/devices/<serial>/switch/ports")
def get_switch_ports(serial):
    log_request()
    t = _SERIAL_INDEX.get(serial)
    if not t: return jsonify([])
    return jsonify(t["switch_ports"].get(serial, []))

@app.route("/api/v1/devices/<serial>/switch/ports/statuses")
def get_switch_port_statuses(serial):
    log_request()
    t = _SERIAL_INDEX.get(serial)
    if not t: return jsonify([])
    return jsonify(t["switch_port_statuses"].get(serial, []))

@app.route("/api/v1/devices/<serial>/appliance/uplinks/settings")
def get_appliance_uplinks_settings(serial):
    log_request()
    return jsonify({"interfaces": {"wan1": {"enabled": True, "svis": {"ipv4": {"assignmentMode": "static", "address": "203.0.113.10/24", "gateway": "203.0.113.1"}}}, "wan2": {"enabled": False, "svis": {}}}})

@app.route("/api/v1/devices/<serial>/appliance/performance")
def get_appliance_performance(serial):
    log_request()
    t = _SERIAL_INDEX.get(serial)
    if not t: return jsonify({"perfScore": 100})
    return jsonify(t["appliance_performance"].get(serial, {"perfScore": 100}))

@app.route("/api/v1/devices/<serial>/wireless/status")
def get_wireless_status(serial):
    log_request()
    t = _SERIAL_INDEX.get(serial)
    if not t: return jsonify({"basicServiceSets": []})
    return jsonify(t["wireless_device_status"].get(serial, {"basicServiceSets": []}))

@app.route("/api/v1/devices/<serial>/management/interface")
def get_management_interface(serial):
    log_request()
    return jsonify({"wan1": {"wanEnabled": "enabled", "usingStaticIp": True, "staticIp": "203.0.113.10", "staticSubnetMask": "255.255.255.0", "staticGatewayIp": "203.0.113.1"}, "wan2": {"wanEnabled": "disabled", "usingStaticIp": False}})


# ── Catch-all ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def catch_all(path):
    app.logger.warning("UNIMPLEMENTED: %s /api/v1/%s", request.method, path)
    return jsonify({"errors": [f"Endpoint not implemented in mock: /api/v1/{path}"]}), 404


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
