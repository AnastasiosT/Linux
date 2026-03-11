import os
import random
import time
import uuid

from flask import Flask, request, jsonify
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import StatusCode

# ── OTel setup ────────────────────────────────────────────────────────────────
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

resource = Resource.create({"service.name": "backend"})

# Traces
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True))
)
trace.set_tracer_provider(trace_provider)

# Metrics (exported every 30 s)
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True),
    export_interval_millis=30_000,
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

tracer = trace.get_tracer(__name__)
meter  = metrics.get_meter(__name__)

# ── Simulated inventory ───────────────────────────────────────────────────────
INVENTORY = {
    "laptop":     5,
    "phone":      12,
    "tablet":     0,   # always out of stock
    "headphones": 8,
    "keyboard":   15,
    "monitor":    3,
    "mouse":      20,
}

# ── Metrics instruments ───────────────────────────────────────────────────────
db_query_duration = meter.create_histogram(
    "db.query.duration_ms",
    description="Simulated DB query duration in milliseconds",
    unit="ms",
)
orders_processed = meter.create_counter(
    "orders.processed.total",
    description="Total orders processed by the backend",
)

# Observable gauge: reports current stock level for each item every export cycle
def observe_inventory(options):
    for item, qty in INVENTORY.items():
        yield metrics.Observation(qty, {"item": item})

meter.create_observable_gauge(
    "inventory.stock",
    callbacks=[observe_inventory],
    description="Current stock level per item",
)

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/inventory")
def get_inventory():
    item = request.args.get("item", "unknown")
    t0   = time.time()

    with tracer.start_as_current_span("db.query.inventory") as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.operation", "SELECT")
        span.set_attribute("db.statement",
            f"SELECT quantity FROM inventory WHERE item = '{item}'")
        span.set_attribute("inventory.item", item)

        time.sleep(random.uniform(0.05, 0.20))  # simulate DB latency

        available = INVENTORY.get(item, 0)
        span.set_attribute("inventory.available", available)

    db_query_duration.record((time.time() - t0) * 1000, {"operation": "SELECT", "table": "inventory"})
    return jsonify({"item": item, "available": available})


@app.route("/process-order", methods=["POST"])
def process_order():
    data     = request.json or {}
    item     = data.get("item", "unknown")
    user     = data.get("user", "anonymous")
    quantity = data.get("quantity", 1)
    t0       = time.time()

    with tracer.start_as_current_span("db.write.order") as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.operation", "INSERT")
        span.set_attribute("db.statement",
            f"INSERT INTO orders (item, user, quantity) VALUES ('{item}', '{user}', {quantity})")
        span.set_attribute("order.item", item)
        span.set_attribute("order.user", user)

        time.sleep(random.uniform(0.10, 0.30))  # simulate processing

        # 10 % payment gateway error
        if random.random() < 0.10:
            err = "Payment gateway timeout"
            span.record_exception(Exception(err))
            span.set_status(StatusCode.ERROR, err)
            orders_processed.add(1, {"item": item, "status": "error"})
            db_query_duration.record((time.time() - t0) * 1000,
                                     {"operation": "INSERT", "table": "orders"})
            return jsonify({"error": err}), 503

        if item in INVENTORY and INVENTORY[item] > 0:
            INVENTORY[item] -= quantity

        order_id = str(uuid.uuid4())[:8].upper()
        span.set_attribute("order.id", order_id)

    orders_processed.add(1, {"item": item, "status": "success"})
    db_query_duration.record((time.time() - t0) * 1000,
                             {"operation": "INSERT", "table": "orders"})
    return jsonify({"order_id": order_id, "status": "processed", "item": item})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "backend"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
