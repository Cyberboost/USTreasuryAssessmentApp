from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.service import verify_image_against_application

app = FastAPI(title="TTB Alcohol Label Verification Prototype")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


class BatchJob(dict):
    pass


BATCH_JOBS: dict[str, BatchJob] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.post("/api/verify")
async def verify_single(
    image: UploadFile = File(...),
    application_json: str = Form(...),
) -> dict[str, Any]:
    try:
        application_fields = json.loads(application_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid application JSON: {exc}") from exc

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    try:
        return verify_image_against_application(image_bytes, application_fields)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Verification failed: {exc}") from exc


async def _run_batch(job_id: str, files_payload: list[tuple[str, bytes]], application_fields: dict[str, str]) -> None:
    job = BATCH_JOBS[job_id]
    for index, (filename, image_bytes) in enumerate(files_payload, start=1):
        try:
            result = verify_image_against_application(image_bytes, application_fields)
        except Exception as exc:  # noqa: BLE001
            result = {
                "brand_name": {"label": "", "application": application_fields.get("brand_name", ""), "match": False},
                "alcohol_content": {
                    "label": "",
                    "application": application_fields.get("alcohol_content", ""),
                    "match": False,
                    "confidence": 0.0,
                },
                "government_warning": {
                    "label": "",
                    "application": application_fields.get("government_warning", ""),
                    "match": False,
                },
                "issues": [f"Processing failed: {exc}"],
                "processing_time_ms": 0,
            }
        result["filename"] = filename
        job["results"].append(result)
        job["processed"] = index

    job["status"] = "completed"
    job["completed_at"] = datetime.now(timezone.utc).isoformat()


@app.post("/api/batch/start")
async def start_batch(
    images: list[UploadFile] = File(...),
    application_json: str = Form(...),
) -> dict[str, Any]:
    if not images:
        raise HTTPException(status_code=400, detail="Please upload at least one image.")
    if len(images) > 300:
        raise HTTPException(status_code=400, detail="Batch limit is 300 images per run.")

    try:
        application_fields = json.loads(application_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid application JSON: {exc}") from exc

    files_payload: list[tuple[str, bytes]] = []
    for upload in images:
        payload = await upload.read()
        if payload:
            files_payload.append((upload.filename or "unnamed", payload))

    if not files_payload:
        raise HTTPException(status_code=400, detail="No readable files were uploaded.")

    job_id = str(uuid.uuid4())
    BATCH_JOBS[job_id] = BatchJob(
        {
            "job_id": job_id,
            "status": "processing",
            "total": len(files_payload),
            "processed": 0,
            "results": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    asyncio.create_task(_run_batch(job_id, files_payload, application_fields))
    return {"job_id": job_id, "status": "processing", "total": len(files_payload)}


@app.get("/api/batch/{job_id}")
def get_batch_status(job_id: str) -> dict[str, Any]:
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Batch job not found.")
    job = BATCH_JOBS[job_id]
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "processed": job["processed"],
        "total": job["total"],
    }


@app.get("/api/batch/{job_id}/results")
def get_batch_results(job_id: str) -> JSONResponse:
    if job_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Batch job not found.")
    job = BATCH_JOBS[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail="Batch is still processing.")

    return JSONResponse(
        content={"job_id": job_id, "results": job["results"]},
        headers={"Content-Disposition": f'attachment; filename="{job_id}-results.json"'},
    )
