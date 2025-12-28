# gateway_api/main.py
from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

REGISTRY_URL = "http://service_registry:8000"

@app.get("/")
def read_root():
    return {"service": "API Gateway", "status": "active"}

@app.get("/traffic/status")
async def get_traffic_status():
    async with httpx.AsyncClient() as client:
        # Step 1: Discover the service URL
        try:
            # Ask the registry: "Where is traffic_service?"
            registry_response = await client.get(f"{REGISTRY_URL}/discover/traffic_service")
            
            if registry_response.status_code != 200:
                raise HTTPException(status_code=503, detail="Traffic service not found in registry")
            
            # Extract the URL (e.g., "http://traffic_service:8000")
            service_url = registry_response.json()["url"]
            
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Service Registry unavailable")

        # Step 2: Call the service
        try:
            # Now we use the dynamic URL
            response = await client.get(f"{service_url}/traffic/status")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Traffic Service unavailable")