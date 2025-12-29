# traffic_service/main.py
from fastapi import FastAPI
import random
from datetime import datetime
import httpx
import asyncio

# 1. IMPORTAR LIBRERÍAS DE PROMETHEUS
from prometheus_client import make_asgi_app, Counter, Histogram # <--- IMPORTANTE

app = FastAPI()

# 2. DEFINIR LAS MÉTRICAS
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

# 3. ACTIVAR LA RUTA /metrics (Esto es lo que te faltaba seguramente)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app) # <--- IMPORTANTE: Sin esto, da error 404

# --- CONFIGURACIÓN DE REGISTRO (SERVICE DISCOVERY) ---
SERVICE_NAME = "traffic_service"
SERVICE_URL = "http://traffic_service:8000"
REGISTRY_URL = "http://service_registry:8000/register"

@app.on_event("startup")
async def register_with_registry():
    async with httpx.AsyncClient() as client:
        for attempt in range(5):
            try:
                # print(f"Attempting to register {SERVICE_NAME}...")
                response = await client.post(
                    REGISTRY_URL,
                    json={"name": SERVICE_NAME, "url": SERVICE_URL}
                )
                if response.status_code == 200:
                    print(f"Successfully registered {SERVICE_NAME}")
                    break
            except Exception as e:
                print(f"Registration attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(2)

@app.get("/")
def read_root():
    return {"service": "Traffic Service", "status": "active"}

@app.get("/traffic/status")
def get_traffic_status():
    # 4. USAR LA MÉTRICA (Cronómetro de latencia)
    with REQUEST_LATENCY.labels(method="GET", endpoint="/traffic/status").time():
        
        intersection_id = "I-12"
        current_time = datetime.utcnow().isoformat()
        vehicle_count = random.randint(50, 500)
        
        signal_phase = "NS_GREEN"
        if vehicle_count > 400:
            signal_phase = "NS_RED_EXTENDED"

        # 5. USAR LA MÉTRICA (Contar la visita)
        REQUEST_COUNT.labels(method="GET", endpoint="/traffic/status", http_status=200).inc()

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