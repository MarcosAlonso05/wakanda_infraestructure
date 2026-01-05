import httpx
import time
import random
import asyncio
from datetime import datetime

GATEWAY_URL = "http://localhost:8080"

ZONES = ["A", "B", "C", "D", "E", "CENTRAL", "INDUSTRIAL"]

SERVICES = ["traffic", "energy", "water", "waste", "security", "health"]

async def simulate_user_activity():
    print(f"Starting traffic simulation over Wakanda ({GATEWAY_URL})...")
    print("Press CTRL+C to stop.\n")

    async with httpx.AsyncClient() as client:
        total_requests = 0
        errors = 0

        try:
            while True:
                zone = random.choice(ZONES)
                service = random.choice(SERVICES)
                
                start_time = time.time()
                try:
                    url = f"{GATEWAY_URL}/{service}/zone/{zone}"
                    response = await client.get(url, timeout=5.0)
                    
                    elapsed = (time.time() - start_time) * 1000 # ms
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    if response.status_code == 200:
                        data = response.json()
                        item_count = len(data) if isinstance(data, list) else 0
                        print(f"[{timestamp}] ✅ {service.upper()} | Zone {zone} | {item_count} items | {elapsed:.0f}ms")
                    else:
                        print(f"[{timestamp}] ❌ {service.upper()} | Zone {zone} | Error {response.status_code}")
                        errors += 1
                        
                except httpx.RequestError as e:
                    print(f"[{timestamp}] Connection Error: {e}")
                    errors += 1
                
                total_requests += 1
                
                await asyncio.sleep(random.uniform(0.1, 0.8))

        except KeyboardInterrupt:
            print("\nSimulation stopped.")
            print(f"Summary: {total_requests} requests, {errors} errors.")

if __name__ == "__main__":
    try:
        asyncio.run(simulate_user_activity())
    except ImportError:
        print("Error: You need to install the 'httpx' library. Run: pip install httpx")