"""FastAPI interface for legacy operational checks and scoped CTCAE v5 grading."""
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from ctcae_grading import grade_lab_event
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")
app = FastAPI(
    title="CTCAE Laboratory Grading and Demonstration API",
    description="Two reference CTCAE v5 laboratory grading terms; legacy operational checks are not CTCAE grades.",
    version="3.0.1",
)


def require_api_key(x_api_key: str | None = Header(default=None)):
    configured = os.getenv("API_KEY")
    if not configured:
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    if x_api_key is None or not secrets.compare_digest(x_api_key, configured):
        raise HTTPException(status_code=401, detail="Invalid API key")


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class LabGradeRequest(BaseModel):
    term: str = Field(min_length=1, max_length=100)
    value: float = Field(allow_inf_nan=False, ge=0)
    lln: float = Field(allow_inf_nan=False, gt=0)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "ctcae-adverse-event-grader", "version": "3.0.1"}


@app.get("/metrics")
def metrics(_=Depends(require_api_key)):
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
    }


@app.post("/api/ctcae/grade")
def api_ctcae_grade(payload: LabGradeRequest, _=Depends(require_api_key)):
    try:
        return grade_lab_event(payload.term, payload.value, payload.lln)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload, _=Depends(require_api_key)):
    try:
        return supervisor.process_task(payload).to_dict()
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail="Sensitive identifier detected; do not submit personal data") from exc


@app.post("/api/chat")
def api_chat(req: ChatRequest, _=Depends(require_api_key)):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail="Sensitive identifier detected; do not submit personal data") from exc


@app.get("/api/audit/logs")
def api_audit_logs(_=Depends(require_api_key)):
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
