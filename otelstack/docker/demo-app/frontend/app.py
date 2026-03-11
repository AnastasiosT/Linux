import os
import random
import time
import threading

import requests
from flask import Flask, request, jsonify
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import StatusCode

# ── OTel setup ────────────────────────────────────────────────────────────────
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

resource = Resource.create({"service.name": "frontend"})

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
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)
meter  = metrics.get_meter(__name__)

# ── Metrics instruments ───────────────────────────────────────────────────────
orders_counter = meter.create_counter(
    "orders.total",
    description="Total number of orders attempted",
)
order_duration = meter.create_histogram(
    "orders.duration_ms",
    description="End-to-end order duration in milliseconds",
    unit="ms",
)

# ── Config ────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5001")
ITEMS = ["laptop", "phone", "tablet", "headphones", "keyboard", "monitor", "mouse"]

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/order")
def create_order():
    item = request.args.get("item", random.choice(ITEMS))
    user = f"user-{random.randint(1, 50)}"
    t0   = time.time()

    with tracer.start_as_current_span("create-order") as span:
        span.set_attribute("order.item", item)
        span.set_attribute("order.user", user)

        try:
            inv = requests.get(
                f"{BACKEND_URL}/inventory",
                params={"item": item},
                timeout=5,
            ).json()

            if inv.get("available", 0) <= 0:
                span.set_attribute("order.status", "out_of_stock")
                orders_counter.add(1, {"item": item, "status": "out_of_stock"})
                order_duration.record((time.time() - t0) * 1000,
                                      {"item": item, "status": "out_of_stock"})
                return jsonify({"status": "out_of_stock", "item": item}), 409

            result = requests.post(
                f"{BACKEND_URL}/process-order",
                json={"item": item, "user": user, "quantity": 1},
                timeout=5,
            )

            if result.status_code != 200:
                span.set_status(StatusCode.ERROR, result.text)
                orders_counter.add(1, {"item": item, "status": "error"})
                order_duration.record((time.time() - t0) * 1000,
                                      {"item": item, "status": "error"})
                return jsonify({"error": result.json().get("error")}), result.status_code

            span.set_attribute("order.status", "success")
            span.set_attribute("order.id", result.json().get("order_id", ""))
            orders_counter.add(1, {"item": item, "status": "success"})
            order_duration.record((time.time() - t0) * 1000,
                                  {"item": item, "status": "success"})
            return jsonify({"status": "ordered", "item": item, **result.json()})

        except Exception as exc:
            span.record_exception(exc)
            span.set_status(StatusCode.ERROR, str(exc))
            orders_counter.add(1, {"item": item, "status": "error"})
            order_duration.record((time.time() - t0) * 1000,
                                  {"item": item, "status": "error"})
            return jsonify({"error": str(exc)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "frontend"})


# ── Load generator ────────────────────────────────────────────────────────────

def load_generator():
    time.sleep(8)
    while True:
        try:
            requests.get(
                "http://localhost:5000/order",
                params={"item": random.choice(ITEMS)},
                timeout=5,
            )
        except Exception:
            pass
        time.sleep(random.uniform(1.5, 3.5))


if __name__ == "__main__":
    threading.Thread(target=load_generator, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
