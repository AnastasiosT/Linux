# Distributed Tracing

## Architecture

```
┌─────────────────────┐
│  demo-app frontend  │  Flask app, auto-instrumented, port 5000
│  demo-app backend   │  Flask app, auto-instrumented, port 5001
└────────┬────────────┘
         │ OTLP gRPC → :4317
         ▼
┌─────────────────────┐
│   otel-collector    │  traces pipeline
└────────┬────────────┘
         │ OTLP gRPC → :4417
         ▼
┌─────────────────────┐
│      Checkmk        │  receives + forwards to built-in Jaeger
│   Jaeger UI :16690  │
└─────────────────────┘
```

## Services Sending Traces

| Service    | Port | Description                        |
|------------|------|------------------------------------|
| `frontend` | 5000 | Receives orders, calls backend     |
| `backend`  | 5001 | Inventory checks, order processing |

## Viewing Traces

Open Checkmk's built-in Jaeger UI: `http://<checkmk-host>:16690`

- Select a service from the dropdown
- Click **Find Traces**
- Click any trace to see the full span tree

## Trace Flow (demo-app)

```
frontend: create-order
  └─ GET /inventory        → backend: db.query.inventory
  └─ POST /process-order   → backend: db.write.order
```

Each span includes attributes like `order.item`, `order.user`, `db.statement`, `order.id`.

10% of orders trigger a simulated payment gateway error (503) — visible as error spans.

## Adding Your Own App

Send traces to `http://192.168.121.100:4317` (gRPC) or `:4318` (HTTP) using any OTel SDK.

Minimal Python example:
```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="192.168.121.100:4317", insecure=True))
)
```

## Collector Config

Active config: `otel-collector-config.yaml_withlogs` (deployed as `otel-collector-config.yaml`)

Traces pipeline:
```
receivers:  [otlp]
processors: [memory_limiter, resource, batch]
exporters:  [debug, otlp_grpc/checkmk-traces]
```

`__CHECKMK_TRACES_ENDPOINT__` is replaced by the Vagrantfile provisioner with `<gateway>:4417`
