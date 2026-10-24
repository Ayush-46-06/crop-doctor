"""
Crop Doctor AI - Production Server Entrypoint
Patches Streamlit's Starlette routes to provide lightweight /health and /healthz
endpoints for UptimeRobot, Render, and load balancers.
"""
import sys
import streamlit.web.server.starlette.starlette_routes as sr
from starlette.routing import Route
from starlette.responses import JSONResponse

# Patch Starlette health routes to add /health and /healthz
_original_create_health_routes = sr.create_health_routes

def _patched_create_health_routes(runtime, base_url):
    routes = _original_create_health_routes(runtime, base_url)

    async def _health_endpoint(request):
        return JSONResponse(
            {
                "status": "ok",
                "service": "Crop Doctor AI",
                "healthy": True,
            },
            status_code=200,
            headers={"Cache-Control": "no-cache"},
        )

    # Add /health and /healthz endpoints
    routes.append(Route(sr._with_base("health", base_url), _health_endpoint, methods=["GET", "HEAD"]))
    routes.append(Route(sr._with_base("healthz", base_url), _health_endpoint, methods=["GET", "HEAD"]))
    return routes

sr.create_health_routes = _patched_create_health_routes

# Run Streamlit CLI
from streamlit.web.cli import main

if __name__ == "__main__":
    main()
