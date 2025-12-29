# gateway_api/main.py
from fastapi import FastAPI, HTTPException
import httpx
import pybreaker

app = FastAPI()

REGISTRY_URL = "http://service_registry:8000"

# Configure Circuit Breaker
# fail_max=3: If it fails 3 times, the circuit opens.
# reset_timeout=10: Wait 10 seconds before trying again (simplified for testing).
traffic_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=10)

@app.get("/")
def read_root():
    return {"service": "API Gateway", "status": "active"}

@app.get("/traffic/status")
async def get_traffic_status():
    async with httpx.AsyncClient() as client:
        # Step 1: Discover service (Discovery is usually reliable, so we don't wrap this)
        try:
            registry_response = await client.get(f"{REGISTRY_URL}/discover/traffic_service")
            if registry_response.status_code != 200:
                raise HTTPException(status_code=503, detail="Traffic service not found in registry")
            
            service_url = registry_response.json()["url"]
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Service Registry unavailable")

        # Step 2: Call the service protected by Circuit Breaker
        try:
            response = await call_traffic_service(client, service_url)
            return response.json()
            
        except pybreaker.CircuitBreakerError:
            # This happens when the circuit is OPEN (fuse blown)
            raise HTTPException(
                status_code=503, 
                detail="Traffic Service is temporarily unavailable (Circuit Open)"
            )
        except httpx.RequestError:
            # This happens when the actual call fails
            raise HTTPException(status_code=503, detail="Traffic Service unreachable")

# We wrap the specific function call with the breaker decorator
@traffic_breaker
async def call_traffic_service(client, url):
    # If this raises an exception, the breaker counts a failure
    response = await client.get(f"{url}/traffic/status")
    response.raise_for_status() # Raise error if status is 4xx or 5xx
    return response