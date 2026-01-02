# frontend/main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles # <--- IMPORTANTE: Importar esto
import httpx

app = FastAPI()

# 1. Montar la carpeta estática
# Esto hace que los archivos en /static sean accesibles desde el navegador
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

GATEWAY_URL = "http://gateway_api:8000"

# ... (El resto de tus rutas @app.get... se quedan igual) ...
@app.get("/", response_class=HTMLResponse)
async def read_map(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})

@app.get("/zone/{zone_id}", response_class=HTMLResponse)
async def read_zone_details(request: Request, zone_id: str):
    traffic_data = []
    error = None
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{GATEWAY_URL}/traffic/zone/{zone_id}")
            if resp.status_code == 200:
                traffic_data = resp.json()
            else:
                error = "Error fetching data from Gateway"
        except Exception as e:
            error = f"Connection failed: {str(e)}"

    return templates.TemplateResponse("zone_details.html", {
        "request": request,
        "zone_id": zone_id,
        "traffic_data": traffic_data,
        "error": error
    })