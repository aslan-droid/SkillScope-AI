from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.entities import ChatSession
from app.schemas.api_schemas import AssistantAskRequest
from app.services.ai_assistant import answer_user_question, check_ollama_status

router = APIRouter()


@router.get("/status", summary="Yerel Ollama LLM durumunu ve AI Fallback motoru bilgisini döner")
def get_assistant_status():
    ollama_info = check_ollama_status()
    return {
        "ollama": ollama_info,
        "fallback_engine": "RULE_AND_STATISTICAL_FALLBACK",
        "zero_cost_guaranteed": True,
        "suggested_questions": [
            "Veri analisti olmak için neler öğrenmeliyim?",
            "Python mı R mı daha fazla aranıyor?",
            "Gaziantep'te hangi teknoloji alanlarında ilan var?",
            "SQL ile birlikte en çok hangi beceriler aranıyor?",
            "CV'm hangi pozisyonlarla daha çok eşleşiyor?",
        ],
    }


@router.post("/ask", summary="Kullanıcı sorusunu veritabanı analizlerine dayanarak (Ollama veya Fallback ile) yanıtlar")
def ask_assistant(payload: AssistantAskRequest, db: Session = Depends(get_db)):
    return answer_user_question(
        db=db,
        question=payload.question,
        session_id=payload.session_id,
    )


@router.get("/sessions", summary="Önceki sohbet oturumlarını listeler")
def list_chat_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).limit(15).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "message_count": len(s.messages),
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}", summary="Belirli bir sohbet oturumunun mesaj geçmişini döner")
def get_chat_session_messages(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sohbet oturumu bulunamadı.")
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "engine_used": m.engine_used,
                "evidence": m.evidence_metadata,
                "created_at": m.created_at.isoformat(),
            }
            for m in session.messages
        ],
    }
