"""Runtime configuration, loaded from the environment."""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

# Fixed demo organization IDs. These match supabase/seed.sql so a freshly
# seeded database and the in-memory fallback agree on who is talking.
DEMO_PROVIDER_ORG_ID = "11111111-1111-4111-8111-111111111111"
DEMO_PAYER_ORG_ID = "22222222-2222-4222-8222-222222222222"

PROVIDER_AGENT_ID = "agent://pavo/provider/metro-valley"
PAYER_AGENT_ID = "agent://pavo/payer/meridian"


class Settings:
    """Process configuration. Read once at import, overridable in tests."""

    def __init__(self) -> None:
        self.supabase_url: str = os.getenv("SUPABASE_URL", "").strip()
        self.supabase_service_role_key: str = os.getenv(
            "SUPABASE_SERVICE_ROLE_KEY", ""
        ).strip()
        self.anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.aria_version: str = os.getenv("ARIA_VERSION", "1.0")
        self.ml_classifier_threshold: float = float(
            os.getenv("ML_CLASSIFIER_THRESHOLD", "0.75")
        )
        self.appeal_confidence_threshold: float = float(
            os.getenv("APPEAL_CONFIDENCE_THRESHOLD", "0.70")
        )
        self.frontend_origin: str = os.getenv(
            "FRONTEND_ORIGIN", "http://localhost:3000"
        )

    @property
    def supabase_configured(self) -> bool:
        """True when both Supabase credentials are present."""
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
