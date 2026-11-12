import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.database.seed import load_synthetic_demo_dataset, seed_skills_and_categories
from app.database.session import Base, SessionLocal, engine
from app.models.entities import Job
from app.services.live_sync import SYNC_STATE, sync_live_sources
import app.models  # noqa: F401


def _run_sync_in_session() -> None:
    db = SessionLocal()
    try:
        sync_live_sources(db=db, sources=["remotive", "arbeitnow"], limit_per_source=80, retrain_models=True)
    finally:
        db.close()


async def _periodic_live_sync_loop() -> None:
    """Belirlenen aralıklarla açık API kaynaklarından yeni iş ilanlarını arka planda çeker."""
    interval_seconds = max(60, settings.LIVE_SYNC_INTERVAL_MINUTES * 60)
    db = SessionLocal()
    try:
        real_count = db.query(Job).filter(Job.is_demo.is_(False)).count()
    finally:
        db.close()

    if real_count == 0:
        await asyncio.to_thread(_run_sync_in_session)
    else:
        SYNC_STATE["next_sync_at"] = (
            datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)
        ).isoformat()

    while True:
        await asyncio.sleep(interval_seconds)
        await asyncio.to_thread(_run_sync_in_session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    sync_task: asyncio.Task | None = None
    if settings.APP_ENV != "test":
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_skills_and_categories(db)
            if settings.AUTO_SEED_DEMO_DATA:
                load_synthetic_demo_dataset(db, force_reload=False)
        finally:
            db.close()

        if settings.AUTO_SYNC_LIVE_DATA:
            sync_task = asyncio.create_task(_periodic_live_sync_loop())
    try:
        yield
    finally:
        if sync_task is not None:
            sync_task.cancel()
            with suppress(asyncio.CancelledError):
                await sync_task


app = FastAPI(
    title="SkillScope AI API",
    description=(
        "Yapay zekâ destekli iş piyasası analiz ve kariyer zekâ platformu REST API. "
        "Sıfır zorunlu ücretli API bağımlılığı ile NLP beceri çıkarımı, zaman serisi talep tahmini, "
        "CV analizi, kariyer yol haritası ve hibrit AI asistanı servislerini sunar."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Sistem iç detaylarını sızdırmadan güvenli hata yanıtı döner."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "İstek işlenirken beklenmeyen bir sunucu hatası oluştu. Lütfen girdi verilerinizi kontrol edin."
        },
    )


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Kök Dizin"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }
