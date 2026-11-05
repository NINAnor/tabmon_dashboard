import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import get_settings
from .data import DataStore
from .routers import ops, public

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = DataStore(get_settings())
    app.state.store = store
    task = asyncio.create_task(store.refresh_forever())
    yield
    task.cancel()


app = FastAPI(
    title="TABMON dashboard API",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.include_router(public.router)
app.include_router(public.clips_router)
app.include_router(ops.auth_router)
app.include_router(ops.router)


@app.exception_handler(RuntimeError)
async def not_ready(request: Request, exc: RuntimeError):
    return JSONResponse({"detail": str(exc)}, status_code=503)


@app.get("/api/health")
def health():
    store: DataStore = app.state.store
    return {"ok": True, "loaded_at": store.loaded_at}
