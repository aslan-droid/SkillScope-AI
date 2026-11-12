from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.database.seed import load_synthetic_demo_dataset, seed_skills_and_categories
from app.database.session import Base, SessionLocal, engine
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.APP_ENV != "test":
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_skills_and_categories(db)
            if settings.AUTO_SEED_DEMO_DATA:
                load_synthetic_demo_dataset(db, force_reload=False)
        finally:
            db.close()
    yield


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
