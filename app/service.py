from __future__ import annotations

import hashlib
import time
from typing import Any

import pytesseract

from app.image_processing import preprocess_image
from app.matching import extract_fields, verify_extracted_fields

OCR_CACHE: dict[str, str] = {}
OCR_CACHE_MAX = 512
TESSERACT_OCR_CONFIG = "--oem 1 --psm 6"


def _extract_text(image_bytes: bytes) -> str:
    image = preprocess_image(image_bytes)
    # --oem 1: LSTM engine. --psm 6: assume a single uniform block of text.
    return pytesseract.image_to_string(image, config=TESSERACT_OCR_CONFIG)


def verify_image_against_application(
    image_bytes: bytes,
    application_fields: dict[str, str],
) -> dict[str, Any]:
    start = time.perf_counter()
    image_key = hashlib.sha256(image_bytes).hexdigest()

    if image_key in OCR_CACHE:
        ocr_text = OCR_CACHE[image_key]
    else:
        ocr_text = _extract_text(image_bytes)
        if len(OCR_CACHE) >= OCR_CACHE_MAX:
            OCR_CACHE.pop(next(iter(OCR_CACHE)))
        OCR_CACHE[image_key] = ocr_text

    label_fields = extract_fields(ocr_text)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return verify_extracted_fields(label_fields, application_fields, elapsed_ms)
