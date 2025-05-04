"""Tasks for generating retainer agreements and handling e-signatures."""

from pi_auto_api.tasks import app


@app.task(name="generate_retainer")
def generate_retainer(client_id: int):
    """Generate retainer agreement for a client.

    Fetch client & incident → call Docassemble `/api/v1/generate/retainer`
    → send DocuSign envelope (placeholder).
    """
    return {"client_id": client_id, "status": "queued"}
