from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.engine import get_dashboard_summary, get_market_analytics
from app.database.session import get_db

router = APIRouter()


@router.get("/dashboard", summary="Ana sayfa Dashboard için tüm özet metrikleri ve grafik verilerini döner")
def read_dashboard_summary(
    include_demo: bool = Query(True),
    db: Session = Depends(get_db),
):
    return get_dashboard_summary(db, include_demo=include_demo)


@router.get("/market", summary="İş piyasası analizi sayfasındaki çoklu filtreleme ve grafik verilerini döner")
def read_market_analytics(
    city: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    remote_type: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    include_demo: bool = Query(True),
    db: Session = Depends(get_db),
):
    return get_market_analytics(
        db=db,
        city=city,
        role=role,
        sector=sector,
        remote_type=remote_type,
        skill_name=skill,
        date_from=date_from,
        date_to=date_to,
        include_demo=include_demo,
    )
