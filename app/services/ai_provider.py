from openai import OpenAI
from app.config import AI_PROVIDER_MODE, OPENAI_API_KEY, DEFAULT_MODEL

_client = None


def get_openai_client() -> OpenAI:
    global _client
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing")
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def call_ai_provider(provider: str, messages: list[dict], model: str | None, max_tokens: int) -> dict:
    if provider != "openai":
        raise ValueError(f"Unsupported provider: {provider}")

    selected_model = model or DEFAULT_MODEL
    if AI_PROVIDER_MODE == "demo":
        prompt = "\n".join(message.get("content", "") for message in messages if message.get("role") == "user")
        output_text = (
            "Demo provider response: this request passed through the governance pipeline. "
            "For high-risk AI systems under the EU AI Act, maintain risk management, data governance, "
            "technical documentation, logging, human oversight, accuracy/cybersecurity controls, "
            "post-market monitoring, and incident reporting evidence. "
            f"Request summary: {prompt[:240]}"
        )
        return {
            "provider": "demo",
            "model": f"{selected_model}-demo",
            "output_text": output_text[: max(1, max_tokens) * 8],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(output_text.split()),
                "total_tokens": len(prompt.split()) + len(output_text.split()),
            },
            "finish_reason": "stop",
            "provider_response_id": "demo-response",
        }

    client = get_openai_client()
    response = client.chat.completions.create(model=selected_model, messages=messages, max_tokens=max_tokens, timeout=30)
    output_text = response.choices[0].message.content or ""
    finish_reason = response.choices[0].finish_reason
    usage = {}
    if response.usage:
        usage = {"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens, "total_tokens": response.usage.total_tokens}

    return {"provider": provider, "model": selected_model, "output_text": output_text, "usage": usage, "finish_reason": finish_reason, "provider_response_id": response.id}
