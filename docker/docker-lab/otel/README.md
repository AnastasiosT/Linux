# OpenTelemetry Metrics Collection for Checkmk

This setup collects system metrics using Docker containers and sends them to Checkmk's OpenTelemetry receiver.

## Overview

```
┌─────────────────┐
│ node-exporter   │  Collects system metrics (CPU, memory, disk, network)
│  (port 9100)    │
└────────┬────────┘
         │ scrapes every 30s
         ▼
┌─────────────────┐
│ otel-collector  │  Scrapes & processes metrics
│                 │
└────────┬────────┘
         │ forwards via gRPC
         ▼
┌─────────────────┐
│ Checkmk Server  │  Receives & monitors metrics
│  (port 4317)    │
└─────────────────┘
```

## Prerequisites

- Docker and Docker Compose installed
- Checkmk server with OpenTelemetry receiver enabled
- Network connectivity between Docker host and Checkmk server

## Quick Start

### 1. Download the Configuration Files

You need these 2 files:
- `docker-compose.yml`
- `otel-collector-config.yaml`

### 2. Configure the Checkmk Endpoint

Edit `otel-collector-config.yaml` and update line 42:

```yaml
exporters:
  otlp/checkmk:
    endpoint: "YOUR_CHECKMK_IP:4317"  # Change this!
```

**Examples:**
- If Checkmk is on the same machine: `192.168.1.100:4317`
- If Checkmk is on another server: `checkmk.example.com:4317`

### 3. Enable Checkmk's OpenTelemetry Receiver

In Checkmk Web UI:

1. Go to **Setup → Agents → Other integrations → OpenTelemetry**
2. Add a new rule:
   - **Port**: `4317`
   - **Protocol**: `gRPC`
   - **Enabled**: ✓
3. **Save**
4. Click **Activate Changes** (very important!)

Verify Checkmk is listening:
```bash
sudo ss -tulpn | grep 4317
# Should show: tcp LISTEN 0 4096 *:4317
```

### 4. Start the Containers

```bash
cd /path/to/docker/otel
docker-compose up -d
```

### 5. Verify It's Working

Check the logs:
```bash
docker logs -f otel-collector
```

You should see:
- ✅ "Everything is ready. Begin running and processing data."
- ✅ No "connection refused" errors
- ✅ Metrics being scraped and exported

### 6. Create a Host in Checkmk

In Checkmk Web UI:

1. **Setup → Hosts → Add host**
2. Configure:
   - **Hostname**: `docker-metrics-collector`
   - **IP Address**: Can leave as 127.0.0.1 or empty
   - **Monitoring agents**: Select "OpenTelemetry"
     - **Host name resource attribute**: `service.name`
     - **Host name**: `docker-metrics-collector`
3. **Save**
4. Click **Run service discovery** → **Full scan**
5. **Accept all** discovered services
6. **Activate Changes**

## What Metrics You'll Get

After service discovery, you'll see these services in Checkmk:

### CPU Metrics
- `system.cpu.load_average.1m` - 1 minute load average
- `system.cpu.load_average.5m` - 5 minute load average
- `system.cpu.load_average.15m` - 15 minute load average
- `system.cpu.time` - CPU time per core and state

### Memory Metrics
- `system.memory.usage` - Memory usage by state (used, free, cached, etc.)

### Disk Metrics (per disk)
- `system.disk.io` - Bytes read/written
- `system.disk.operations` - Read/write operations
- `system.disk.operation_time` - Time spent in I/O
- `system.disk.io_time` - Disk active time
- `system.disk.weighted_io_time` - Weighted I/O time
- `system.disk.merged` - Merged operations
- `system.disk.pending_operations` - Queue size

### Network Metrics (per interface)
- `system.network.io` - Bytes transmitted/received
- `system.network.packets` - Packets transmitted/received
- `system.network.errors` - Network errors
- `system.network.dropped` - Dropped packets
- `system.network.connections` - Active connections

### Filesystem Metrics (per mount point)
- `system.filesystem.usage` - Bytes used
- `system.filesystem.inodes.usage` - Inodes used

## Troubleshooting

### Connection Refused Errors

**Problem:** Collector logs show `connection refused`

**Solution:**
```bash
# Check if Checkmk is listening on port 4317
sudo ss -tulpn | grep 4317

# If not, restart Checkmk (replace SITENAME)
sudo omd restart SITENAME

# Check Docker collector logs
docker logs otel-collector | tail -n 50
```

### No Metrics in Checkmk

**Problem:** Services discovered but showing no data

**Check:**
1. Verify metrics are being collected:
   ```bash
   # Should show system metrics
   docker logs otel-collector | grep "system.cpu\|system.memory"
   ```

2. Check export logs:
   ```bash
   docker logs otel-collector | grep -i "export"
   ```

3. Re-run service discovery in Checkmk

### High Cardinality Warnings

**Problem:** Checkmk shows warnings like "cardinality exceeds 20"

**Explanation:** You have many CPU cores, disks, or network interfaces. Checkmk aggregates them automatically.

**Solution (optional):** Filter specific data points - see "Advanced Configuration" below.

### Port Conflicts

**Problem:** Error `bind: address already in use`

**Solution:**
```bash
# Check what's using the port
sudo lsof -i :4317

# If it's an old Checkmk instance
sudo omd restart SITENAME

# If it's Docker
docker-compose down
docker-compose up -d
```

## Commands Reference

### Start/Stop Containers
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker logs -f otel-collector
docker logs -f node-exporter
```

### Check Container Status
```bash
# List running containers
docker-compose ps

# Check resource usage
docker stats otel-collector node-exporter

# View metrics being exported
docker logs otel-collector | tail -n 100
```

### Checkmk Commands
```bash
# Check Checkmk site status
omd status SITENAME

# Restart Checkmk
sudo omd restart SITENAME

# View Checkmk OTel collector logs
sudo tail -f /omd/sites/SITENAME/var/log/otelcol.log
```

## Advanced Configuration

### Filtering CPU Cores

If you want to reduce the number of CPU cores monitored (e.g., only monitor cpu0-cpu3):

Edit `otel-collector-config.yaml` and add this processor:

```yaml
processors:
  filter/reduce_cpus:
    metrics:
      datapoint:
        # Keep only cpu0, cpu1, cpu2, cpu3
        - 'name == "system.cpu.time" and not (attributes["cpu"] == "cpu0" or attributes["cpu"] == "cpu1" or attributes["cpu"] == "cpu2" or attributes["cpu"] == "cpu3")'
  
  batch:
    timeout: 10s
  
  resource:
    # existing config...

service:
  pipelines:
    metrics:
      receivers:
        - prometheus
        - hostmetrics
      processors:
        - filter/reduce_cpus  # Add this line
        - resource
        - batch
      exporters:
        - debug
        - otlp/checkmk
```

Then restart:
```bash
docker-compose restart otel-collector
```

### Filtering Specific Disks

To only monitor specific disks (e.g., sda and sdb):

```yaml
processors:
  filter/specific_disks:
    metrics:
      datapoint:
        # Drop all disk metrics except sda and sdb
        - 'IsMatch(name, "system.disk.*") and not (attributes["device"] == "sda" or attributes["device"] == "sdb")'
```

### Changing Collection Interval

Edit `otel-collector-config.yaml`:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: node-exporter
          scrape_interval: 60s  # Change from 30s to 60s
  
  hostmetrics:
    collection_interval: 60s  # Change from 30s to 60s
```

## Architecture Details

### Container: node-exporter
- **Image:** `prom/node-exporter:latest`
- **Purpose:** Collects system-level metrics from the host machine
- **Exports:** Prometheus-format metrics on port 9100
- **Metrics:** CPU, memory, disk, network, filesystem, load average

### Container: otel-collector
- **Image:** `otel/opentelemetry-collector-contrib:latest`
- **Purpose:** Scrapes metrics and forwards them to Checkmk
- **Network Mode:** `host` (to access Checkmk on the same machine)
- **Components:**
  - **Receivers:** Scrapes node-exporter (prometheus) and collects host metrics
  - **Processors:** Adds resource attributes, batches metrics
  - **Exporters:** Sends to Checkmk via OTLP gRPC

### Resource Attributes Set
```yaml
service.name: docker-metrics-collector
deployment.environment: testing
host.name: docker-host
```

## File Structure

```
/path/to/docker/otel/
├── docker-compose.yml          # Container definitions
├── otel-collector-config.yaml  # OTel collector configuration
└── README.md                   # This file
```

## Security Notes

- The OTel collector sends data **unencrypted** (TLS disabled)
- If Checkmk requires TLS, update the exporter config:
  ```yaml
  exporters:
    otlp/checkmk:
      endpoint: "checkmk.example.com:4317"
      tls:
        insecure: false
        cert_file: /path/to/cert.pem
        key_file: /path/to/key.pem
  ```

## Updating

### Update Container Images
```bash
docker-compose pull
docker-compose up -d
```

### Update Configuration
```bash
# Edit config
nano otel-collector-config.yaml

# Restart to apply changes
docker-compose restart otel-collector
```

## Support

### Useful Resources
- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)
- [Checkmk OpenTelemetry Integration](https://docs.checkmk.com/latest/en/opentelemetry.html)
- [Node Exporter Documentation](https://github.com/prometheus/node_exporter)

### Common Issues
1. **Connection refused** → Checkmk OTel receiver not enabled or not listening
2. **No metrics** → Check collector logs, verify scraping is working
3. **High cardinality** → Normal for many cores/disks, can filter if needed
4. **Port conflicts** → Restart Checkmk, check for duplicate containers

## Maintenance

### Regular Checks
- Monitor collector logs for errors: `docker logs otel-collector | grep -i error`
- Verify services are green in Checkmk
- Check disk space usage on Docker host

### Cleanup Old Logs
```bash
# Clear Docker logs
docker-compose down
docker system prune -f
docker-compose up -d
```

---

**Questions?** Contact your monitoring team or check the Checkmk documentation.
