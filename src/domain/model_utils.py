"""Model utilities for provider detection."""


def detect_provider(model_name: str) -> str:
    """Detect provider from model name patterns."""
    model_lower = model_name.lower()
    
    if model_lower.startswith("gpt-") or "gpt" in model_lower:
        return "openai"
    elif model_lower.startswith("claude-") or "claude" in model_lower:
        return "anthropic"
    elif model_lower.startswith("gemini-") or "gemini" in model_lower:
        return "google"
    elif model_lower.startswith(('command', 'embed')):
        return 'cohere'
    elif model_lower.startswith(('mistral', 'mixtral')):
        return 'mistral'
    else:
        # Default fallback - try openai first as most common
        return "openai"