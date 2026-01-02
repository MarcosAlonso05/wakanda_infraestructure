from fastapi import FastAPI, HTTPException
import httpx
import pybreaker

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_jaeger():
    resource = Resource(attributes={
        SERVICE_NAME: "gateway_api" 
    })
    
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
    
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

setup_jaeger()

app = FastAPI()

FastAPIInstrumentor.instrument_app(app)

traffic_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=10)

REGISTRY_URL = "http://service_registry:8000"

@traffic_breaker
async def call_traffic_service(client, url):
    response = await client.get(f"{url}/traffic/status")
    response.raise_for_status()
    return response

@app.get("/")
def read_root():
    return {"service": "API Gateway", "status": "active"}

@app.get("/traffic/status")
async def get_traffic_status():
    async with httpx.AsyncClient() as client:
        try:
            registry_response = await client.get(f"{REGISTRY_URL}/discover/traffic_service")
            if registry_response.status_code != 200:
                raise HTTPException(status_code=503, detail="Traffic service not found in registry")
            
            service_url = registry_response.json()["url"]
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Service Registry unavailable")

        try:
            response = await call_traffic_service(client, service_url)
            return response.json()
            
        except pybreaker.CircuitBreakerError:
            raise HTTPException(
                status_code=503, 
                detail="Traffic Service is temporarily unavailable (Circuit Open)"
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Traffic Service unreachable")
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=500, detail="Traffic Service returned an error")

@app.get("/energy/grid")
async def get_energy_grid():
    async with httpx.AsyncClient() as client:
        try:
            registry_response = await client.get(f"{REGISTRY_URL}/discover/energy_service")
            if registry_response.status_code != 200:
                raise HTTPException(status_code=503, detail="Energy service not found")
            
            service_url = registry_response.json()["url"]
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Registry unavailable")

        try:
            
            response = await client.get(f"{service_url}/energy/grid", timeout=5.0)
            return response.json()
            
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Energy Service unreachable")

@app.get("/water/status")
async def get_water_status():
    async with httpx.AsyncClient() as client:
        try:
            registry_response = await client.get(f"{REGISTRY_URL}/discover/water_service")
            if registry_response.status_code != 200:
                raise HTTPException(status_code=503, detail="Water service not found")
            
            service_url = registry_response.json()["url"]
            
            response = await client.get(f"{service_url}/water/status", timeout=5.0)
            return response.json()
            
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Water Service unreachable")
        
@app.get("/waste/status")
async def get_waste_status():
    async with httpx.AsyncClient() as client:
        try:
            registry_response = await client.get(f"{REGISTRY_URL}/discover/waste_service")
            if registry_response.status_code != 200:
                raise HTTPException(status_code=503, detail="Waste service not found")
            
            service_url = registry_response.json()["url"]
            
            response = await client.get(f"{service_url}/waste/status", timeout=5.0)
            return response.json()
            
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Waste Service unreachable")
        
@app.get("/security/status")
async def get_security_status():
    async with httpx.AsyncClient() as client:
        try:
            # 1. Discovery
            registry_response = await client.get(f"{REGISTRY_URL}/discover/security_service")
            if registry_response.status_code != 200:
                raise HTTPException(status_code=503, detail="Security service not found")
            
            service_url = registry_response.json()["url"]
            
            # 2. Forward Request
            response = await client.get(f"{service_url}/security/status", timeout=5.0)
            return response.json()
            
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Security Service unreachable")

@app.get("/health/status")
async def get_health_status():
    async with httpx.AsyncClient() as client:
        try:
            # 1. Discovery
            registry_response = await client.get(f"{REGISTRY_URL}/discover/health_service")
            if registry_response.status_code != 200:
                raise HTTPException(status_code=503, detail="Health service not found")
            
            service_url = registry_response.json()["url"]
            
            # 2. Forward Request
            response = await client.get(f"{service_url}/health/status", timeout=5.0)
            return response.json()
            
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Health Service unreachable")