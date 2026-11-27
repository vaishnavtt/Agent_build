"""Member 6 repair endpoints. The client provides identifiers only."""

from typing import Annotated

from fastapi import APIRouter, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.services.repair.history import HistoryResponse
from app.services.repair.integration import RepairBindings, RepairReadiness, RepairResponse, RepairService
from app.services.repair.recovery_contracts import RecoveryScope


class RepairRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request: Request) -> Response:
            try:
                response = await handler(request)
            except RequestValidationError:
                response = JSONResponse(
                    status_code=422,
                    content={"status": "invalid_request", "explanation": "Provide only the workflow, revision, and execution run identifiers."},
                )
            except Exception:
                response = JSONResponse(
                    status_code=500,
                    content={"status": "graph_error", "explanation": "The repair request could not be completed safely."},
                )
            response.headers["Cache-Control"] = "no-store"
            return response

        return safe_handler


router = APIRouter(route_class=RepairRoute)
_unconfigured = RepairService(RepairBindings())


def get_service(request: Request) -> RepairService:
    return getattr(request.app.state, "repair_service", _unconfigured)


@router.get("/readiness", response_model=RepairReadiness)
def readiness(request: Request) -> RepairReadiness:
    return get_service(request).readiness()


@router.get("/history", response_model=HistoryResponse)
def history(request: Request, workflow_id: str, workflow_revision_id: str, execution_run_id: str,
            offset: Annotated[int, Query(ge=0, le=1000000)] = 0,
            limit: Annotated[int, Query(ge=1, le=50)] = 20):
    try:
        scope = RecoveryScope(workflow_id=workflow_id, workflow_revision_id=workflow_revision_id,
                              execution_run_id=execution_run_id)
    except ValueError:
        return JSONResponse({"status": "invalid_request"}, status_code=422)
    code, body = get_service(request).history(scope, request, offset, limit)
    return body if code == 200 else JSONResponse(body, status_code=code)


@router.post("/diagnose", response_model=RepairResponse)
def diagnose(scope: RecoveryScope, request: Request, response: Response) -> RepairResponse:
    response.status_code, outcome = get_service(request).run(scope, request, "diagnose")
    return outcome


@router.post("/recover", response_model=RepairResponse)
def recover(scope: RecoveryScope, request: Request, response: Response) -> RepairResponse:
    response.status_code, outcome = get_service(request).run(scope, request, "recover")
    return outcome
