from fastapi import FastAPI
import random
from datetime import datetime
import httpx
import asyncio

from prometheus_client import make_asgi_app, Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

MY_SERVICE_NAME = "energy_service"

def setup_jaeger():
    resource = Resource(attributes={
        SERVICE_NAME: MY_SERVICE_NAME
    })
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

setup_jaeger()

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

REQUEST_COUNT = Counter(
    'app_request_count', 
    'Application Request Count',
    ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds', 
    'Application Request Latency',
    ['method', 'endpoint']
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

SERVICE_URL = "http://energy_service:8000"
REGISTRY_URL = "http://service_registry:8000/register"

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
    return {"service": "Energy Service", "status": "active"}

@app.get("/energy/grid")
def get_energy_grid():
    with REQUEST_LATENCY.labels(method="GET", endpoint="/energy/grid").time():
        
        grid_load_percent = random.randint(40, 95)
        status = "STABLE"
        if grid_load_percent > 90:
            status = "CRITICAL_LOAD"

        REQUEST_COUNT.labels(method="GET", endpoint="/energy/grid", http_status=200).inc()

        return {
            "grid_id": "WAKANDA-NORTH",
            "timestamp": datetime.utcnow().isoformat(),
            "current_load_mw": random.randint(300, 800),
            "capacity_percent": grid_load_percent,
            "status": status,
            "renewable_contribution": "45%"
        }