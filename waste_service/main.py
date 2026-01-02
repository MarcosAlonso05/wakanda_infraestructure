# waste_service/main.py
from fastapi import FastAPI
import random
from datetime import datetime
import httpx
import asyncio
from typing import List, Dict

# --- METRICS & TRACING ---
from prometheus_client import make_asgi_app, Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# --- CONFIGURATION ---
MY_SERVICE_NAME = "waste_service"
SERVICE_URL = "http://waste_service:8000"
REGISTRY_URL = "http://service_registry:8000/register"

# --- PERSISTENCIA EN MEMORIA ---
# Guardamos cuántos contenedores tiene cada zona
ZONE_CONFIG: Dict[str, int] = {}

# --- TRACING SETUP ---
def setup_jaeger():
    resource = Resource(attributes={SERVICE_NAME: MY_SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

setup_jaeger()

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# --- METRICS ---
REQUEST_COUNT = Counter('app_request_count', 'Request Count', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request Latency', ['method', 'endpoint'])
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# --- REGISTRATION ---
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

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"service": "Waste Management Service", "status": "active"}

@app.get("/waste/zone/{zone_id}")
def get_waste_by_zone(zone_id: str):
    """
    Devuelve el estado de los contenedores en una zona.
    Número de contenedores persistente (2-5 por zona).
    """
    with REQUEST_LATENCY.labels(method="GET", endpoint="/waste/zone").time():
        
        # 1. Configurar zona si es nueva
        if zone_id not in ZONE_CONFIG:
            ZONE_CONFIG[zone_id] = random.randint(2, 5)
            print(f"DEBUG: Configured Waste Zone {zone_id} with {ZONE_CONFIG[zone_id]} bins.")

        num_sensors = ZONE_CONFIG[zone_id]
        sensors_data = []

        # 2. Generar datos
        waste_types = ["ORGANIC", "PLASTIC", "PAPER", "GLASS"]
        
        for i in range(1, num_sensors + 1):
            bin_id = f"BIN-{zone_id}-0{i}"
            
            # Simulamos llenado
            fill_level = random.randint(0, 100)
            
            # Asignamos un tipo de basura fijo basado en el índice (para que no cambie el tipo al refrescar)
            w_type = waste_types[i % len(waste_types)]
            
            status = "NORMAL"
            if fill_level > 90:
                status = "CRITICAL_FULL"
            elif fill_level > 75:
                status = "WARNING_HIGH"

            sensors_data.append({
                "id": bin_id,
                "zone": zone_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": w_type,
                "fill_level_percent": fill_level,
                "status": status
            })

        REQUEST_COUNT.labels(method="GET", endpoint="/waste/zone", http_status=200).inc()
        return sensors_data