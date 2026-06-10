# USTreasuryAssessmentApp

AI-powered alcohol label verification prototype for TTB-style label review workflows.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Cyberboost/USTreasuryAssessmentApp)
[![CI](https://github.com/Cyberboost/USTreasuryAssessmentApp/actions/workflows/ci.yml/badge.svg)](https://github.com/Cyberboost/USTreasuryAssessmentApp/actions/workflows/ci.yml)

## Hiring Manager Review

This is a deployable FastAPI work sample that turns a regulatory review workflow into a working prototype: upload alcohol label images, extract text with OCR, compare the label against submitted application fields, and return structured pass/fail results.

What it demonstrates:

- Product thinking for a compliance-adjacent government workflow.
- Python/FastAPI API design with a browser-based review UI.
- OCR preprocessing with OpenCV, Tesseract, field extraction, normalization, and confidence scoring.
- Single-label and batch processing paths, including progress polling and JSON result download.
- Containerized deployment through Docker, Render Blueprint config, and Azure-ready container packaging.
- Automated validation through GitHub Actions, unit tests, and Docker image builds.

Fast review path:

1. Click **Deploy to Render** to create a temporary public review URL.
2. Open the generated Render URL and upload one of the generated sample label images.
3. Review `/health`, `/api/verify`, and `/api/batch/start` for the API surface.
4. Check the CI badge for the current test and Docker build status.

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
- Containerization: Dockerfile for Render, Azure App Service, and Azure Container Apps
- CI/CD: GitHub Actions for `pytest` and Docker build validation

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
pytest
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

## Deploy to Render.com

Use the Deploy to Render button at the top of this README, or open this link directly:

`https://render.com/deploy?repo=https://github.com/Cyberboost/USTreasuryAssessmentApp`

Render will read `render.yaml`, build the Docker image, and create a public `https://<your-app>.onrender.com` URL.

1. Sign up at [render.com](https://render.com) (free, no credit card required).
2. Click the deploy button or direct link above.
3. Review the service settings and click **Apply**.
4. Wait for the first Docker build to finish. Your public URL will appear in the Render dashboard.

> **Note:** Free instances spin down after 15 minutes of inactivity. The first request after a cold start takes ~30 seconds.

## Azure deployment

This repository includes a `Dockerfile` suitable for:

- Azure App Service (custom container)
- Azure Container Apps

Build and run container locally:

```bash
docker build -t ttb-label-prototype .
docker run -p 8000:8000 ttb-label-prototype
```
