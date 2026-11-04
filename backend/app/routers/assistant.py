"""Router for Grounded Policy & Early-Warning Assistant."""
from fastapi import APIRouter, Depends, status
from backend.app.middleware.auth_middleware import AuthenticatedUser, get_current_user
from backend.app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from backend.app.services.assistant_service import query_assistant

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

@router.post("/query", response_model=AssistantQueryResponse, status_code=status.HTTP_200_OK)
def handle_assistant_query(
    payload: AssistantQueryRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Answers staff queries on statutory school policies, warning rules, and SOPs.

    Strict guardrails: rejects predictive requests (dropout/emotional predictions).
    """
    result = query_assistant(payload.query, payload.language or "en")
    return AssistantQueryResponse(**result)
