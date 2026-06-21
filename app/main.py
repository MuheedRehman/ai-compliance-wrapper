from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.errors import register_exception_handlers
from app.limiter import limiter
from app.routes.chat import router as chat_router
from app.routes.features import router as features_router
from app.routes.logs import router as logs_router
from app.routes.evidence import router as evidence_router
from app.routes.reviews import router as reviews_router
from app.routes.ai_systems import router as ai_systems_router
from app.routes.billing import router as billing_router
from app.routes.webhooks_stripe import router as webhooks_router
from app.routes.classification import router as classification_router
from app.routes.obligations import router as obligations_router
from app.routes.reports import router as reports_router
from app.routes.compliance import router as compliance_router
from app.routes.website_scans import router as website_scans_router
from app.routes.tenant_admin import router as tenant_admin_router
from app.routes.runtime import router as runtime_router
from app.config import FRONTEND_URL

app = FastAPI(title="AI Compliance & Governance Wrapper", version="0.5.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _cors_origins() -> list[str]:
    origins = [origin.strip() for origin in FRONTEND_URL.split(",") if origin.strip()]
    return origins or ["http://localhost:3000"]


cors_origins = _cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    # Explicit allowlist — x-dashboard-user-role is intentionally excluded
    # (it is set by the server-side Next.js proxy, never by the browser directly)
    allow_headers=["x-api-key", "content-type", "accept", "authorization", "x-request-id"],
    expose_headers=["x-request-id"],
    max_age=600,
)

app.include_router(chat_router)
app.include_router(features_router)
app.include_router(logs_router)
app.include_router(evidence_router)
app.include_router(reviews_router)
app.include_router(ai_systems_router)
app.include_router(billing_router)
app.include_router(webhooks_router)
app.include_router(classification_router)
app.include_router(obligations_router)
app.include_router(reports_router)
app.include_router(compliance_router)
app.include_router(website_scans_router)
app.include_router(tenant_admin_router)
app.include_router(runtime_router)

register_exception_handlers(app)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"status": "ok", "service": "AI Compliance API"}
