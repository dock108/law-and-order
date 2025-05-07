"""PI Workflow API router defining stub endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter()


@router.get("/cases")
async def list_cases():
    """Stub route for listing cases."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@router.get("/cases/{caseId}")
async def get_case_detail(caseId: str):
    """Stub route for case detail."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@router.post("/cases/{caseId}/advance")
async def advance_case_stage(caseId: str):
    """Stub route for advancing case stage."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@router.get("/tasks")
async def list_tasks():
    """Stub route for listing tasks."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@router.post("/tasks")
async def create_task():
    """Stub route for creating a task."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@router.patch("/tasks/{taskId}")
async def update_task(taskId: str):
    """Stub route for updating a task."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@router.delete("/tasks/{taskId}")
async def delete_task(taskId: str):
    """Stub route for deleting a task."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@router.post("/tasks/bulk-complete")
async def mark_many_tasks_done():
    """Stub route for marking many tasks as done."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@router.get("/documents")
async def list_documents():
    """Stub route for listing documents."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@router.post("/documents/{docId}/send")
async def send_document(docId: str):
    """Stub route for sending a document."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@router.get("/events/stream")
async def get_event_stream():
    """Stub route for the SSE event stream."""
    return PlainTextResponse("", status_code=501)
