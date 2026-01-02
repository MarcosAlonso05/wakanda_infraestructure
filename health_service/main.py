from fastapi import FastAPI
import random
from datetime import datetime
import httpx
import asyncio

# --- METRICS & TRACING IMPORTS ---
from prometheus_client import make_asgi_app, Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# --- CONFIGURATION ---
MY_SERVICE_NAME = "health_service"
SERVICE_URL = "http://health_service:8000"
REGISTRY_URL = "http://service_registry:8000/register"

# --- TRACING SETUP (OTLP) ---
def setup_jaeger():
    resource = Resource(attributes={SERVICE_NAME: MY_SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

setup_jaeger()

# --- APP SETUP ---
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# --- PROMETHEUS METRICS ---
REQUEST_COUNT = Counter(
    'app_request_count', 'Application Request Count', ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds', 'Application Request Latency', ['method', 'endpoint']
)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# --- SERVICE DISCOVERY REGISTRATION ---
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

# --- BUSINESS LOGIC (HEALTH) ---

@app.get("/")
def read_root():
    return {"service": "Smart Health System", "status": "active"}

@app.get("/health/status")
def get_health_status():
    with REQUEST_LATENCY.labels(method="GET", endpoint="/health/status").time():
        
        # Simulación: Estado de hospitales
        hospital_id = "GEN-HOSPITAL-01"
        icu_occupancy_percent = random.randint(30, 100)
        ambulances_available = random.randint(0, 15)
        
        system_status = "NORMAL"
        if icu_occupancy_percent > 90:
            system_status = "CRITICAL_BED_SHORTAGE"
        elif ambulances_available < 2:
            system_status = "WARNING_NO_AMBULANCES"

        REQUEST_COUNT.labels(method="GET", endpoint="/health/status", http_status=200).inc()

        return {
            "hospital_id": hospital_id,
            "timestamp": datetime.utcnow().isoformat(),
            "icu_occupancy_percent": icu_occupancy_percent,
            "ambulances_available": ambulances_available,
            "er_wait_time_minutes": random.randint(10, 240),
            "system_status": system_status,
            "active_emergencies": random.randint(0, 5)
        }