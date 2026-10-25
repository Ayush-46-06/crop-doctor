"""
Crop Doctor AI - Production Server Entrypoint
Patches Streamlit's Starlette routes to provide lightweight /health and /healthz
endpoints for UptimeRobot, Render, and load balancers, and maintains keep-alive to avoid cold starts.
"""
import os
import sys
import threading
import time
import urllib.request
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
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    # Add /health and /healthz endpoints
    routes.append(Route(sr._with_base("health", base_url), _health_endpoint, methods=["GET", "HEAD"]))
    routes.append(Route(sr._with_base("healthz", base_url), _health_endpoint, methods=["GET", "HEAD"]))
    return routes

sr.create_health_routes = _patched_create_health_routes

def _start_keep_alive():
    """
    Render free tier puts instances to sleep after 15 minutes of inactivity.
    If RENDER_EXTERNAL_URL or KEEP_ALIVE_URL is present, periodically ping /health
    every 12 minutes to keep the instance warm and eliminate cold start delays.
    """
    external_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("KEEP_ALIVE_URL")
    if not external_url:
        return

    target = external_url.rstrip("/") + "/health"

    def _pinger():
        time.sleep(45)  # Wait for server to bind and start listening
        while True:
            try:
                req = urllib.request.Request(
                    target,
                    headers={"User-Agent": "CropDoctorKeepAlive/1.0"},
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    pass
            except Exception:
                pass
            time.sleep(12 * 60)  # Ping every 12 minutes

    thread = threading.Thread(target=_pinger, daemon=True, name="keep-alive-pinger")
    thread.start()

# Run Streamlit CLI
from streamlit.web.cli import main

if __name__ == "__main__":
    _start_keep_alive()
    main()

