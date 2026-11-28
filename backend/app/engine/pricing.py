"""Model-specific pricing calculations based on official provider documentation."""

from typing import Dict, Optional

# Pricing rates per 1,000,000 tokens (USD)
# Source: Google Cloud & Google AI Studio official Gemini API pricing
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Gemini 1.5 Pro (prompts <= 128k: $1.25, output: $5.00)
    "gemini-1.5-pro": {
        "prompt_rate_per_m": 1.25,
        "completion_rate_per_m": 5.00,
    },
    "gemini-1.5-pro-latest": {
        "prompt_rate_per_m": 1.25,
        "completion_rate_per_m": 5.00,
    },
    # Gemini 1.5 Flash (prompts <= 128k: $0.075, output: $0.30)
    "gemini-1.5-flash": {
        "prompt_rate_per_m": 0.075,
        "completion_rate_per_m": 0.30,
    },
    "gemini-1.5-flash-latest": {
        "prompt_rate_per_m": 0.075,
        "completion_rate_per_m": 0.30,
    },
    # Gemini 1.5 Flash-8B (prompts: $0.0375, output: $0.15)
    "gemini-1.5-flash-8b": {
        "prompt_rate_per_m": 0.0375,
        "completion_rate_per_m": 0.15,
    },
    # Gemini 2.0 Flash (prompts: $0.10, output: $0.40)
    "gemini-2.0-flash": {
        "prompt_rate_per_m": 0.10,
        "completion_rate_per_m": 0.40,
    },
    "gemini-2.0-flash-exp": {
        "prompt_rate_per_m": 0.10,
        "completion_rate_per_m": 0.40,
    },
    # Gemini 1.0 Pro legacy (prompts: $0.50, output: $1.50)
    "gemini-1.0-pro": {
        "prompt_rate_per_m": 0.50,
        "completion_rate_per_m": 1.50,
    },
    "gemini-pro": {
        "prompt_rate_per_m": 0.50,
        "completion_rate_per_m": 1.50,
    },
}

DEFAULT_MODEL_FALLBACK = "gemini-1.5-pro"


def calculate_estimated_cost_usd(
    model: Optional[str],
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Calculates estimated execution cost in USD based on verified model rates.

    Safely handles missing or zero token counts and falls back to base model pricing.
    """
    if prompt_tokens <= 0 and completion_tokens <= 0:
        return 0.0

    model_key = (model or DEFAULT_MODEL_FALLBACK).strip().lower()
    rates = MODEL_PRICING.get(model_key)
    if not rates:
        for known_key in MODEL_PRICING:
            if known_key in model_key or model_key in known_key:
                rates = MODEL_PRICING[known_key]
                break
    if not rates:
        rates = MODEL_PRICING[DEFAULT_MODEL_FALLBACK]

    prompt_cost = (max(0, prompt_tokens) / 1_000_000.0) * rates["prompt_rate_per_m"]
    completion_cost = (max(0, completion_tokens) / 1_000_000.0) * rates["completion_rate_per_m"]
    return round(prompt_cost + completion_cost, 6)
