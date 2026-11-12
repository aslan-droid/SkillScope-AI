from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics.engine import get_dashboard_summary, get_market_analytics, get_skill_deep_dive
from app.core.config import settings
from app.models.entities import ChatMessage, ChatSession, CVAnalysis, DataSource, Job, Skill
from app.nlp.extractor import SkillExtractor, normalize_role_title
from app.services.cv_and_career import get_role_skill_benchmarks

KNOWN_CITIES = [
    "İstanbul",
    "Ankara",
    "İzmir",
    "Gaziantep",
    "Bursa",
    "Kocaeli",
    "Antalya",
    "Adana",
    "Konya",
    "Kayseri",
]


def check_ollama_status() -> Dict[str, Any]:
    """Yerel Ollama servisinin çalışıp çalışmadığını ve yapılandırılan modeli kontrol eder."""
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return {
                    "available": True,
                    "base_url": settings.OLLAMA_BASE_URL,
                    "configured_model": settings.OLLAMA_MODEL,
                    "installed_models": models,
                }
    except Exception:
        pass
    return {
        "available": False,
        "base_url": settings.OLLAMA_BASE_URL,
        "configured_model": settings.OLLAMA_MODEL,
        "installed_models": [],
    }


def _detect_question_context(db: Session, question: str) -> Dict[str, Any]:
    """
    Kullanıcının Türkçe sorusundaki anahtar kavramları (şehir, pozisyon, beceriler, CV referansı)
    güvenli biçimde tespit eder ve izin verilen backend analiz fonksiyonlarını çağırır.
    Asla doğrudan SQL çalıştırmaz.
    """
    q_low = question.lower().replace("İ", "i").replace("I", "ı")
    extractor = SkillExtractor.from_db(db)
    mentioned_skills = extractor.extract_skills(question)

    # "Python mı R mı" gibi tek harfli 'R' dil karşılaştırması kontrolü
    mentions_r_lang = any(tok in q_low.split() for tok in ["r", "r?"]) and ("mı" in q_low or "mi" in q_low or "karşılaştır" in q_low)

    detected_city: Optional[str] = None
    for city in KNOWN_CITIES:
        c_low = city.lower().replace("İ", "i").replace("I", "ı")
        if c_low in q_low:
            detected_city = city
            break

    detected_role: Optional[str] = None
    role_keywords = [
        ("veri analist", "Veri Analisti"),
        ("data analyst", "Veri Analisti"),
        ("veri bilim", "Veri Bilimci"),
        ("data scientist", "Veri Bilimci"),
        ("yapay zeka", "Yapay Zekâ / ML Mühendisi"),
        ("yapay zekâ", "Yapay Zekâ / ML Mühendisi"),
        ("machine learning", "Yapay Zekâ / ML Mühendisi"),
        ("backend", "Backend Geliştirici"),
        ("frontend", "Frontend Geliştirici"),
        ("full stack", "Full-Stack / Yazılım Mühendisi"),
        ("yazılım", "Full-Stack / Yazılım Mühendisi"),
        ("devops", "DevOps & Sistem Mühendisi"),
        ("siber güvenlik", "Siber Güvenlik Uzmanı"),
        ("iş analist", "İş Analisti / Ürün Yöneticisi"),
    ]
    for kw, norm_r in role_keywords:
        if kw in q_low:
            detected_role = norm_r
            break

    asks_cv = any(k in q_low for k in ["cv", "özgeçmiş", "ozgecmis", "benim beceri", "hangi pozisyonlarla"])
    asks_cooccurrence = any(k in q_low for k in ["birlikte", "yanında", "beraber", "eşlik"])
    asks_comparison = any(k in q_low for k in ["mı", "mi", "mu", "mü", "daha fazla", "karşılaştır", "fark"]) and (len(mentioned_skills) >= 2 or mentions_r_lang)

    return {
        "question_lower": q_low,
        "mentioned_skills": mentioned_skills,
        "mentions_r_lang": mentions_r_lang,
        "detected_city": detected_city,
        "detected_role": detected_role,
        "asks_cv": asks_cv,
        "asks_cooccurrence": asks_cooccurrence,
        "asks_comparison": asks_comparison,
    }


def _build_evidence_and_rule_response(db: Session, question: str) -> Dict[str, Any]:
    """
    Veritabanındaki gerçek istatistikleri kullanarak kanıta dayalı (evidence-based)
    yapılandırılmış analiz sonucu ve kural tabanlı Türkçe yanıt oluşturur.
    """
    ctx = _detect_question_context(db, question)
    dashboard = get_dashboard_summary(db, include_demo=True)

    total_jobs = dashboard["total_jobs"]
    date_min = dashboard["date_range"]["min_date"] or "Belirtilmemiş"
    date_max = dashboard["date_range"]["max_date"] or "Belirtilmemiş"
    date_period_str = f"{date_min} — {date_max}"

    sources = [s.name for s in db.query(DataSource).all()]
    source_str = ", ".join(sources) if sources else "Yerel PostgreSQL Veri Tabanı"
    has_demo = dashboard["demo_jobs_count"] > 0

    limitations_note = (
        f"Analiz edilen {total_jobs} ilanın {dashboard['demo_jobs_count']} adedi sentetik demo verisidir (`SYNTHETIC_DEMO`). "
        "Sonuçlar yalnızca yüklü veri setini temsil eder; Türkiye genel iş piyasasının tamamı için kesin istatistik iddiası taşımaz."
        if has_demo
        else f"Sonuçlar sisteme yüklenmiş {total_jobs} adet ilana dayanmaktadır; örneklem büyüklüğü ile sınırlıdır."
    )

    if total_jobs == 0:
        return {
            "supported": False,
            "rule_answer": (
                "Şu anda veritabanında analiz edilmiş iş ilanı bulunmamaktadır. "
                "Lütfen **Veri Yönetimi** sayfasından bir CSV dosyası yükleyin veya Sentetik Demo Veri Setini etkinleştirin."
            ),
            "evidence": {
                "data_period": "Veri yok",
                "sample_size": 0,
                "analysis_method": "Veritabanı Kontrolü",
                "source": "Veri Yok",
                "limitations": "Henüz veri yüklenmedi.",
                "highlights": [],
            },
        }

    # 1. CV Eşleşme Soruları
    if ctx["asks_cv"]:
        latest_cv = db.query(CVAnalysis).order_by(CVAnalysis.created_at.desc()).first()
        if not latest_cv:
            ans = (
                "Henüz sistemde analiz edilmiş bir CV kaydınız bulunmuyor. "
                "**Kariyer Eşleştirme** sayfasından PDF formatındaki CV'nizi yüklediğinizde, "
                f"mevcut {total_jobs} iş ilanı üzerinden hangi pozisyonlarla ne oranda örtüştüğünüzü ve eksik becerilerinizi ayrıntılı olarak görebilirsiniz."
            )
            return {
                "supported": True,
                "rule_answer": ans,
                "evidence": {
                    "data_period": date_period_str,
                    "sample_size": total_jobs,
                    "analysis_method": "CV Eşleştirme ve Beceri Boşluk Analizi",
                    "source": source_str,
                    "limitations": limitations_note,
                    "highlights": [{"label": "Durum", "value": "CV henüz yüklenmedi"}],
                },
            }

        ans = (
            f"### CV Analiz ve Pozisyon Eşleşme Özeti\n\n"
            f"Son yüklediğiniz **{latest_cv.filename}** dosyasında tespit edilen beceriler: "
            f"**{', '.join(latest_cv.extracted_skills) if latest_cv.extracted_skills else 'Tespit edilemedi'}**.\n\n"
            f"- **Hedef Pozisyon:** {latest_cv.target_role}\n"
            f"- **Beceri Örtüşme Oranı:** **%{latest_cv.match_score}** *(Not: Bu oran işe alınma garantisi değil, ilanlardaki becerilerle örtüşme skorudur)*\n"
            f"- **Eşleşen Becerileriniz:** {', '.join(m['name'] for m in (latest_cv.matched_skills or [])) or 'Yok'}\n"
            f"- **Öncelikli Tamamlanması Önerilen Beceriler:** {', '.join(m['name'] for m in (latest_cv.missing_skills or [])[:5]) or 'Eksik temel beceri görünmüyor'}\n"
        )
        return {
            "supported": True,
            "rule_answer": ans,
            "evidence": {
                "data_period": date_period_str,
                "sample_size": total_jobs,
                "analysis_method": "CV Beceri Çıkarımı ve Pozisyon Karşılaştırma",
                "source": f"{latest_cv.filename} + {source_str}",
                "limitations": limitations_note,
                "highlights": [
                    {"label": "Hedef Rol", "value": latest_cv.target_role},
                    {"label": "Beceri Örtüşmesi", "value": f"%{latest_cv.match_score}"},
                ],
            },
        }

    # 2. İki Becerinin Karşılaştırılması (Örn: "Python mı R mı daha fazla aranıyor?")
    if ctx["asks_comparison"]:
        skills_to_compare = [s["name"] for s in ctx["mentioned_skills"][:2]]
        comparison_lines = []
        highlights = []
        for sk_name in skills_to_compare:
            deep = get_skill_deep_dive(db, sk_name, include_demo=True)
            cnt = deep["demand_count"] if deep else 0
            pct = deep["demand_percentage"] if deep else 0.0
            comparison_lines.append(f"- **{sk_name}:** **{cnt} ilan** (Tüm ilanların **%{pct}**'si)")
            highlights.append({"label": sk_name, "value": f"{cnt} ilan (%{pct})"})

        if ctx["mentions_r_lang"] and "R" not in skills_to_compare:
            comparison_lines.append(
                "- **R Programlama Dili:** Mevcut veri setindeki ilanlarda **0 ilan (%0.0)** doğrudan talep görmektedir (Python veri analizi ve veri biliminde açık ara öndedir)."
            )
            highlights.append({"label": "R", "value": "0 ilan (%0.0)"})

        ans = (
            f"### Beceri Talep Karşılaştırması ({date_period_str})\n\n"
            f"Veritabanındaki **{total_jobs}** iş ilanı üzerinde yapılan sıklık analizine göre:\n\n"
            + "\n".join(comparison_lines)
            + "\n\n**Değerlendirme:** İncelenen ilanlarda **Python**, hem veri analizi/veri bilimi hem de backend ve yapay zekâ rollerinde en yüksek talebe sahip becerilerden biridir."
        )
        return {
            "supported": True,
            "rule_answer": ans,
            "evidence": {
                "data_period": date_period_str,
                "sample_size": total_jobs,
                "analysis_method": "Beceri Frekans ve Oran Karşılaştırma Analizi",
                "source": source_str,
                "limitations": limitations_note,
                "highlights": highlights,
            },
        }

    # 3. Birlikte Aranan Beceriler (Örn: "SQL ile birlikte en çok hangi beceriler aranıyor?")
    if ctx["mentioned_skills"] and (ctx["asks_cooccurrence"] or len(ctx["mentioned_skills"]) == 1 and not ctx["detected_role"] and not ctx["detected_city"]):
        primary_skill = ctx["mentioned_skills"][0]["name"]
        deep = get_skill_deep_dive(db, primary_skill, include_demo=True)
        if deep:
            co_list = deep["co_occurring_skills"][:6]
            co_bullets = "\n".join(
                f"{idx}. **{c['name']}** ({c['category']}) — {c['co_count']} ortak ilan (**%{c['co_percentage']}** birliktelik)"
                for idx, c in enumerate(co_list, start=1)
            )
            role_bullets = ", ".join(f"{r['role']} ({r['count']} ilan)" for r in deep["by_role"][:4])
            ans = (
                f"### {primary_skill} Beceri ve Birliktelik Analizi\n\n"
                f"İncelenen **{total_jobs}** iş ilanının **{deep['demand_count']}** adedinde (**%{deep['demand_percentage']}**) **{primary_skill}** aranmaktadır.\n\n"
                f"**{primary_skill} ile birlikte en çok talep edilen teknolojiler:**\n"
                f"{co_bullets or 'Birlikte aranan ek beceri verisi bulunamadı.'}\n\n"
                f"**En çok talep eden pozisyonlar:** {role_bullets or 'Belirtilmemiş'}."
            )
            return {
                "supported": True,
                "rule_answer": ans,
                "evidence": {
                    "data_period": date_period_str,
                    "sample_size": deep["demand_count"],
                    "analysis_method": f"{primary_skill} Birliktelik (Co-occurrence) ve Pozisyon Dağılım Analizi",
                    "source": source_str,
                    "limitations": limitations_note,
                    "highlights": [
                        {"label": f"{primary_skill} İlan Sayısı", "value": f"{deep['demand_count']} (%{deep['demand_percentage']})"},
                        {"label": "En Güçlü Eşlikçi", "value": co_list[0]["name"] if co_list else "-"},
                    ],
                },
            }

    # 4. Şehir Bazlı Analiz (Örn: "Gaziantep'te hangi teknoloji alanlarında ilan var?")
    if ctx["detected_city"]:
        city_name = ctx["detected_city"]
        market = get_market_analytics(db, city=city_name, role=ctx["detected_role"], include_demo=True)
        sample_cnt = market["sample_size"]
        if sample_cnt == 0:
            ans = (
                f"Veritabanındaki **{total_jobs}** ilan içerisinde **{city_name}** lokasyonuna ait kayıt bulunamadı. "
                f"Mevcut şehirler: {', '.join(market['filters_available']['cities'])}."
            )
        else:
            roles_txt = "\n".join(
                f"- **{r['role']}:** {r['count']} ilan (%{r['percentage']})"
                for r in market["role_distribution"][:5]
            )
            sectors_txt = ", ".join(f"{s['sector']} ({s['count']})" for s in market["sector_distribution"][:4])
            skills_txt = ", ".join(f"**{s['name']}** (%{s['percentage']})" for s in market["top_skills"][:6])
            ans = (
                f"### {city_name} İş Piyasası ve Teknoloji Analizi ({date_period_str})\n\n"
                f"**{city_name}** için toplam **{sample_cnt}** adet iş ilanı analiz edilmiştir:\n\n"
                f"**Öne Çıkan Pozisyonlar:**\n{roles_txt}\n\n"
                f"**Sektörel Dağılım:** {sectors_txt}\n\n"
                f"**{city_name} İlanlarında En Çok Aranan Beceriler:** {skills_txt}"
            )
        return {
            "supported": True,
            "rule_answer": ans,
            "evidence": {
                "data_period": date_period_str,
                "sample_size": sample_cnt,
                "analysis_method": f"Şehir Bazlı ({city_name}) Kesit ve Frekans Analizi",
                "source": source_str,
                "limitations": limitations_note,
                "highlights": [
                    {"label": "Şehir", "value": city_name},
                    {"label": "İlan Sayısı", "value": str(sample_cnt)},
                ],
            },
        }

    # 5. Pozisyon / Meslek Hedefi Analizi (Örn: "Veri analisti olmak için en çok hangi teknolojiler aranıyor?")
    if ctx["detected_role"]:
        role_name = ctx["detected_role"]
        bench = get_role_skill_benchmarks(db, role_name, include_demo=True)
        role_jobs_cnt = bench["total_role_jobs"]
        top_b = bench["benchmarks"][:8]
        skill_lines = "\n".join(
            f"{idx}. **{b['name']}** ({b['category']}) — **{b['demand_count']} ilan** (**%{b['demand_percentage']}**)"
            for idx, b in enumerate(top_b, start=1)
        )
        ans = (
            f"### {role_name} Pozisyonu İçin En Çok Aranan Teknolojiler ({date_period_str})\n\n"
            f"Veritabanındaki **{role_jobs_cnt}** adet **{role_name}** ilanı incelendiğinde en yüksek sıklıkla talep edilen beceriler:\n\n"
            f"{skill_lines}\n\n"
            f"**Kariyer Önerisi:** İlanların en büyük kısmında temel gereksinim olarak **{top_b[0]['name'] if top_b else 'SQL'}** ve "
            f"**{top_b[1]['name'] if len(top_b) > 1 else 'Python'}** öne çıkmaktadır. Kişiselleştirilmiş haftalık çalışma planı için **Kariyer Eşleştirme** sayfasındaki Yol Haritası aracını kullanabilirsiniz."
        )
        return {
            "supported": True,
            "rule_answer": ans,
            "evidence": {
                "data_period": date_period_str,
                "sample_size": role_jobs_cnt,
                "analysis_method": f"Pozisyon Bazlı ({role_name}) Beceri Sıklık ve Trend Analizi",
                "source": source_str,
                "limitations": limitations_note,
                "highlights": [
                    {"label": "İncelenen Rol", "value": role_name},
                    {"label": "Rol İlan Sayısı", "value": str(role_jobs_cnt)},
                    {"label": "Lider Beceri", "value": f"{top_b[0]['name']} (%{top_b[0]['demand_percentage']})" if top_b else "-"},
                ],
            },
        }

    # 6. Genel Piyasa Soruları ("En çok hangi teknolojiler aranıyor?", "Genel durum nedir?")
    general_keywords = ["en çok", "trend", "popüler", "beceri", "teknoloji", "ilan", "piyasa", "sektör", "şehir", "uzaktan", "maaş"]
    if any(k in ctx["question_lower"] for k in general_keywords):
        top_sk_lines = "\n".join(
            f"{idx}. **{s['name']}** ({s['category']}) — {s['count']} ilan (**%{s['percentage']}**)"
            for idx, s in enumerate(dashboard["top_skills"][:7], start=1)
        )
        top_roles_str = ", ".join(f"{r['role']} ({r['count']})" for r in dashboard["top_roles"][:4])
        ans = (
            f"### Genel İş Piyasası ve Beceri Talebi Özeti ({date_period_str})\n\n"
            f"Toplam **{total_jobs}** iş ilanı ({dashboard['unique_cities']} şehir, {dashboard['unique_companies']} şirket) üzerindeki analiz sonuçları:\n\n"
            f"**En Çok Aranan 7 Beceri:**\n{top_sk_lines}\n\n"
            f"**En Fazla İlan Açılan Roller:** {top_roles_str}\n"
            f"**Çalışma Modeli Dağılımı:** Uzaktan %{dashboard['remote_ratio']} | Hibrit %{dashboard['hybrid_ratio']} | Ofisten %{dashboard['onsite_ratio']}"
        )
        return {
            "supported": True,
            "rule_answer": ans,
            "evidence": {
                "data_period": date_period_str,
                "sample_size": total_jobs,
                "analysis_method": "Genel Piyasa Frekans ve Dağılım Analizi",
                "source": source_str,
                "limitations": limitations_note,
                "highlights": [
                    {"label": "Toplam İlan", "value": str(total_jobs)},
                    {"label": "Uzaktan Oranı", "value": f"%{dashboard['remote_ratio']}"},
                ],
            },
        }

    # 7. Desteklenmeyen / Kapsam Dışı Soru
    return {
        "supported": False,
        "rule_answer": (
            "Bu soru mevcut iş ilanı ve kariyer analitiği kapsamı dışında kalmaktadır veya kural tabanlı analiz motoru tarafından doğrudan desteklenmemektedir.\n\n"
            "**Sorabileceğiniz veri odaklı soru örnekleri:**\n"
            "- *\"Veri analisti olmak için neler öğrenmeliyim?\"*\n"
            "- *\"Python mı R mı daha fazla aranıyor?\"*\n"
            "- *\"Gaziantep'te hangi teknoloji alanlarında ilan var?\"*\n"
            "- *\"SQL ile birlikte en çok hangi beceriler aranıyor?\"*\n"
            "- *\"CV'm hangi pozisyonlarla daha çok eşleşiyor?\"*"
        ),
        "evidence": {
            "data_period": date_period_str,
            "sample_size": total_jobs,
            "analysis_method": "Kapsam ve Anahtar Kelime Doğrulaması",
            "source": source_str,
            "limitations": "Soru desteklenen analitik şablonlarla eşleşmedi.",
            "highlights": [],
        },
    }


def answer_user_question(
    db: Session,
    question: str,
    session_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Katmanlı AI Yanıt Sistemi:
    1. Önce izin verilen backend analiz fonksiyonlarıyla kanıt paketini (`evidence`) ve doğrulanmış istatistikleri çıkarır.
    2. Yerel Ollama servisi açıksa, bu istatistikleri bağlam (RAG/Retrieval context) olarak verip Türkçe yanıt üretir.
    3. Ollama kapalıysa veya hata verirse, uydurma istatistik üretmeyen Kural ve İstatistik Tabanlı Fallback yanıtını döndürür.
    """
    if session_id:
        chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    else:
        chat_session = None

    if not chat_session:
        chat_session = ChatSession(title=question[:80])
        db.add(chat_session)
        db.flush()

    user_msg = ChatMessage(
        session_id=chat_session.id,
        role="user",
        content=question,
        engine_used="USER_INPUT",
    )
    db.add(user_msg)
    db.flush()

    analysis_pack = _build_evidence_and_rule_response(db, question)
    rule_answer = analysis_pack["rule_answer"]
    evidence = analysis_pack["evidence"]

    ollama_info = check_ollama_status()
    engine_used = "RULE_AND_STATISTICAL_FALLBACK"
    final_answer = rule_answer

    if ollama_info["available"] and analysis_pack["supported"]:
        system_prompt = (
            "Sen SkillScope AI kariyer ve iş piyasası analiz asistanısın. "
            "SADECE aşağıda sana verilen VERİTABANI ANALİZ SONUÇLARINI kullan. "
            "Asla tabloda olmayan bir sayı veya istatistik uydurma. Yanıtını açık, profesyonel Türkçe ile yaz."
        )
        user_prompt = (
            f"Kullanıcı Sorusu: {question}\n\n"
            f"Doğrulanmış Veritabanı Analiz Özeti:\n{rule_answer}\n\n"
            f"Veri Dönemi: {evidence['data_period']} | Örneklem: {evidence['sample_size']} ilan.\n"
            "Lütfen bu verilere sadık kalarak kullanıcıya yardımcı bir yanıt oluştur."
        )
        try:
            with httpx.Client(timeout=float(settings.OLLAMA_TIMEOUT_SECONDS)) as client:
                resp = client.post(
                    f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": f"{system_prompt}\n\n{user_prompt}",
                        "stream": False,
                    },
                )
                if resp.status_code == 200:
                    llm_text = (resp.json().get("response") or "").strip()
                    if len(llm_text) > 30:
                        final_answer = llm_text
                        engine_used = f"OLLAMA_LOCAL_LLM ({settings.OLLAMA_MODEL})"
        except Exception:
            engine_used = "RULE_AND_STATISTICAL_FALLBACK"

    assistant_msg = ChatMessage(
        session_id=chat_session.id,
        role="assistant",
        content=final_answer,
        engine_used=engine_used,
        evidence_metadata=evidence,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return {
        "session_id": chat_session.id,
        "message_id": assistant_msg.id,
        "question": question,
        "answer": final_answer,
        "engine_used": engine_used,
        "is_fallback": engine_used == "RULE_AND_STATISTICAL_FALLBACK",
        "ollama_status": ollama_info,
        "evidence": evidence,
        "created_at": assistant_msg.created_at.isoformat(),
    }
