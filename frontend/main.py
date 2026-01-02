# frontend/main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

GATEWAY_URL = "http://gateway_api:8000"

@app.get("/", response_class=HTMLResponse)
async def read_map(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})

@app.get("/zone/{zone_id}", response_class=HTMLResponse)
async def read_zone_details(request: Request, zone_id: str):
    
    # Lista de servicios a consultar
    services = ["traffic", "energy", "water", "waste", "security", "health"]
    
    # Diccionario para guardar los resultados
    data = {service: [] for service in services}
    errors = []

    async with httpx.AsyncClient() as client:
        # Preparamos las 6 peticiones en paralelo
        tasks = []
        for service in services:
            url = f"{GATEWAY_URL}/{service}/zone/{zone_id}"
            tasks.append(client.get(url, timeout=4.0))

        # Ejecutamos las peticiones a la vez
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Procesamos resultados
        for i, service in enumerate(services):
            resp = responses[i]
            if isinstance(resp, Exception):
                # Si hubo error de conexión
                errors.append(f"{service.capitalize()}: Connection Error")
            elif resp.status_code == 200:
                # Si todo fue bien, guardamos el JSON
                data[service] = resp.json()
            else:
                # Si el servicio respondió error (ej. 503)
                errors.append(f"{service.capitalize()}: Service Unavailable")

    return templates.TemplateResponse("zone_details.html", {
        "request": request,
        "zone_id": zone_id,
        "data": data,   # Pasamos todos los datos juntos
        "errors": errors
    })