from fastapi import FastAPI

from app.config import settings
from interfaces_adaptor.http.controllers import router as ingest_router

app = FastAPI(title="RAPTOR Service")
app.include_router(ingest_router, prefix=settings.api_prefix)
