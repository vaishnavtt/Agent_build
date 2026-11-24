"""Opt-in live Gemini smoke test using synthetic diagnostic context."""

from argparse import ArgumentParser

from app.services.repair.diagnosis import ExternalDiagnosticFact
from app.services.repair.gemini_diagnosis import (
    ComplexFailureCode,
    GeminiDiagnosisProvider,
    GeminiDiagnosticContext,
    GeminiHypothesis,
)


def main() -> int:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Allow one external Gemini request.")
    if not parser.parse_args().live:
        print("Live request disabled. Use --live only after approval.")
        return 0
    provider = GeminiDiagnosisProvider.from_backend_settings()
    reply = provider.generate(GeminiDiagnosticContext(
        node_type="Output", error_code=ComplexFailureCode.UNEXPECTED_OUTPUT_SHAPE,
        facts=(ExternalDiagnosticFact.OUTPUT_SHAPE_MISMATCH,),
    ))
    if reply.issue or not reply.text:
        print(f"Gemini smoke test unavailable: {reply.issue or 'empty_response'}.")
        return 1
    try:
        GeminiHypothesis.model_validate_json(reply.text, strict=True)
    except ValueError:
        print("Gemini replied with an invalid advisory schema.")
        return 1
    print(f"Gemini returned a structured advisory reply. Requests: {reply.usage.calls}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
