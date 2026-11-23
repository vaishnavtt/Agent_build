"""Gemini AI Client - Centralized Google Gemini API integration.

Uses google-generativeai SDK when available, with urllib fallback.
API key is strictly server-side only - never sent to frontend.
Handles rate limits, timeouts, model variations, and structured JSON generation.
"""

from typing import Optional, Dict, Any, Tuple
import logging
import json
import re
import time

logger = logging.getLogger(__name__)


def call_gemini(
    prompt: str,
    system_instruction: str = "",
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 25,
) -> Optional[str]:
    """
    Calls the Gemini API using the google-generativeai SDK or urllib fallback.
    
    Returns the generated text, or None if the call fails or key is not set.
    API key is loaded strictly from environment / .env file on the server.
    """
    from app.core.config import settings

    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.debug("GEMINI_API_KEY not set or using placeholder value.")
        return None

    target_model = model or getattr(settings, "GEMINI_DEFAULT_MODEL", "gemini-1.5-pro")

    # Try google-generativeai SDK first
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model_obj = genai.GenerativeModel(
            model_name=target_model,
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
        logger.debug("google-generativeai package not installed. Using urllib fallback.")
    except Exception as e:
        err_str = str(e).lower()
        if "quota" in err_str or "429" in err_str or "resource_exhausted" in err_str:
            logger.warning(f"Gemini API rate limit / quota exceeded for model {target_model}: {e}")
        elif "not_found" in err_str or "404" in err_str:
            logger.warning(f"Gemini model '{target_model}' not found or unavailable: {e}")
        elif "api_key" in err_str or "401" in err_str or "403" in err_str:
            logger.warning(f"Gemini API key invalid or unauthorized: {e}")
        else:
            logger.warning(f"google-generativeai SDK call failed: {e}. Trying urllib fallback.")

    # Urllib fallback (no extra dependencies)
    try:
        import urllib.request
        import urllib.error

        full_prompt = f"System Instructions: {system_instruction}\n\nTask: {prompt}" if system_instruction else prompt
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}"
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
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except urllib.error.HTTPError as http_err:
        if http_err.code == 429:
            logger.warning(f"Gemini HTTP 429: Rate limit or quota reached on model {target_model}.")
        elif http_err.code in (401, 403):
            logger.warning("Gemini HTTP 401/403: API key invalid or lacks permission.")
        elif http_err.code == 404:
            logger.warning(f"Gemini HTTP 404: Model {target_model} not found.")
        else:
            logger.warning(f"Gemini HTTP error {http_err.code}: {http_err.reason}")
    except urllib.error.URLError as url_err:
        logger.warning(f"Gemini connection / timeout error: {url_err.reason}")
    except Exception as e:
        logger.warning(f"Gemini urllib fallback exception: {e}")

    return None


def call_gemini_json(
    prompt: str,
    system_instruction: str = "",
    model: Optional[str] = None,
    temperature: float = 0.2,
    timeout: int = 25,
) -> Optional[dict]:
    """
    Calls Google Gemini API expecting a structured JSON response.
    Parses JSON safely from Markdown codeblocks or raw text.
    Returns parsed dictionary or None on failure.
    """
    from app.core.config import settings

    target_model = model or getattr(settings, "GEMINI_DEFAULT_MODEL", "gemini-1.5-pro")
    json_system_prompt = (
        (system_instruction + "\n\n" if system_instruction else "")
        + "CRITICAL: You MUST respond ONLY with valid JSON conforming to the requested schema. "
        "Do not include any conversational preamble, commentary, or markdown formatting outside the JSON."
    )

    raw_text = call_gemini(
        prompt=prompt,
        system_instruction=json_system_prompt,
        model=target_model,
        temperature=temperature,
        max_tokens=4096,
        timeout=timeout,
    )

    if not raw_text:
        return None

    # Clean code block if present
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Attempt to find the first valid JSON object / array in the text
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        logger.warning(f"Failed to parse Gemini response as JSON: {raw_text[:200]}")
        return None
