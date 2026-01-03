from fastapi import FastAPI
import random
from datetime import datetime
import httpx
import asyncio
from typing import List, Dict # Importamos Dict

from prometheus_client import make_asgi_app, Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

MY_SERVICE_NAME = "traffic_service"
SERVICE_URL = "http://traffic_service:8000"
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
    return {"service": "Traffic Service", "status": "active"}

@app.get("/traffic/zone/{zone_id}")
def get_traffic_by_zone(zone_id: str):
    """
    Devuelve sensores para una zona.
    El número de sensores se decide la primera vez y se mantiene fijo.
    """
    with REQUEST_LATENCY.labels(method="GET", endpoint="/traffic/zone").time():
        
        if zone_id not in ZONE_CONFIG:
            ZONE_CONFIG[zone_id] = random.randint(2, 6)
            print(f"DEBUG: Configurada Zona {zone_id} con {ZONE_CONFIG[zone_id]} sensores.")

        num_sensors = ZONE_CONFIG[zone_id]
        
        sensors_data = []
        
        for i in range(1, num_sensors + 1):
            intersection_id = f"I-{zone_id}-0{i}"
            
            vehicle_count = random.randint(0, 600)
            phase = "GREEN"
            if vehicle_count > 500:
                phase = "RED_ALL_WAY"
            elif vehicle_count > 300:
                phase = "RED_EXTENDED"
            
            status_text = "CONGESTED" if vehicle_count > 450 else "FLOWING"
            
            sensors_data.append({
                "id": intersection_id,
                "zone": zone_id,
                "timestamp": datetime.utcnow().isoformat(),
                "vehicle_count": vehicle_count,
                "signal_phase": phase,
                "status": status_text
            })

        REQUEST_COUNT.labels(method="GET", endpoint="/traffic/zone", http_status=200).inc()
        return sensors_data

@app.get("/traffic/status")
def get_traffic_status():
    return {"status": "legacy", "value": random.randint(0,100)}