# traffic_service/main.py
from fastapi import FastAPI
import random
from datetime import datetime
import httpx
import asyncio

app = FastAPI()

# Configuration for Service Discovery
SERVICE_NAME = "traffic_service"
# This URL is how other containers will reach this service inside Docker network
SERVICE_URL = "http://traffic_service:8000"
# The URL of the Service Registry
REGISTRY_URL = "http://service_registry:8000/register"

@app.on_event("startup")
async def register_with_registry():
    """
    On startup, this service attempts to register itself with the Service Registry.
    It uses a retry loop because the Registry might be starting up at the same time.
    """
    async with httpx.AsyncClient() as client:
        # Try to register up to 5 times
        for attempt in range(5):
            try:
                print(f"Attempting to register {SERVICE_NAME}...")
                response = await client.post(
                    REGISTRY_URL,
                    json={"name": SERVICE_NAME, "url": SERVICE_URL}
                )
                if response.status_code == 200:
                    print(f"Successfully registered {SERVICE_NAME}")
                    break
            except Exception as e:
                print(f"Registration attempt {attempt + 1} failed: {str(e)}")
                # Wait 2 seconds before retrying
                await asyncio.sleep(2)
        else:
            print("Failed to register service after multiple attempts.")

@app.get("/")
def read_root():
    return {"service": "Traffic Service", "status": "active"}

@app.get("/traffic/status")
def get_traffic_status():
    # Simulating data as requested in the PDF
    intersection_id = "I-12"
    current_time = datetime.utcnow().isoformat()
    
    # Simulating random vehicle count
    vehicle_count = random.randint(50, 500)
    
    # Logic to determine signal phase based on vehicle count
    signal_phase = "NS_GREEN"
    if vehicle_count > 400:
        signal_phase = "NS_RED_EXTENDED"

    return {
        "intersection_id": intersection_id,
        "timestamp": current_time,
        "vehicle_count": vehicle_count,
        "average_speed_kmh": 14.2,
        "signal_phase": signal_phase,
        "recommended_adjustment": {
            "new_green_seconds": 45
        }
    }

@app.post("/traffic/adjust")
def adjust_traffic_light(adjustment_data: dict):
    return {"status": "success", "message": "Traffic light adjusted", "data": adjustment_data}