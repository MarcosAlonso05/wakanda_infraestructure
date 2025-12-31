from fastapi import FastAPI
import random
from datetime import datetime, timedelta
import httpx
import asyncio

from prometheus_client import make_asgi_app, Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

MY_SERVICE_NAME = "waste_service"
SERVICE_URL = "http://waste_service:8000"
REGISTRY_URL = "http://service_registry:8000/register"

def setup_jaeger():
    resource = Resource(attributes={SERVICE_NAME: MY_SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

setup_jaeger()

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

REQUEST_COUNT = Counter(
    'app_request_count', 'Application Request Count', ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds', 'Application Request Latency', ['method', 'endpoint']
)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.on_event("startup")
async def register_with_registry():
    async with httpx.AsyncClient() as client:
        for attempt in range(5):
            try:
                response = await client.post(
                    REGISTRY_URL,
                    json={"name": MY_SERVICE_NAME, "url": SERVICE_URL}
                )
                if response.status_code == 200:
                    print(f"Registered {MY_SERVICE_NAME}")
                    break
            except Exception:
                await asyncio.sleep(2)

@app.get("/")
def read_root():
    return {"service": "Waste Management Service", "status": "active"}

@app.get("/waste/status")
def get_waste_status():
    with REQUEST_LATENCY.labels(method="GET", endpoint="/waste/status").time():
        
        fill_level = random.randint(0, 100)
        waste_type = random.choice(["ORGANIC", "PLASTIC", "PAPER", "GENERAL"])
        
        status = "NORMAL"
        if fill_level >= 90:
            status = "CRITICAL_FULL_PICKUP_REQUIRED"
        elif fill_level >= 75:
            status = "WARNING_HIGH_LEVEL"

        next_pickup_hours = random.randint(2, 24)
        if status == "CRITICAL_FULL_PICKUP_REQUIRED":
            next_pickup_hours = 1

        REQUEST_COUNT.labels(method="GET", endpoint="/waste/status", http_status=200).inc()

        return {
            "bin_id": f"BIN-{random.randint(100, 999)}",
            "timestamp": datetime.utcnow().isoformat(),
            "type": waste_type,
            "fill_level_percent": fill_level,
            "status": status,
            "estimated_pickup_in_hours": next_pickup_hours,
            "truck_assigned": "TRUCK-42" if fill_level > 80 else None
        }