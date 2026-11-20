"""Gemini AI Client - Centralized Google Gemini API integration.

Uses google-generativeai SDK when available, with urllib fallback.
API key is strictly server-side only - never sent to frontend.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


def call_gemini(
    prompt: str,
    system_instruction: str = "",
    model: str = "gemini-1.5-pro",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> Optional[str]:
    """
    Calls the Gemini API using the google-generativeai SDK or urllib fallback.
    
    Returns the generated text, or None if the call fails or key is not set.
    API key is loaded strictly from environment / .env file on the server.
    """
    from app.core.config import settings
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return None

    # Try google-generativeai SDK first
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model_obj = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction or None,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )
        response = model_obj.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"google-generativeai SDK call failed: {e}. Trying urllib fallback.")

    # Urllib fallback (no extra dependencies)
    try:
        import urllib.request
        import json

        full_prompt = f"System Instructions: {system_instruction}\n\nTask: {prompt}" if system_instruction else prompt
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
            f":generateContent?key={api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except Exception as e:
        logger.warning(f"Gemini urllib fallback also failed: {e}")

    return None
