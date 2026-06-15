from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.integrations.stripe_client import verify_webhook_signature
from app.models import ProcessedStripeEvent
from app.services.billing_service import handle_stripe_webhook

router = APIRouter(prefix="/v1/webhooks", tags=["Webhooks"])

@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook_signature(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # event can be a stripe.Event or a dict if mocked
    if isinstance(event, dict):
        event_id = event.get("id", "")
        event_type = event.get("type")
        data = event.get("data", {})
    else:
        event_id = event.id
        event_type = event.type
        data = event.data

    # Idempotency guard — Stripe retries on timeout; don't process the same event twice
    if event_id and db.get(ProcessedStripeEvent, event_id):
        return {"status": "already_processed"}

    handle_stripe_webhook(db, event_type, data)

    if event_id:
        db.add(ProcessedStripeEvent(stripe_event_id=event_id))
    db.commit()

    return {"status": "success"}
