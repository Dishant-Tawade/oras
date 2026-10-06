"""ORAS FastAPI entry point: REST API, WebSocket endpoint and the built frontend."""
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Configure the root logger so application loggers reach stdout; uvicorn only
# configures its own.
_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

from auth import get_store
from config import refresh_cfg, refresh_derived
from routers import admin_router, auth_router, game_router, ws_router
from scenarios import set_active_scenario
from services.executors import BROADCAST_EXECUTOR, SIMULATION_EXECUTOR
from services.timer import TimerManager
from ws.manager import ConnectionManager

DEFAULT_SCENARIO = ('us', 'ev')
MAX_CONCURRENT_SIMULATIONS = 8


def _load_saved_scenario() -> None:
    """Activate the scenario the admin last chose, falling back to the default."""
    country, industry = get_store().load_active_scenario() or DEFAULT_SCENARIO
    try:
        set_active_scenario(country, industry)
    except KeyError:
        logging.warning("Saved scenario %s/%s is not registered; using default.", country, industry)
        set_active_scenario(*DEFAULT_SCENARIO)
    refresh_cfg()
    refresh_derived()


_load_saved_scenario()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.timer_manager = TimerManager(app.state.manager)
    yield
    await app.state.manager.disconnect_all()


app = FastAPI(title="ORAS", lifespan=lifespan)

app.state.manager = ConnectionManager()
app.state.simulation_executor = SIMULATION_EXECUTOR
app.state.broadcast_executor = BROADCAST_EXECUTOR
# Bounds simultaneous year-lock simulations so a burst of locks cannot starve
# the event loop (heartbeats, polls) of CPU.
app.state.sim_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SIMULATIONS)

# Credentials are allowed, so the browser rejects a wildcard origin.
_DEFAULT_ORIGINS = "http://localhost:5173,http://localhost:8080,http://localhost:3000"
_origins_raw = os.environ.get('ALLOWED_ORIGINS', _DEFAULT_ORIGINS).strip()
if _origins_raw == "*":
    raise RuntimeError(
        "ALLOWED_ORIGINS='*' is not permitted. Set it to a comma-separated list "
        "of origins, e.g. https://oras.example.com"
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins_raw.split(',') if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api")
app.include_router(game_router.router, prefix="/api")
app.include_router(admin_router.router, prefix="/api")
app.include_router(ws_router.router)

# Serve the built frontend (run `npm run build` in frontend/) when present.
for _dist in (os.path.join(_ROOT, "frontend", "dist"),
              os.path.join(os.path.dirname(_ROOT), "frontend", "dist")):
    if os.path.isdir(_dist):
        app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
        break


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", host="0.0.0.0", port=8080, reload=True,
        reload_excludes=["data/*", "*.json", "*.tmp", "__pycache__/*"],
    )
