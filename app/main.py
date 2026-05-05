from fastapi import FastAPI
from app.errors import register_exception_handlers
from app.routes.chat import router as chat_router
from app.routes.features import router as features_router
from app.routes.logs import router as logs_router
from app.routes.reviews import router as reviews_router
from app.routes.ai_systems import router as ai_systems_router
from app.config import EVIDENCE_CHAIN_MODE

app = FastAPI(title="AI Compliance & Governance Wrapper", version="0.5.0")

app.include_router(chat_router)
app.include_router(features_router)
app.include_router(logs_router)
app.include_router(reviews_router)
app.include_router(ai_systems_router)

register_exception_handlers(app)


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "AI Compliance & Governance Wrapper",
        "version": "0.5.0",
        "sprint": "Phase 3 Registry Endpoints",
        "evidence_chain": EVIDENCE_CHAIN_MODE,
    }
