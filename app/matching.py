from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

STANDARD_GOVERNMENT_WARNING = (
    "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK "
    "ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. "
    "(2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR "
    "OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."
)

GOVERNMENT_WARNING_REGEX = re.compile(
    r"(GOVERNMENT WARNING:\s*\(1\).*?\(2\).*?HEALTH PROBLEMS\.)",
    re.IGNORECASE | re.DOTALL,
)


def normalize_spaces(value: str) -> str:
    return " ".join(value.split())


def normalize_text(value: str) -> str:
    value = value.strip()
    value = value.replace("’", "'").replace("`", "'")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_spaces(left), normalize_spaces(right)).ratio()


def extract_alcohol_content(text: str) -> str:
    patterns = [
        re.compile(r"(\d{1,2}(?:\.\d+)?\s*%\s*(?:ALC\.?\s*/\s*VOL|ABV|ALC/VOL))", re.IGNORECASE),
        re.compile(r"(\d{1,3}(?:\.\d+)?\s*PROOF)", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return normalize_spaces(match.group(1).upper().replace("ALC / VOL", "ALC/VOL"))
    return ""


def normalize_alcohol_content(value: str) -> str:
    value = value.upper().replace("ALC./VOL", "ALC/VOL").replace("ALC / VOL", "ALC/VOL")
    value = normalize_spaces(value)
    value = value.replace(" ", "")
    value = value.replace("ALCOHOLBYVOLUME", "ALC/VOL")
    return value


def extract_field(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if not match:
        return ""
    return normalize_spaces(match.group(1))


def extract_fields(ocr_text: str) -> dict[str, str]:
    text = normalize_spaces(ocr_text)

    warning_match = GOVERNMENT_WARNING_REGEX.search(ocr_text)
    government_warning = normalize_spaces(warning_match.group(1)) if warning_match else ""

    brand_name = extract_field(ocr_text, r"^\s*(?:BRAND NAME|BRAND)\s*[:\-]\s*(.+?)\s*$")
    if not brand_name:
        lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
        for line in lines:
            if "GOVERNMENT WARNING" in line.upper() or len(line) < 3:
                continue
            if len(line.split()) <= 6:
                brand_name = line
                break

    return {
        "brand_name": brand_name,
        "class_type": extract_field(ocr_text, r"^\s*(?:CLASS\s*/\s*TYPE|CLASS|TYPE)\s*[:\-]\s*(.+?)\s*$"),
        "alcohol_content": extract_alcohol_content(text),
        "net_contents": extract_field(ocr_text, r"^\s*(?:NET\s*(?:CONTENTS|CONTENT)|CONTENTS)\s*[:\-]?\s*(\d+(?:\.\d+)?\s*(?:ML|CL|L|LITER|LITERS|FL\.?\s*OZ|OZ))\s*$"),
        "government_warning": government_warning,
    }


def _build_match(label: str, application: str, is_match: bool, confidence: float | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "label": label,
        "application": application,
        "match": is_match,
    }
    if confidence is not None:
        payload["confidence"] = round(confidence, 3)
    return payload


def verify_extracted_fields(
    label_fields: dict[str, str],
    application_fields: dict[str, str],
    processing_time_ms: int,
) -> dict[str, Any]:
    issues: list[str] = []

    label_brand = label_fields.get("brand_name", "")
    app_brand = application_fields.get("brand_name", "")
    brand_match = normalize_text(label_brand) == normalize_text(app_brand) and bool(app_brand)

    label_class = label_fields.get("class_type", "")
    app_class = application_fields.get("class_type", "")
    class_match = normalize_text(label_class) == normalize_text(app_class) if app_class else True

    label_alcohol = label_fields.get("alcohol_content", "")
    app_alcohol = application_fields.get("alcohol_content", "")
    alcohol_confidence = similarity(normalize_alcohol_content(label_alcohol), normalize_alcohol_content(app_alcohol))
    alcohol_match = alcohol_confidence >= 0.9 and bool(app_alcohol)

    label_net = label_fields.get("net_contents", "")
    app_net = application_fields.get("net_contents", "")
    net_match = normalize_text(label_net) == normalize_text(app_net) if app_net else True

    label_warning = normalize_spaces(label_fields.get("government_warning", ""))
    app_warning = normalize_spaces(application_fields.get("government_warning", STANDARD_GOVERNMENT_WARNING))
    warning_prefix_ok = "GOVERNMENT WARNING:" in label_fields.get("government_warning", "")
    warning_match = normalize_spaces(label_warning) == app_warning and warning_prefix_ok

    if not brand_match:
        issues.append("Brand name does not match application data.")
    if not class_match:
        issues.append("Class/type does not match application data.")
    if not alcohol_match:
        issues.append("Alcohol content does not match application data.")
    if not net_match:
        issues.append("Net contents does not match application data.")
    if not warning_match:
        issues.append("Government warning missing/altered or not exact all-caps format.")

    return {
        "brand_name": _build_match(label_brand, app_brand, brand_match),
        "class_type": _build_match(label_class, app_class, class_match),
        "alcohol_content": _build_match(label_alcohol, app_alcohol, alcohol_match, confidence=alcohol_confidence),
        "net_contents": _build_match(label_net, app_net, net_match),
        "government_warning": _build_match(label_warning, app_warning, warning_match),
        "issues": issues,
        "processing_time_ms": processing_time_ms,
    }
