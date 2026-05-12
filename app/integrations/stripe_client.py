import stripe
from app.config import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, FRONTEND_URL
from typing import Optional, Dict, Any

stripe.api_key = STRIPE_API_KEY

def create_checkout_session(tenant_id: str, plan_id: str) -> str:
    """Create a Stripe checkout session for a tenant."""
    # In a real implementation, we'd lookup or create a Stripe Customer ID here.
    # For this exercise, we mock the session URL.
    if STRIPE_API_KEY == "sk_test_mock":
        return f"{FRONTEND_URL}/mock-checkout?tenant_id={tenant_id}&plan={plan_id}"
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': plan_id, # Assumes plan_id is a valid Stripe Price ID
            'quantity': 1,
        }],
        mode='subscription',
        success_url=f'{FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{FRONTEND_URL}/cancel',
        client_reference_id=tenant_id,
    )
    return session.url


def create_portal_session(stripe_customer_id: str) -> str:
    """Create a Stripe customer portal session."""
    if STRIPE_API_KEY == "sk_test_mock":
        return f"{FRONTEND_URL}/mock-portal?customer={stripe_customer_id}"
        
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f'{FRONTEND_URL}/dashboard',
    )
    return session.url


def verify_webhook_signature(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify the Stripe webhook signature."""
    if STRIPE_WEBHOOK_SECRET == "whsec_mock":
        # Mock behavior for testing
        import json
        data = json.loads(payload)
        return stripe.Event.construct_from(data, stripe.api_key)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        return event
    except stripe.error.SignatureVerificationError as e:
        raise ValueError("Invalid signature") from e
    except Exception as e:
        raise ValueError(f"Webhook error: {str(e)}") from e
