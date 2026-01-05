# wakanda_infraestructure

ste proyecto implementa una arquitectura de **microservicios** completa para la simulación y gestión de una Smart City. El sistema está diseñado para ser escalable, resiliente y observable, utilizando contenedores Docker y un stack moderno de monitorización.

## Tecnologías y Herramientas

* **Lenguaje:** Python (FastAPI, Uvicorn, HTTPX).
* **Contenedores:** Docker & Docker Compose.
* **Orquestación:** Service Discovery & API Gateway pattern.
* **Frontend:** HTML5, CSS3 (Glassmorphism), Jinja2 Templates.
* **Observabilidad:**
    * **Prometheus:** Recolección de métricas.
    * **Grafana:** Visualización de dashboards en tiempo real.
    * **Jaeger:** Trazabilidad distribuida (Distributed Tracing).

## Arquitectura del Sistema

El sistema se compone de los siguientes contenedores interconectados:

1.  **Core Infrastructure:**
    * `service_registry` (Puerto 8002): Descubrimiento dinámico de servicios.
    * `gateway_api` (Puerto 8080): Punto de entrada único y balanceo de carga.
2.  **Microservicios de Negocio:**
    * `traffic_service`: Control de flujo vehicular.
    * `energy_service`: Gestión de red eléctrica y transformadores.
    * `water_service`: Calidad y suministro de agua.
    * `waste_service`: Gestión de residuos y contenedores inteligentes.
    * `security_service`: Videovigilancia y conteo de personas.
    * `health_service`: Gestión de recursos hospitalarios.
3.  **Frontend:** Dashboard web para visualizar el estado de las zonas.

## Instalación y Ejecución

### Prerrequisitos
* Docker Desktop instalado y corriendo.
* Python 3.x (Opcional, solo para correr el script de integración localmente).

### Pasos para arrancar
1.  Clona el repositorio.
2.  Construye y levanta los contenedores:
    ```bash
    docker compose up -d --build
    ```
3.  Espera unos segundos a que todos los servicios se registren en el `service_registry`.

## Accesos y URLs

| Componente | URL | Credenciales (si aplica) |
| :--- | :--- | :--- |
| **Frontend (Mapa)** | `http://localhost:3001` | - |
| **API Gateway** | `http://localhost:8080/docs` | - |
| **Grafana** | `http://localhost:3000` | admin / admin |
| **Jaeger UI** | `http://localhost:16686` | - |
| **Prometheus** | `http://localhost:9090` | - |

## Ejecución de Pruebas

### 1. Tests Unitarios (Dentro de Docker)

Para verificar la lógica interna de los servicios (ej. Tráfico):

```bash
docker compose exec traffic_service pytest
```

### 2. Test de Integración / Carga (Bot de Tráfico)

Este script simula usuarios navegando por el sistema para generar datos en Grafana.
Requisito: Instalar librería local (pip install httpx).
Ejecutar:

```bash
python integration_test.py
```

---

## Enlace al repositorio

```
https://github.com/MarcosAlonso05/wakanda_infraestructure
```
