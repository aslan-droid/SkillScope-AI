import re
from typing import Any, Dict, List, Optional, Sequence
from sqlalchemy.orm import Session

from app.models.entities import Skill
from app.nlp.skill_catalog import DEFAULT_SKILLS_CATALOG


def _normalize_turkish_lower(text: str) -> str:
    """Türkçe büyük/küçük harf dönüşümünü doğru yapan yardımcı fonksiyon."""
    if not text:
        return ""
    text = text.replace("İ", "i").replace("I", "ı")
    return text.lower()


def _build_term_pattern(term: str) -> re.Pattern:
    """
    C#, C++, .NET, Power BI, SQL'de gibi özel karakterli veya Türkçe ek almış
    terimleri yanlış pozitif üretmeden yakalayan regex deseni oluşturur.
    """
    norm_term = _normalize_turkish_lower(term.strip())
    escaped = re.escape(norm_term)
    # Boşlukları esnek boşluk veya tire ile eşleştir (örn: "power bi" -> "power[\s\-]*bi")
    escaped = escaped.replace(r"\ ", r"[\s\-]+")
    # Kelime başlangıcı: harf veya rakam olmayan bir sınır veya satır başı
    # Kelime sonu: Türkçe kesme işareti (') veya boşluk/noktalama veya satır sonu
    pattern_str = rf"(?<![a-z0-9çğıöşü]){escaped}(?=(?:['’][a-zçğıöşü]+)?(?![a-z0-9çğıöşü]))"
    return re.compile(pattern_str, re.IGNORECASE)


class SkillExtractor:
    """
    Yönetilebilir beceri sözlüğü üzerinden iş ilanları ve CV metinlerinden
    beceri çıkarımı, normalizasyon ve kategori gruplaması yapan modüler NLP motoru.
    """

    def __init__(self, skills_definitions: Optional[Sequence[Dict[str, Any]]] = None):
        self.catalog: List[Dict[str, Any]] = list(skills_definitions or DEFAULT_SKILLS_CATALOG)
        self._compiled_rules: List[Dict[str, Any]] = []
        self._compile()

    @classmethod
    def from_db(cls, db: Session) -> "SkillExtractor":
        db_skills = db.query(Skill).filter(Skill.is_active.is_(True)).all()
        if not db_skills:
            return cls(DEFAULT_SKILLS_CATALOG)
        defs = [
            {
                "id": s.id,
                "name": s.name,
                "slug": s.slug,
                "category": s.category,
                "aliases": s.aliases or [],
                "prerequisites": s.prerequisites or [],
                "estimated_hours": s.estimated_hours,
                "learning_resources": s.learning_resources or [],
            }
            for s in db_skills
        ]
        return cls(defs)

    def _compile(self) -> None:
        self._compiled_rules = []
        for item in self.catalog:
            terms = [item["name"]] + list(item.get("aliases", []))
            # Uzun terimleri önce değerlendir
            unique_terms = sorted(set(t.strip() for t in terms if t and t.strip()), key=len, reverse=True)
            patterns = [(t, _build_term_pattern(t)) for t in unique_terms]
            self._compiled_rules.append(
                {
                    "id": item.get("id"),
                    "name": item["name"],
                    "slug": item["slug"],
                    "category": item["category"],
                    "prerequisites": item.get("prerequisites", []),
                    "estimated_hours": item.get("estimated_hours", 20),
                    "learning_resources": item.get("learning_resources", []),
                    "patterns": patterns,
                }
            )

    def extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """
        Verilen metinden tekilleştirilmiş beceri listesi çıkarır.
        Her öğe: {name, slug, category, matched_term, confidence, id}
        """
        if not text or not text.strip():
            return []

        norm_text = _normalize_turkish_lower(text)
        extracted: List[Dict[str, Any]] = []
        seen_slugs = set()

        for rule in self._compiled_rules:
            if rule["slug"] in seen_slugs:
                continue
            for raw_term, pattern in rule["patterns"]:
                match = pattern.search(norm_text)
                if match:
                    seen_slugs.add(rule["slug"])
                    extracted.append(
                        {
                            "id": rule.get("id"),
                            "name": rule["name"],
                            "slug": rule["slug"],
                            "category": rule["category"],
                            "matched_term": raw_term,
                            "confidence": 1.0 if _normalize_turkish_lower(raw_term) == _normalize_turkish_lower(rule["name"]) else 0.95,
                        }
                    )
                    break

        return extracted

    def group_by_category(self, extracted_skills: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        grouped: Dict[str, List[str]] = {}
        for item in extracted_skills:
            cat = item["category"]
            grouped.setdefault(cat, [])
            if item["name"] not in grouped[cat]:
                grouped[cat].append(item["name"])
        return grouped


def normalize_role_title(raw_title: str) -> str:
    """
    Farklı şekillerde yazılmış iş ilanı başlıklarını standart meslek gruplarına normalize eder.
    """
    t = _normalize_turkish_lower(raw_title or "")
    if any(k in t for k in ["veri analist", "data analyst", "bi analyst", "iş zekası", "is zekasi", "raporlama uzman"]):
        return "Veri Analisti"
    if any(k in t for k in ["veri bilim", "data scientist", "data science"]):
        return "Veri Bilimci"
    if any(k in t for k in ["yapay zeka", "yapay zekâ", "ai engineer", "machine learning", "ml engineer", "nlp", "derin öğrenme"]):
        return "Yapay Zekâ / ML Mühendisi"
    if any(k in t for k in ["veri mühendis", "data engineer", "etl", "big data"]):
        return "Veri Mühendisi"
    if any(k in t for k in ["frontend", "front-end", "react", "arayüz geliştirici", "ui developer"]):
        return "Frontend Geliştirici"
    if any(k in t for k in ["backend", "back-end", "java developer", ".net developer", "python developer"]):
        return "Backend Geliştirici"
    if any(k in t for k in ["full stack", "fullstack", "full-stack", "yazılım mühendis", "yazilim muhendis", "software engineer", "yazılım geliştirici"]):
        return "Full-Stack / Yazılım Mühendisi"
    if any(k in t for k in ["devops", "cloud", "bulut", "sre", "sistem mühendis", "linux", "kubernetes", "ağ uzman", "network"]):
        return "DevOps & Sistem Mühendisi"
    if any(k in t for k in ["siber güvenlik", "cyber security", "security analyst", "pentest", "soc analyst", "güvenlik uzman"]):
        return "Siber Güvenlik Uzmanı"
    if any(k in t for k in ["iş analist", "is analist", "business analyst", "product owner", "proje yönetici", "scrum master"]):
        return "İş Analisti / Ürün Yöneticisi"
    return raw_title.strip() if raw_title and raw_title.strip() else "Genel Teknoloji Uzmanı"
