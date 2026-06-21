from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional at runtime
    pass


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = PROJECT_ROOT / ".cache"


@dataclass(frozen=True)
class Settings:
    dip_api_key: str
    dip_base_url: str
    groq_api_key: str | None
    groq_model: str
    cache_dir: Path
    cache_enabled: bool
    request_timeout: int

    @classmethod
    def from_env(cls) -> "Settings":
        dip_key = os.getenv("DIP_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        # Deferred import avoids a circular dependency at module load.
        try:
            from .observability.audit import security_auth_source

            security_auth_source(
                "dip", source="env" if dip_key else "public_fallback"
            )
            security_auth_source(
                "groq", source="env" if groq_key else "missing"
            )
        except Exception:
            pass
        return cls(
            dip_api_key=dip_key,
            dip_base_url=os.getenv(
                "DIP_BASE_URL", "https://search.dip.bundestag.de/api/v1"
            ),
            groq_api_key=groq_key,
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            cache_dir=Path(os.getenv("DIP_CACHE_DIR", str(DEFAULT_CACHE_DIR))),
            cache_enabled=os.getenv("DIP_CACHE_ENABLED", "true").lower() == "true",
            request_timeout=int(os.getenv("DIP_REQUEST_TIMEOUT", "60")),
        )


settings = Settings.from_env()
