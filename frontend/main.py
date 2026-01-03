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
    
    services = ["traffic", "energy", "water", "waste", "security", "health"]
    
    data = {service: [] for service in services}
    errors = []

    async with httpx.AsyncClient() as client:
        tasks = []
        for service in services:
            url = f"{GATEWAY_URL}/{service}/zone/{zone_id}"
            tasks.append(client.get(url, timeout=4.0))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for i, service in enumerate(services):
            resp = responses[i]
            if isinstance(resp, Exception):
                errors.append(f"{service.capitalize()}: Connection Error")
            elif resp.status_code == 200:
                data[service] = resp.json()
            else:
                errors.append(f"{service.capitalize()}: Service Unavailable")

    return templates.TemplateResponse("zone_details.html", {
        "request": request,
        "zone_id": zone_id,
        "data": data,
        "errors": errors
    })