# service_registry/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory storage for services: { "service_name": "service_url" }
service_store = {}

# Data model for input validation
class ServiceRegistration(BaseModel):
    name: str
    url: str

@app.post("/register")
def register_service(service: ServiceRegistration):
    # Save the service info
    service_store[service.name] = service.url
    print(f"Registered service: {service.name} at {service.url}")
    return {"status": "registered", "service": service.name}

@app.get("/discover/{service_name}")
def discover_service(service_name: str):
    url = service_store.get(service_name)
    if not url:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"url": url}

@app.get("/")
def get_all_services():
    return service_store