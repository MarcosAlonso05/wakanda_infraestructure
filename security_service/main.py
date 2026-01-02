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
MY_SERVICE_NAME = "security_service"
SERVICE_URL = "http://security_service:8000"
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

# --- BUSINESS LOGIC ---

@app.get("/")
def read_root():
    return {"service": "Security Command Center", "status": "active"}

@app.get("/security/status")
def get_security_status():
    with REQUEST_LATENCY.labels(method="GET", endpoint="/security/status").time():
        
        # Simulación: Análisis de cámaras de vigilancia
        zone_id = random.choice(["DOWNTOWN", "BORDER_NORTH", "LABS", "RESIDENTIAL"])
        crowd_density = random.randint(0, 100)
        
        threat_level = "LOW"
        alerts = []

        if crowd_density > 80:
            threat_level = "MEDIUM"
            alerts.append("UNUSUAL_CROWD_DETECTED")
        
        # Simulación evento aleatorio raro (Intrusión)
        if random.random() < 0.1: # 10% de probabilidad
            threat_level = "HIGH"
            alerts.append("UNAUTHORIZED_ACCESS_ATTEMPT")

        REQUEST_COUNT.labels(method="GET", endpoint="/security/status", http_status=200).inc()

        return {
            "zone_id": zone_id,
            "timestamp": datetime.utcnow().isoformat(),
            "active_cameras": 124,
            "threat_level": threat_level,
            "crowd_density_percent": crowd_density,
            "active_alerts": alerts,
            "drone_patrol_status": "AIRBORNE" if threat_level == "HIGH" else "DOCKED"
        }