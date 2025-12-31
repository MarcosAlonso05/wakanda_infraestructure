import random
import httpx
import asyncio
from fastapi import FastAPI
from datetime import datetime

from prometheus_client import make_asgi_app, Counter, Histogram

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_jaeger():
    resource = Resource(attributes={
        SERVICE_NAME: "water_service" 
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

SERVICE_NAME_REGISTRY = "water_service"
SERVICE_URL = "http://water_service:8000"
REGISTRY_URL = "http://service_registry:8000/register"

@app.on_event("startup")
async def register_with_registry():
    async with httpx.AsyncClient() as client:
        for attempt in range(5):
            try:
                response = await client.post(
                    REGISTRY_URL,
                    json={"name": SERVICE_NAME_REGISTRY, "url": SERVICE_URL}
                )
                if response.status_code == 200:
                    print(f"Successfully registered {SERVICE_NAME_REGISTRY}")
                    break
            except Exception as e:
                print(f"Registration attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(2)

@app.get("/")
def read_root():
    return {"service": "Water Service", "status": "active"}

@app.get("/water/status")
def get_water_status():
    with REQUEST_LATENCY.labels(method="GET", endpoint="/water/status").time():
        
        ph_level = round(random.uniform(6.5, 8.5), 2)
        turbidity = random.randint(1, 15)
        pressure_psi = random.randint(40, 80)
        
        water_status = "SAFE"
        if ph_level < 6.5 or ph_level > 8.0:
            water_status = "WARNING_PH_LEVEL"
        elif turbidity > 10:
            water_status = "WARNING_TURBIDITY_HIGH"

        REQUEST_COUNT.labels(method="GET", endpoint="/water/status", http_status=200).inc()

        return {
            "reservoir_id": "RES-MAIN-01",
            "timestamp": datetime.utcnow().isoformat(),
            "ph_level": ph_level,
            "turbidity_ntu": turbidity,
            "pressure_psi": pressure_psi,
            "quality_status": water_status,
            "chlorine_level_mg": 0.5
        }

@app.post("/water/adjust")
def adjust_water_light(adjustment_data: dict):
    return {"status": "success", "message": "Water light adjusted", "data": adjustment_data}