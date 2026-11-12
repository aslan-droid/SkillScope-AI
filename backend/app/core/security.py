import hashlib
import hmac
import os
import re


def hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256 ile güvenli parola özetleme (ücretsiz, sıfır dış bağımlılık)."""
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256$120000${salt}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Özetlenmiş parolayı doğrular."""
    try:
        algorithm, iterations, salt, stored_hash = hashed_password.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
        return hmac.compare_digest(dk.hex(), stored_hash)
    except Exception:
        return False


def compute_job_fingerprint(title: str, company: str, location: str, description: str) -> str:
    """Mükerrer (duplicate) iş ilanlarını engellemek için normalize edilmiş SHA-256 özeti üretir."""
    normalized = "|".join(
        [
            re.sub(r"\s+", " ", (title or "").strip().lower()),
            re.sub(r"\s+", " ", (company or "").strip().lower()),
            re.sub(r"\s+", " ", (location or "").strip().lower()),
            re.sub(r"\s+", " ", (description or "").strip().lower()[:400]),
        ]
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
