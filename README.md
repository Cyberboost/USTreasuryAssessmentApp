# USTreasuryAssessmentApp Prototype

AI-powered alcohol label verification prototype for TTB label reviewers.

## What this prototype does

- Upload one label image and compare OCR output against application JSON fields.
- Upload batches of up to 300 label images asynchronously.
- Track batch progress and download structured JSON results.
- Uses temporary in-memory processing only (no persistent label data store).

## Tech stack

- Backend + UI host: FastAPI
- OCR: Tesseract (`pytesseract`) + OpenCV preprocessing
- Matching: Regex + normalization + similarity scoring
- Frontend: Accessible single-page UI served from FastAPI
- Containerization: Dockerfile for Azure App Service / Azure Container Apps

## API result format

```json
{
  "brand_name": { "label": "", "application": "", "match": true },
  "alcohol_content": { "label": "", "application": "", "match": false, "confidence": 0.92 },
  "government_warning": { "label": "", "application": "", "match": true },
  "issues": [],
  "processing_time_ms": 0
}
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Build from external `D:` drive (Windows)

If your local repository is on an external `D:` drive, run all commands from that clone path, for example:

```powershell
cd D:\USTreasuryAssessmentApp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Install Tesseract locally if missing:

- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`

Run:

```bash
uvicorn app.main:app --reload
```

Open: `http://127.0.0.1:8000`

## Tests

```bash
pytest tests/test_matching.py
```

## Generate synthetic test labels

```bash
python scripts/generate_test_labels.py --output sample_labels
```

Generated samples include:

- valid baseline label
- altered warning label (expected fail)
- case/apostrophe variant brand label (expected match)

## Batch flow

1. Upload 1–300 images
2. Start batch (`/api/batch/start`)
3. Poll progress (`/api/batch/{job_id}`)
4. Download results (`/api/batch/{job_id}/results`)

## Security and compliance assumptions

- Prototype scope only (no direct COLA integration).
- No persistent PII storage; data kept in process memory during runtime.
- Intended for FedRAMP-minded deployment hardening in Azure environments.

## Tradeoffs

- Government warning bold-style validation is approximated through OCR text checks (exact all-caps phrase match).
- OCR quality depends on image clarity and local Tesseract model quality.
- In-memory batch state resets when the app process restarts.

## Azure deployment

This repository includes a `Dockerfile` suitable for:

- Azure App Service (custom container)
- Azure Container Apps

Build and run container locally:

```bash
docker build -t ttb-label-prototype .
docker run -p 8000:8000 ttb-label-prototype
```
