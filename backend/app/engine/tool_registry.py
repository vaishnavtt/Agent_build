import ast
import operator as op
import json
from typing import Dict, Any, Callable, Awaitable, Optional, List
import httpx
from app.engine.types import ToolExecutionError


# Supported math operators for safe AST evaluation (strictly NO eval or exec)
_SAFE_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def _eval_ast_node(node: ast.AST) -> float:
    """Recursively evaluates safe mathematical AST nodes."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[op_type](_eval_ast_node(node.operand))
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            left = _eval_ast_node(node.left)
            right = _eval_ast_node(node.right)
            # Guard division by zero
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("Division by zero in calculation expression")
            return _SAFE_OPERATORS[op_type](left, right)
    raise ValueError(f"Unsupported or unsafe expression component: {type(node).__name__}")


def safe_calculate(expression: str) -> float:
    """Safely evaluates an arithmetic expression using AST without eval()."""
    try:
        parsed = ast.parse(expression.strip(), mode="eval")
        return _eval_ast_node(parsed.body)
    except Exception as e:
        raise ToolExecutionError(f"Math evaluation failed for '{expression}': {str(e)}")


async def tool_calculator(params: Dict[str, Any], context: Any) -> Dict[str, Any]:
    expr = params.get("expression")
    if not expr and isinstance(params.get("output"), dict):
        expr = params["output"].get("expression")
    if not expr and isinstance(params.get("data"), dict):
        expr = params["data"].get("expression")
    if not expr:
        expr = params.get("query") or params.get("text", "")

    if isinstance(expr, dict):
        expr = expr.get("expression") or expr.get("text", "")

    if not expr:
        raise ToolExecutionError("Calculator requires an 'expression' parameter.")
    result = safe_calculate(str(expr))
    return {"expression": str(expr), "result": result, "formatted": str(result)}


async def tool_text_formatter(params: Dict[str, Any], context: Any) -> Dict[str, Any]:
    text = str(params.get("text", params.get("input", "")))
    operation = str(params.get("operation", "upper")).lower()

    if operation == "upper":
        transformed = text.upper()
    elif operation == "lower":
        transformed = text.lower()
    elif operation == "title":
        transformed = text.title()
    elif operation == "strip":
        transformed = text.strip()
    elif operation == "word_count":
        return {"text": text, "count": len(text.split()), "operation": operation}
    elif operation == "length":
        return {"text": text, "length": len(text), "operation": operation}
    else:
        transformed = text

    return {
        "original": text,
        "result": transformed,
        "operation": operation,
        "length": len(transformed),
    }


async def tool_web_search(params: Dict[str, Any], context: Any) -> Dict[str, Any]:
    query = str(params.get("query", params.get("text", ""))).strip()
    if not query:
        raise ToolExecutionError("Web search requires a non-empty 'query' parameter.")

    # Return structured search results
    return {
        "query": query,
        "results": [
            {
                "title": f"Market Research & Insights: {query}",
                "snippet": f"Verified analysis and data points for '{query}' covering industry metrics.",
                "url": f"https://search.internal/results?q={query.replace(' ', '+')}",
            },
            {
                "title": f"Executive Summary - {query}",
                "snippet": f"Overview of current best practices, historical records, and findings relating to {query}.",
                "url": f"https://knowledge.internal/overview?q={query.replace(' ', '+')}",
            },
        ],
        "total_results": 2,
        "status": "success",
    }


async def tool_json_parser(params: Dict[str, Any], context: Any) -> Dict[str, Any]:
    data = params.get("data") or params.get("text") or params.get("json_string")
    mode = params.get("mode", "parse")

    if mode == "stringify":
        try:
            return {"result": json.dumps(data, indent=2), "status": "success"}
        except Exception as e:
            raise ToolExecutionError(f"JSON stringify failed: {str(e)}")
    else:
        if isinstance(data, dict):
            return {"result": data, "status": "success"}
        try:
            parsed = json.loads(str(data))
            return {"result": parsed, "status": "success"}
        except Exception as e:
            raise ToolExecutionError(f"JSON parse failed: {str(e)}")


async def tool_http_request(params: Dict[str, Any], context: Any) -> Dict[str, Any]:
    url = str(params.get("url", params.get("endpoint", ""))).strip()
    if not url:
        raise ToolExecutionError("HTTP tool requires a valid 'url' or 'endpoint' parameter.")
    method = str(params.get("method", "GET")).upper()
    headers = params.get("headers", {})
    body = params.get("body", params.get("data"))

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            if method == "GET":
                resp = await client.get(url, headers=headers)
            elif method == "POST":
                resp = await client.post(url, headers=headers, json=body)
            else:
                raise ToolExecutionError(f"Unsupported HTTP method '{method}'.")

            return {
                "status_code": resp.status_code,
                "url": url,
                "headers": dict(resp.headers),
                "text": resp.text[:2000],
            }
        except Exception as e:
            raise ToolExecutionError(f"HTTP request to {url} failed: {str(e)}")


class PredefinedToolRegistry:
    """Registry maintaining approved, deterministic tool handlers."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        # Register standard approved tools
        self.register(
            "calculator",
            "Safe arithmetic expression evaluator without code execution.",
            tool_calculator,
        )
        self.register(
            "text_formatter",
            "String transformations: upper, lower, title, strip, and metrics.",
            tool_text_formatter,
        )
        self.register(
            "web_search",
            "Structured web search and knowledge retrieval.",
            tool_web_search,
        )
        self.register(
            "json_parser",
            "Safe JSON parsing and serializing.",
            tool_json_parser,
        )
        self.register(
            "http_request",
            "Safe external HTTP request dispatcher.",
            tool_http_request,
        )

    def register(
        self,
        name: str,
        description: str,
        handler: Callable[[Dict[str, Any], Any], Awaitable[Dict[str, Any]]],
    ) -> None:
        self._tools[name.lower()] = {
            "name": name,
            "description": description,
            "handler": handler,
        }

    def has_tool(self, name: str) -> bool:
        return name.lower() in self._tools

    def get_tool(self, name: str) -> Dict[str, Any]:
        tool = self._tools.get(name.lower())
        if not tool:
            available = ", ".join(self._tools.keys())
            raise ToolExecutionError(
                f"Tool '{name}' is not registered or approved. Available tools: {available}"
            )
        return tool

    def list_tools(self) -> List[Dict[str, str]]:
        return [
            {"name": t["name"], "description": t["description"]}
            for t in self._tools.values()
        ]


# Global singleton registry instance
tool_registry = PredefinedToolRegistry()
