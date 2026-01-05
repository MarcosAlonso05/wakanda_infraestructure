from fastapi import FastAPI
import random
from datetime import datetime
import httpx
import asyncio
from typing import List, Dict

from prometheus_client import make_asgi_app, Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

MY_SERVICE_NAME = "security_service"
SERVICE_URL = "http://security_service:8000"
REGISTRY_URL = "http://service_registry:8000/register"

ZONE_CONFIG: Dict[str, int] = {}

def setup_jaeger():
    resource = Resource(attributes={SERVICE_NAME: MY_SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

setup_jaeger()

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

REQUEST_COUNT = Counter('app_request_count', 'Request Count', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request Latency', ['method', 'endpoint'])
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.on_event("startup")
async def register_with_registry():
    async with httpx.AsyncClient() as client:
        for attempt in range(5):
            try:
                await client.post(REGISTRY_URL, json={"name": MY_SERVICE_NAME, "url": SERVICE_URL})
                print(f"Registered {MY_SERVICE_NAME}")
                break
            except Exception:
                await asyncio.sleep(2)

@app.get("/")
def read_root():
    return {"service": "Security Command Center", "status": "active"}

@app.get("/security/zone/{zone_id}")
def get_security_by_zone(zone_id: str):
    with REQUEST_LATENCY.labels(method="GET", endpoint="/security/zone").time():
        
        if zone_id not in ZONE_CONFIG:
            ZONE_CONFIG[zone_id] = random.randint(3, 8)
            print(f"DEBUG: Configured Security Zone {zone_id} with {ZONE_CONFIG[zone_id]} cameras.")

        num_cameras = ZONE_CONFIG[zone_id]
        sensors_data = []

        for i in range(1, num_cameras + 1):
            cam_id = f"CAM-{zone_id}-0{i}"
            
            people_count = random.randint(0, 50)
            alert_level = "SAFE"
            anomalies = []

            if people_count > 40:
                alert_level = "WARNING_CROWD"
                anomalies.append("High crowd density")
            
            if random.random() < 0.05:
                alert_level = "DANGER"
                anomalies.append("Aggressive behavior detected")

            sensors_data.append({
                "id": cam_id,
                "zone": zone_id,
                "timestamp": datetime.utcnow().isoformat(),
                "people_detected": people_count,
                "status": alert_level,
                "alerts": anomalies
            })

        REQUEST_COUNT.labels(method="GET", endpoint="/security/zone", http_status=200).inc()
        return sensors_data