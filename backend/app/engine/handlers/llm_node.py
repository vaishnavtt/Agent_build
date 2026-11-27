import json
from typing import Dict, Any
import httpx
from app.core.config import settings
from app.engine.handlers.base import BaseNodeHandler, get_node_meta
from app.engine.security import redact_text
from app.engine.types import ExecutionContext, NodeExecutionError, GeminiConfigError
from app.schemas.execution import TokenUsage


class LLMNodeHandler(BaseNodeHandler):
    """Handler for Gemini LLM reasoning nodes with actual API call and token tracking."""

    def __init__(self):
        super().__init__("LLM")

    async def execute(
        self,
        node: Dict[str, Any],
        incoming_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        node_id, node_name, config = get_node_meta(node, "LLM Node")

        model = config.get("model", settings.GEMINI_DEFAULT_MODEL) or "gemini-1.5-pro"
        system_prompt = config.get("systemPrompt", "You are a helpful and precise assistant.")
        temperature = float(config.get("temperature", 0.7))
        max_output_tokens = config.get("maxOutputTokens")
        response_format = str(config.get("responseFormat", "text")).lower()
        instructions = config.get("instructions") or config.get("prompt", "")

        # API key verification
        api_key = config.get("apiKey") or settings.GEMINI_API_KEY
        if not api_key:
            raise GeminiConfigError(
                f"Gemini API key is not configured for node '{node_name}' ({node_id}). "
                f"Set GEMINI_API_KEY in the environment or provide it in the node config.",
                node_id=node_id,
            )

        # Assemble prompt from node instructions + incoming upstream context
        context_parts = []
        if instructions:
            context_parts.append(instructions)

        # Extract textual content from incoming upstream data
        for k, v in incoming_data.items():
            if isinstance(v, dict):
                text_val = v.get("text") or v.get("content") or v.get("response") or v.get("output")
                if text_val:
                    context_parts.append(f"[{k}]: {text_val}")
                else:
                    context_parts.append(f"[{k}]: {json.dumps(v)}")
            elif isinstance(v, (str, int, float, bool)):
                context_parts.append(f"[{k}]: {v}")

        full_user_prompt = "\n\n".join(context_parts)
        if not full_user_prompt.strip():
            full_user_prompt = "Process the provided workflow context."

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        gen_config: Dict[str, Any] = {"temperature": temperature}
        if max_output_tokens is not None:
            gen_config["maxOutputTokens"] = int(max_output_tokens)
        if response_format == "json_object":
            gen_config["responseMimeType"] = "application/json"

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": full_user_prompt}],
                }
            ],
            "generationConfig": gen_config,
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(endpoint, json=payload)
            except httpx.TimeoutException:
                raise NodeExecutionError(
                    f"Gemini API call timed out after 60 seconds for node '{node_name}'.",
                    node_id=node_id,
                )
            except Exception as e:
                raise NodeExecutionError(
                    redact_text(f"Network error communicating with Gemini API: {str(e)}"),
                    node_id=node_id,
                )

        self.api_calls_made = 1

        if resp.status_code != 200:
            error_detail = resp.text
            try:
                err_json = resp.json()
                error_detail = err_json.get("error", {}).get("message", resp.text)
            except Exception:
                pass
            raise NodeExecutionError(
                redact_text(f"Gemini API error ({resp.status_code}) on node '{node_name}': {error_detail}"),
                node_id=node_id,
            )

        resp_data = resp.json()

        # Extract generated content
        candidates = resp_data.get("candidates", [])
        if not candidates:
            raise NodeExecutionError(
                f"Gemini returned an empty candidate list on node '{node_name}'.",
                node_id=node_id,
            )

        parts = candidates[0].get("content", {}).get("parts", [])
        response_text = "".join(part.get("text", "") for part in parts)

        # Extract actual provider token usage
        usage_meta = resp_data.get("usageMetadata", {})
        prompt_tokens = usage_meta.get("promptTokenCount", 0)
        completion_tokens = usage_meta.get("candidatesTokenCount", 0)
        total_tokens = usage_meta.get("totalTokenCount", prompt_tokens + completion_tokens)

        self.token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        return {
            "response": response_text,
            "text": response_text,
            "output": response_text,
            "model": model,
            "tokens": self.token_usage.model_dump(),
        }
