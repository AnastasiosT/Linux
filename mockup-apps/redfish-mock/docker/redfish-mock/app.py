"""
Redfish API v1 — Mock Server
Tailored for the Checkmk built-in agent_redfish special agent (Checkmk 2.4+).

Simulates an HPE iLO5 server (covers both Generic and HPE-specific code paths).

Session authentication:
  POST   /redfish/v1/SessionService/Sessions
  GET    /redfish/v1/SessionService/Sessions
  DELETE /redfish/v1/SessionService/Sessions/<id>

Root:
  GET    /redfish/v1

Managers:
  GET    /redfish/v1/Managers
  GET    /redfish/v1/Managers/1

Systems:
  GET    /redfish/v1/Systems
  GET    /redfish/v1/Systems/1
  GET    /redfish/v1/Systems/1/Processors
  GET    /redfish/v1/Systems/1/Processors/1
  GET    /redfish/v1/Systems/1/Memory
  GET    /redfish/v1/Systems/1/Memory/1
  GET    /redfish/v1/Systems/1/EthernetInterfaces
  GET    /redfish/v1/Systems/1/EthernetInterfaces/1
  GET    /redfish/v1/Systems/1/NetworkInterfaces
  GET    /redfish/v1/Systems/1/NetworkInterfaces/1
  GET    /redfish/v1/Systems/1/Storage
  GET    /redfish/v1/Systems/1/Storage/1
  GET    /redfish/v1/Systems/1/Storage/1/Drives/0
  GET    /redfish/v1/Systems/1/Storage/1/Volumes/1

HPE SmartStorage:
  GET    /redfish/v1/Systems/1/SmartStorage
  GET    /redfish/v1/Systems/1/SmartStorage/ArrayControllers
  GET    /redfish/v1/Systems/1/SmartStorage/ArrayControllers/0
  GET    /redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/LogicalDrives
  GET    /redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/LogicalDrives/1
  GET    /redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/DiskDrives
  GET    /redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/DiskDrives/0

Chassis:
  GET    /redfish/v1/Chassis
  GET    /redfish/v1/Chassis/1
  GET    /redfish/v1/Chassis/1/Power
  GET    /redfish/v1/Chassis/1/Thermal
  GET    /redfish/v1/Chassis/1/NetworkAdapters
  GET    /redfish/v1/Chassis/1/NetworkAdapters/1

Firmware:
  GET    /redfish/v1/UpdateService
  GET    /redfish/v1/UpdateService/FirmwareInventory
  GET    /redfish/v1/resourcedirectory
"""

from flask import Flask, jsonify, request, Response
from datetime import datetime, timezone
import logging, random, uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = Flask(__name__)

# ── Active sessions ───────────────────────────────────────────────────────────
SESSIONS: dict = {}

# ── Helpers ───────────────────────────────────────────────────────────────────

def log_request():
    app.logger.info("%-6s %s", request.method, request.path)

def now_ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def rand_temp():
    return round(random.uniform(35.0, 65.0), 1)

def rand_fan():
    return random.randint(2000, 8000)

def health():
    return random.choice(["OK", "OK", "OK", "Warning"])

# ── Session endpoints ─────────────────────────────────────────────────────────

@app.route("/redfish/v1/SessionService/Sessions", methods=["GET", "POST"])
def sessions():
    log_request()
    if request.method == "POST":
        session_id = str(uuid.uuid4())[:8]
        token = str(uuid.uuid4())
        SESSIONS[session_id] = token
        resp = jsonify({
            "@odata.id": f"/redfish/v1/SessionService/Sessions/{session_id}",
            "@odata.type": "#Session.v1_0_0.Session",
            "Id": session_id,
            "Name": "User Session",
            "Description": "Manager User Session",
            "UserName": request.json.get("UserName", "admin") if request.json else "admin",
        })
        resp.headers["X-Auth-Token"] = token
        resp.headers["Location"] = f"/redfish/v1/SessionService/Sessions/{session_id}"
        resp.status_code = 201
        return resp
    return jsonify({
        "@odata.id": "/redfish/v1/SessionService/Sessions",
        "@odata.type": "#SessionCollection.SessionCollection",
        "Name": "Session Collection",
        "Members@odata.count": len(SESSIONS),
        "Members": [{"@odata.id": f"/redfish/v1/SessionService/Sessions/{s}"} for s in SESSIONS],
    })

@app.route("/redfish/v1/Sessions", methods=["GET", "POST"])
def sessions_alt():
    return sessions()

@app.route("/redfish/v1/SessionService/Sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    log_request()
    SESSIONS.pop(session_id, None)
    return Response(status=204)

@app.route("/redfish/v1/SessionService", methods=["GET"])
def session_service():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/SessionService",
        "@odata.type": "#SessionService.v1_0_0.SessionService",
        "Id": "SessionService",
        "Name": "Session Service",
        "Sessions": {"@odata.id": "/redfish/v1/SessionService/Sessions"},
    })

# ── Root ──────────────────────────────────────────────────────────────────────

@app.route("/redfish/v1", methods=["GET"])
@app.route("/redfish/v1/", methods=["GET"])
def redfish_root():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1",
        "@odata.type": "#ServiceRoot.v1_5_1.ServiceRoot",
        "Id": "RootService",
        "Name": "HPE RESTful Root Service",
        "RedfishVersion": "1.6.0",
        "UUID": "00000000-0000-0000-0000-000000000001",
        "Systems":  {"@odata.id": "/redfish/v1/Systems"},
        "Chassis":  {"@odata.id": "/redfish/v1/Chassis"},
        "Managers": {"@odata.id": "/redfish/v1/Managers"},
        "SessionService": {"@odata.id": "/redfish/v1/SessionService"},
        "UpdateService": {"@odata.id": "/redfish/v1/UpdateService"},
        "Links": {
            "Sessions": {"@odata.id": "/redfish/v1/SessionService/Sessions"},
        },
        # HPE OEM block — triggers HPE code path in agent
        "Oem": {
            "Hpe": {
                "Manager": [
                    {
                        "ManagerType": "iLO 5",
                        "ManagerFirmwareVersion": "3.06",
                        "Languages": [{"Version": "3.06"}],
                    }
                ],
                "Moniker": {"PRODGEN": "iLO 5"},
                "Links": {
                    "ResourceDirectory": {"@odata.id": "/redfish/v1/resourcedirectory"},
                },
            }
        },
        "Vendor": "Hpe",
    })

# ── Managers ──────────────────────────────────────────────────────────────────

@app.route("/redfish/v1/Managers", methods=["GET"])
def managers():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Managers",
        "@odata.type": "#ManagerCollection.ManagerCollection",
        "Name": "Manager Collection",
        "Members@odata.count": 1,
        "Members": [{"@odata.id": "/redfish/v1/Managers/1"}],
    })

@app.route("/redfish/v1/Managers/1", methods=["GET"])
def manager_1():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Managers/1",
        "@odata.type": "#Manager.v1_5_1.Manager",
        "Id": "1",
        "Name": "Manager",
        "ManagerType": "BMC",
        "FirmwareVersion": "3.06",
        "Status": {"State": "Enabled", "Health": "OK"},
        "NetworkProtocol": {"@odata.id": "/redfish/v1/Managers/1/NetworkProtocol"},
        "Links": {
            "ManagerForServers": [{"@odata.id": "/redfish/v1/Systems/1"}],
            "ManagerForChassis": [{"@odata.id": "/redfish/v1/Chassis/1"}],
        },
        "Oem": {
            "Hpe": {
                "Links": {
                    "SmartStorage": {"@odata.id": "/redfish/v1/Systems/1/SmartStorage"},
                }
            }
        },
    })

# ── Systems ───────────────────────────────────────────────────────────────────

@app.route("/redfish/v1/Systems", methods=["GET"])
def systems():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems",
        "@odata.type": "#ComputerSystemCollection.ComputerSystemCollection",
        "Name": "Computer System Collection",
        "Members@odata.count": 1,
        "Members": [{"@odata.id": "/redfish/v1/Systems/1"}],
    })

@app.route("/redfish/v1/Systems/1", methods=["GET"])
def system_1():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1",
        "@odata.type": "#ComputerSystem.v1_10_0.ComputerSystem",
        "Id": "1",
        "Name": "ProLiant DL360 Gen10",
        "SystemType": "Physical",
        "Manufacturer": "HPE",
        "Model": "ProLiant DL360 Gen10",
        "SerialNumber": "MOCK0001337",
        "PartNumber": "867959-B21",
        "BIOSVersion": "U32 v2.42 (04/22/2021)",
        "HostName": "mock-server-01",
        "PowerState": "On",
        "Status": {"State": "Enabled", "Health": "OK"},
        "MemorySummary": {
            "TotalSystemMemoryGiB": 64,
            "Status": {"Health": "OK"},
        },
        "ProcessorSummary": {
            "Count": 2,
            "Model": "Intel Xeon Gold 6226R",
            "Status": {"Health": "OK"},
        },
        "Processors":        {"@odata.id": "/redfish/v1/Systems/1/Processors"},
        "Memory":            {"@odata.id": "/redfish/v1/Systems/1/Memory"},
        "Storage":           {"@odata.id": "/redfish/v1/Systems/1/Storage"},
        "EthernetInterfaces":{"@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces"},
        "NetworkInterfaces": {"@odata.id": "/redfish/v1/Systems/1/NetworkInterfaces"},
        "Oem": {
            "Hpe": {
                "Links": {
                    "SmartStorage": {"@odata.id": "/redfish/v1/Systems/1/SmartStorage"},
                }
            }
        },
    })

# Processors

@app.route("/redfish/v1/Systems/1/Processors", methods=["GET"])
def processors():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/Processors",
        "@odata.type": "#ProcessorCollection.ProcessorCollection",
        "Name": "Processors Collection",
        "Members@odata.count": 2,
        "Members": [
            {"@odata.id": "/redfish/v1/Systems/1/Processors/1"},
            {"@odata.id": "/redfish/v1/Systems/1/Processors/2"},
        ],
    })

@app.route("/redfish/v1/Systems/1/Processors/<cpu_id>", methods=["GET"])
def processor(cpu_id):
    log_request()
    return jsonify({
        "@odata.id": f"/redfish/v1/Systems/1/Processors/{cpu_id}",
        "@odata.type": "#Processor.v1_7_2.Processor",
        "Id": cpu_id,
        "Name": f"Proc {cpu_id}",
        "ProcessorType": "CPU",
        "ProcessorArchitecture": "x86",
        "InstructionSet": "x86-64",
        "Manufacturer": "Intel Corporation",
        "Model": "Intel(R) Xeon(R) Gold 6226R CPU @ 2.90GHz",
        "MaxSpeedMHz": 4000,
        "TotalCores": 16,
        "TotalThreads": 32,
        "Socket": f"Proc {cpu_id}",
        "Status": {"State": "Enabled", "Health": "OK"},
    })

# Memory

@app.route("/redfish/v1/Systems/1/Memory", methods=["GET"])
def memory():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/Memory",
        "@odata.type": "#MemoryCollection.MemoryCollection",
        "Name": "Memory Collection",
        "Members@odata.count": 4,
        "Members": [
            {"@odata.id": f"/redfish/v1/Systems/1/Memory/{i}"} for i in range(1, 5)
        ],
    })

@app.route("/redfish/v1/Systems/1/Memory/<mem_id>", methods=["GET"])
def memory_module(mem_id):
    log_request()
    return jsonify({
        "@odata.id": f"/redfish/v1/Systems/1/Memory/{mem_id}",
        "@odata.type": "#Memory.v1_7_1.Memory",
        "Id": mem_id,
        "Name": f"PROC 1 DIMM {mem_id}A",
        "MemoryType": "DRAM",
        "MemoryDeviceType": "DDR4",
        "CapacityMiB": 16384,
        "OperatingSpeedMhz": 2933,
        "Manufacturer": "Hynix",
        "SerialNumber": f"MOCK{mem_id:04d}",
        "Status": {"State": "Enabled", "Health": "OK"},
    })

# EthernetInterfaces

@app.route("/redfish/v1/Systems/1/EthernetInterfaces", methods=["GET"])
def ethernet_interfaces():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces",
        "@odata.type": "#EthernetInterfaceCollection.EthernetInterfaceCollection",
        "Name": "System Ethernet Interfaces",
        "Members@odata.count": 2,
        "Members": [
            {"@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces/1"},
            {"@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces/2"},
        ],
    })

@app.route("/redfish/v1/Systems/1/EthernetInterfaces/<nic_id>", methods=["GET"])
def ethernet_interface(nic_id):
    log_request()
    return jsonify({
        "@odata.id": f"/redfish/v1/Systems/1/EthernetInterfaces/{nic_id}",
        "@odata.type": "#EthernetInterface.v1_4_1.EthernetInterface",
        "Id": nic_id,
        "Name": f"System Embedded NIC {nic_id} Port 1 Partition 1",
        "InterfaceEnabled": True,
        "MACAddress": f"aa:bb:cc:dd:ee:0{nic_id}",
        "SpeedMbps": 1000,
        "FullDuplex": True,
        "LinkStatus": "LinkUp",
        "Status": {"State": "Enabled", "Health": "OK"},
        "IPv4Addresses": [
            {"Address": f"192.168.1.{int(nic_id)+10}", "SubnetMask": "255.255.255.0", "AddressOrigin": "DHCP"},
        ],
    })

# NetworkInterfaces

@app.route("/redfish/v1/Systems/1/NetworkInterfaces", methods=["GET"])
def network_interfaces():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/NetworkInterfaces",
        "@odata.type": "#NetworkInterfaceCollection.NetworkInterfaceCollection",
        "Name": "Network Interface Collection",
        "Members@odata.count": 1,
        "Members": [{"@odata.id": "/redfish/v1/Systems/1/NetworkInterfaces/1"}],
    })

@app.route("/redfish/v1/Systems/1/NetworkInterfaces/<nic_id>", methods=["GET"])
def network_interface(nic_id):
    log_request()
    return jsonify({
        "@odata.id": f"/redfish/v1/Systems/1/NetworkInterfaces/{nic_id}",
        "@odata.type": "#NetworkInterface.v1_1_1.NetworkInterface",
        "Id": nic_id,
        "Name": "HPE Ethernet 1Gb 4-port 331i Adapter",
        "Status": {"State": "Enabled", "Health": "OK"},
        "NetworkPorts": {"@odata.id": f"/redfish/v1/Systems/1/NetworkInterfaces/{nic_id}/NetworkPorts"},
    })

# Storage (generic — for non-HPE path)

@app.route("/redfish/v1/Systems/1/Storage", methods=["GET"])
def storage():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/Storage",
        "@odata.type": "#StorageCollection.StorageCollection",
        "Name": "Storage Collection",
        "Members@odata.count": 1,
        "Members": [{"@odata.id": "/redfish/v1/Systems/1/Storage/1"}],
    })

@app.route("/redfish/v1/Systems/1/Storage/1", methods=["GET"])
def storage_controller():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/Storage/1",
        "@odata.type": "#Storage.v1_7_1.Storage",
        "Id": "1",
        "Name": "HPE Smart Array P408i-a SR Gen10",
        "Status": {"State": "Enabled", "Health": "OK"},
        "StorageControllers": [
            {
                "MemberId": "0",
                "Name": "HPE Smart Array P408i-a SR Gen10",
                "Manufacturer": "HPE",
                "Model": "HPE Smart Array P408i-a SR Gen10",
                "FirmwareVersion": "1.98",
                "Status": {"State": "Enabled", "Health": "OK"},
            }
        ],
        "Drives": [
            {"@odata.id": "/redfish/v1/Systems/1/Storage/1/Drives/0"},
            {"@odata.id": "/redfish/v1/Systems/1/Storage/1/Drives/1"},
        ],
        "Volumes": {"@odata.id": "/redfish/v1/Systems/1/Storage/1/Volumes"},
    })

@app.route("/redfish/v1/Systems/1/Storage/1/Drives/<drive_id>", methods=["GET"])
def drive(drive_id):
    log_request()
    return jsonify({
        "@odata.id": f"/redfish/v1/Systems/1/Storage/1/Drives/{drive_id}",
        "@odata.type": "#Drive.v1_7_0.Drive",
        "Id": drive_id,
        "Name": f"Drive {drive_id}",
        "MediaType": "HDD",
        "Protocol": "SAS",
        "Manufacturer": "SEAGATE",
        "Model": "EG001200JWJNP",
        "SerialNumber": f"MOCK{drive_id}SN001",
        "CapacityBytes": 1200000000000,
        "RotationSpeedRPM": 10000,
        "Status": {"State": "Enabled", "Health": "OK"},
    })

@app.route("/redfish/v1/Systems/1/Storage/1/Volumes", methods=["GET"])
def volumes():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/Storage/1/Volumes",
        "@odata.type": "#VolumeCollection.VolumeCollection",
        "Name": "Volume Collection",
        "Members@odata.count": 1,
        "Members": [{"@odata.id": "/redfish/v1/Systems/1/Storage/1/Volumes/1"}],
    })

@app.route("/redfish/v1/Systems/1/Storage/1/Volumes/1", methods=["GET"])
def volume_1():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/Storage/1/Volumes/1",
        "@odata.type": "#Volume.v1_4_1.Volume",
        "Id": "1",
        "Name": "OS Volume",
        "VolumeType": "Mirrored",
        "RAIDType": "RAID1",
        "CapacityBytes": 1199000000000,
        "Status": {"State": "Enabled", "Health": "OK"},
    })

# ── HPE SmartStorage ──────────────────────────────────────────────────────────

@app.route("/redfish/v1/Systems/1/SmartStorage", methods=["GET"])
def smart_storage():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/SmartStorage",
        "@odata.type": "#HpeSmartStorage.v2_0_0.HpeSmartStorage",
        "Id": "SmartStorage",
        "Name": "HPE Smart Storage",
        "Status": {"State": "Enabled", "Health": "OK"},
        "Links": {
            "ArrayControllers":  {"@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers"},
            "HostBusAdapters":   {"@odata.id": "/redfish/v1/Systems/1/SmartStorage/HostBusAdapters"},
        },
    })

@app.route("/redfish/v1/Systems/1/SmartStorage/ArrayControllers", methods=["GET"])
def array_controllers():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers",
        "@odata.type": "#HpeSmartStorageArrayControllerCollection.HpeSmartStorageArrayControllerCollection",
        "Name": "HpSmartStorage Array Controllers Collection",
        "Members@odata.count": 1,
        "Members": [{"@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0"}],
    })

@app.route("/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0", methods=["GET"])
def array_controller_0():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0",
        "@odata.type": "#HpeSmartStorageArrayController.v2_2_0.HpeSmartStorageArrayController",
        "Id": "0",
        "Name": "HPE Smart Array P408i-a SR Gen10",
        "Model": "HPE Smart Array P408i-a SR Gen10",
        "SerialNumber": "MOCKCTRL001",
        "FirmwareVersion": {"Current": {"VersionString": "1.98"}},
        "Status": {"State": "Enabled", "Health": "OK"},
        "Links": {
            "LogicalDrives": {"@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/LogicalDrives"},
            "PhysicalDrives": {"@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/DiskDrives"},
        },
    })

@app.route("/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/LogicalDrives", methods=["GET"])
def logical_drives():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/LogicalDrives",
        "@odata.type": "#HpeSmartStorageLogicalDriveCollection.HpeSmartStorageLogicalDriveCollection",
        "Name": "HpSmartStorage LogicalDrives Collection",
        "Members@odata.count": 1,
        "Members": [{"@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/LogicalDrives/1"}],
    })

@app.route("/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/LogicalDrives/1", methods=["GET"])
def logical_drive_1():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/LogicalDrives/1",
        "@odata.type": "#HpeSmartStorageLogicalDrive.v2_3_0.HpeSmartStorageLogicalDrive",
        "Id": "1",
        "Name": "HpSmartStorageLogicalDrive",
        "LogicalDriveNumber": 1,
        "Raid": "Raid1",
        "CapacityMiB": 1144064,
        "Status": {"State": "Enabled", "Health": "OK"},
        "VolumeUniqueIdentifier": "MOCKLD001",
    })

@app.route("/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/DiskDrives", methods=["GET"])
def disk_drives():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/DiskDrives",
        "@odata.type": "#HpeSmartStorageDiskDriveCollection.HpeSmartStorageDiskDriveCollection",
        "Name": "HpSmartStorage Disk Drives Collection",
        "Members@odata.count": 2,
        "Members": [
            {"@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/DiskDrives/0"},
            {"@odata.id": "/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/DiskDrives/1"},
        ],
    })

@app.route("/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/DiskDrives/<disk_id>", methods=["GET"])
def disk_drive(disk_id):
    log_request()
    return jsonify({
        "@odata.id": f"/redfish/v1/Systems/1/SmartStorage/ArrayControllers/0/DiskDrives/{disk_id}",
        "@odata.type": "#HpeSmartStorageDiskDrive.v2_1_0.HpeSmartStorageDiskDrive",
        "Id": disk_id,
        "Name": "HpSmartStorageDiskDrive",
        "Model": "EG001200JWJNP",
        "SerialNumber": f"MOCKDISK{disk_id}001",
        "CapacityMiB": 1144064,
        "MediaType": "HDD",
        "InterfaceType": "SAS",
        "RotationalSpeedRpm": 10000,
        "Status": {"State": "Enabled", "Health": "OK"},
    })

@app.route("/redfish/v1/Systems/1/SmartStorage/HostBusAdapters", methods=["GET"])
def host_bus_adapters():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Systems/1/SmartStorage/HostBusAdapters",
        "@odata.type": "#HpeSmartStorageHostBusAdapterCollection.HpeSmartStorageHostBusAdapterCollection",
        "Name": "HpSmartStorage HostBusAdapters Collection",
        "Members@odata.count": 0,
        "Members": [],
    })

# ── Chassis ───────────────────────────────────────────────────────────────────

@app.route("/redfish/v1/Chassis", methods=["GET"])
def chassis():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Chassis",
        "@odata.type": "#ChassisCollection.ChassisCollection",
        "Name": "Computer System Chassis",
        "Members@odata.count": 1,
        "Members": [{"@odata.id": "/redfish/v1/Chassis/1"}],
    })

@app.route("/redfish/v1/Chassis/1", methods=["GET"])
def chassis_1():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Chassis/1",
        "@odata.type": "#Chassis.v1_10_2.Chassis",
        "Id": "1",
        "Name": "Computer System Chassis",
        "ChassisType": "RackMount",
        "Manufacturer": "HPE",
        "Model": "ProLiant DL360 Gen10",
        "SerialNumber": "MOCK0001337",
        "Status": {"State": "Enabled", "Health": "OK"},
        "Power":           {"@odata.id": "/redfish/v1/Chassis/1/Power"},
        "Thermal":         {"@odata.id": "/redfish/v1/Chassis/1/Thermal"},
        "NetworkAdapters": {"@odata.id": "/redfish/v1/Chassis/1/NetworkAdapters"},
    })

# Power

@app.route("/redfish/v1/Chassis/1/Power", methods=["GET"])
def power():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Chassis/1/Power",
        "@odata.type": "#Power.v1_3_0.Power",
        "Id": "Power",
        "Name": "Power",
        "PowerControl": [
            {
                "MemberId": "0",
                "Name": "Server Power Control",
                "PowerConsumedWatts": random.randint(180, 320),
                "PowerCapacityWatts": 800,
                "PowerMetrics": {
                    "MinConsumedWatts": 160,
                    "MaxConsumedWatts": 400,
                    "AverageConsumedWatts": random.randint(200, 280),
                },
                "Status": {"State": "Enabled", "Health": "OK"},
            }
        ],
        "PowerSupplies": [
            {
                "MemberId": "0",
                "Name": "HpeServerPowerSupply",
                "PowerSupplyType": "AC",
                "LineInputVoltage": random.randint(228, 232),
                "LineInputVoltageType": "ACHighLine",
                "PowerCapacityWatts": 800,
                "LastPowerOutputWatts": random.randint(90, 160),
                "FirmwareVersion": "1.00",
                "Manufacturer": "CHCNY",
                "Model": "865414-B21",
                "SerialNumber": "MOCKPSU0001",
                "Status": {"State": "Enabled", "Health": "OK"},
            },
            {
                "MemberId": "1",
                "Name": "HpeServerPowerSupply",
                "PowerSupplyType": "AC",
                "LineInputVoltage": random.randint(228, 232),
                "LineInputVoltageType": "ACHighLine",
                "PowerCapacityWatts": 800,
                "LastPowerOutputWatts": random.randint(90, 160),
                "FirmwareVersion": "1.00",
                "Manufacturer": "CHCNY",
                "Model": "865414-B21",
                "SerialNumber": "MOCKPSU0002",
                "Status": {"State": "Enabled", "Health": "OK"},
            },
        ],
        "Voltages": [
            {
                "MemberId": "0",
                "Name": "VR P1 Vcore",
                "ReadingVolts": round(random.uniform(1.78, 1.82), 2),
                "UpperThresholdCritical": 2.0,
                "LowerThresholdCritical": 1.5,
                "Status": {"State": "Enabled", "Health": "OK"},
            },
            {
                "MemberId": "1",
                "Name": "VR P2 Vcore",
                "ReadingVolts": round(random.uniform(1.78, 1.82), 2),
                "UpperThresholdCritical": 2.0,
                "LowerThresholdCritical": 1.5,
                "Status": {"State": "Enabled", "Health": "OK"},
            },
        ],
    })

# Thermal

@app.route("/redfish/v1/Chassis/1/Thermal", methods=["GET"])
def thermal():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Chassis/1/Thermal",
        "@odata.type": "#Thermal.v1_5_0.Thermal",
        "Id": "Thermal",
        "Name": "Thermal",
        "Temperatures": [
            {
                "MemberId": "0",
                "Name": "01-Inlet Ambient",
                "ReadingCelsius": rand_temp(),
                "UpperThresholdCritical": 42,
                "UpperThresholdFatal": 46,
                "Status": {"State": "Enabled", "Health": "OK"},
            },
            {
                "MemberId": "1",
                "Name": "02-CPU 1",
                "ReadingCelsius": rand_temp(),
                "UpperThresholdCritical": 70,
                "UpperThresholdFatal": 80,
                "Status": {"State": "Enabled", "Health": "OK"},
            },
            {
                "MemberId": "2",
                "Name": "03-CPU 2",
                "ReadingCelsius": rand_temp(),
                "UpperThresholdCritical": 70,
                "UpperThresholdFatal": 80,
                "Status": {"State": "Enabled", "Health": "OK"},
            },
            {
                "MemberId": "3",
                "Name": "04-P1 DIMM 1-6",
                "ReadingCelsius": rand_temp(),
                "UpperThresholdCritical": 87,
                "Status": {"State": "Enabled", "Health": "OK"},
            },
            {
                "MemberId": "4",
                "Name": "14-LiquidCooling Inlet",
                "ReadingCelsius": rand_temp(),
                "UpperThresholdCritical": 55,
                "Status": {"State": "Enabled", "Health": "OK"},
            },
        ],
        "Fans": [
            {
                "MemberId": "0",
                "Name": "Fan 1",
                "Reading": rand_fan(),
                "ReadingUnits": "RPM",
                "UpperThresholdFatal": 15000,
                "LowerThresholdCritical": 500,
                "Status": {"State": "Enabled", "Health": "OK"},
            },
            {
                "MemberId": "1",
                "Name": "Fan 2",
                "Reading": rand_fan(),
                "ReadingUnits": "RPM",
                "UpperThresholdFatal": 15000,
                "LowerThresholdCritical": 500,
                "Status": {"State": "Enabled", "Health": "OK"},
            },
            {
                "MemberId": "2",
                "Name": "Fan 3",
                "Reading": rand_fan(),
                "ReadingUnits": "RPM",
                "UpperThresholdFatal": 15000,
                "LowerThresholdCritical": 500,
                "Status": {"State": "Enabled", "Health": "OK"},
            },
        ],
    })

# NetworkAdapters

@app.route("/redfish/v1/Chassis/1/NetworkAdapters", methods=["GET"])
def network_adapters():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Chassis/1/NetworkAdapters",
        "@odata.type": "#NetworkAdapterCollection.NetworkAdapterCollection",
        "Name": "Network Adapter Collection",
        "Members@odata.count": 1,
        "Members": [{"@odata.id": "/redfish/v1/Chassis/1/NetworkAdapters/1"}],
    })

@app.route("/redfish/v1/Chassis/1/NetworkAdapters/1", methods=["GET"])
def network_adapter_1():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/Chassis/1/NetworkAdapters/1",
        "@odata.type": "#NetworkAdapter.v1_2_0.NetworkAdapter",
        "Id": "1",
        "Name": "HPE Ethernet 1Gb 4-port 331i Adapter",
        "Manufacturer": "HPE",
        "Model": "HPE Ethernet 1Gb 4-port 331i Adapter - NIC",
        "SerialNumber": "MOCKNIC0001",
        "Status": {"State": "Enabled", "Health": "OK"},
        "Controllers": [
            {
                "FirmwarePackageVersion": "20.14.58",
                "ControllerCapabilities": {"NetworkPortCount": 4},
            }
        ],
    })

# ── Firmware / UpdateService ──────────────────────────────────────────────────

@app.route("/redfish/v1/UpdateService", methods=["GET"])
def update_service():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/UpdateService",
        "@odata.type": "#UpdateService.v1_1_1.UpdateService",
        "Id": "UpdateService",
        "Name": "Update Service",
        "FirmwareInventory": {"@odata.id": "/redfish/v1/UpdateService/FirmwareInventory"},
        "SoftwareInventory": {"@odata.id": "/redfish/v1/UpdateService/SoftwareInventory"},
    })

@app.route("/redfish/v1/UpdateService/FirmwareInventory", methods=["GET"])
def firmware_inventory():
    log_request()
    members = [
        {"@odata.id": "/redfish/v1/UpdateService/FirmwareInventory/iLO",        "@odata.type": "#SoftwareInventory.v1_2_0.SoftwareInventory", "Id": "iLO",        "Name": "iLO 5",                                    "Version": "3.06",     "Updateable": True,  "Status": {"State": "Enabled", "Health": "OK"}},
        {"@odata.id": "/redfish/v1/UpdateService/FirmwareInventory/BIOS",        "@odata.type": "#SoftwareInventory.v1_2_0.SoftwareInventory", "Id": "BIOS",       "Name": "System BIOS",                              "Version": "U32 v2.42","Updateable": True,  "Status": {"State": "Enabled", "Health": "OK"}},
        {"@odata.id": "/redfish/v1/UpdateService/FirmwareInventory/NIC",         "@odata.type": "#SoftwareInventory.v1_2_0.SoftwareInventory", "Id": "NIC",        "Name": "HPE Ethernet 1Gb 4-port 331i Adapter",     "Version": "20.14.58", "Updateable": True,  "Status": {"State": "Enabled", "Health": "OK"}},
        {"@odata.id": "/redfish/v1/UpdateService/FirmwareInventory/SmartArray",  "@odata.type": "#SoftwareInventory.v1_2_0.SoftwareInventory", "Id": "SmartArray", "Name": "HPE Smart Array P408i-a SR Gen10",          "Version": "1.98",     "Updateable": True,  "Status": {"State": "Enabled", "Health": "OK"}},
    ]
    # Return embedded members when $expand is requested
    if request.args.get("$expand") or request.args.get("%24expand"):
        return jsonify({
            "@odata.id": "/redfish/v1/UpdateService/FirmwareInventory",
            "@odata.type": "#SoftwareInventoryCollection.SoftwareInventoryCollection",
            "Name": "Firmware Inventory Collection",
            "Members@odata.count": len(members),
            "Members": members,
        })
    return jsonify({
        "@odata.id": "/redfish/v1/UpdateService/FirmwareInventory",
        "@odata.type": "#SoftwareInventoryCollection.SoftwareInventoryCollection",
        "Name": "Firmware Inventory Collection",
        "Members@odata.count": len(members),
        "Members": [{"@odata.id": m["@odata.id"]} for m in members],
    })

@app.route("/redfish/v1/UpdateService/FirmwareInventory/<fw_id>", methods=["GET"])
def firmware_item(fw_id):
    log_request()
    fw_map = {
        "iLO":        ("iLO 5", "3.06"),
        "BIOS":       ("System BIOS", "U32 v2.42"),
        "NIC":        ("HPE Ethernet 1Gb 4-port 331i Adapter", "20.14.58"),
        "SmartArray": ("HPE Smart Array P408i-a SR Gen10", "1.98"),
    }
    name, version = fw_map.get(fw_id, (fw_id, "1.00"))
    return jsonify({
        "@odata.id": f"/redfish/v1/UpdateService/FirmwareInventory/{fw_id}",
        "@odata.type": "#SoftwareInventory.v1_2_0.SoftwareInventory",
        "Id": fw_id,
        "Name": name,
        "Version": version,
        "Updateable": True,
        "Status": {"State": "Enabled", "Health": "OK"},
    })

# HPE ResourceDirectory (iLO firmware path)

@app.route("/redfish/v1/resourcedirectory", methods=["GET"])
def resource_directory():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/resourcedirectory",
        "@odata.type": "#HpeiLOResourceDirectory.v2_0_0.HpeiLOResourceDirectory",
        "Id": "resourcedirectory",
        "Name": "Resource Directory",
        "Instances": [
            {
                "@odata.id": "/redfish/v1/UpdateService/FirmwareInventory",
                "@odata.type": "#FirmwareInventory.FirmwareInventory",
            },
        ],
    })

@app.route("/redfish/v1/UpdateService/SoftwareInventory", methods=["GET"])
def software_inventory():
    log_request()
    return jsonify({
        "@odata.id": "/redfish/v1/UpdateService/SoftwareInventory",
        "@odata.type": "#SoftwareInventoryCollection.SoftwareInventoryCollection",
        "Name": "Software Inventory Collection",
        "Members@odata.count": 0,
        "Members": [],
    })

# ── Catch-all ─────────────────────────────────────────────────────────────────

@app.route("/redfish/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def catch_all(path):
    app.logger.warning("UNIMPLEMENTED: %s /redfish/%s", request.method, path)
    return jsonify({
        "error": {
            "code": "Base.1.0.ResourceNotFound",
            "message": f"Endpoint not implemented in mock: /redfish/{path}",
        }
    }), 404

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
