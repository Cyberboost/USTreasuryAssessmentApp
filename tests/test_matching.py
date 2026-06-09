from app.matching import STANDARD_GOVERNMENT_WARNING, verify_extracted_fields


def test_brand_name_matches_case_and_apostrophe_variation() -> None:
    label_fields = {
        "brand_name": "STONE'S THROW",
        "class_type": "WHISKEY",
        "alcohol_content": "45% ALC/VOL",
        "net_contents": "750 ML",
        "government_warning": STANDARD_GOVERNMENT_WARNING,
    }
    app_fields = {
        "brand_name": "Stone’s Throw",
        "class_type": "WHISKEY",
        "alcohol_content": "45% ALC/VOL",
        "net_contents": "750 ML",
        "government_warning": STANDARD_GOVERNMENT_WARNING,
    }

    result = verify_extracted_fields(label_fields, app_fields, processing_time_ms=100)
    assert result["brand_name"]["match"] is True


def test_abv_formats_match() -> None:
    label_fields = {
        "brand_name": "STONE'S THROW",
        "class_type": "WHISKEY",
        "alcohol_content": "45% Alc./Vol.",
        "net_contents": "750 ML",
        "government_warning": STANDARD_GOVERNMENT_WARNING,
    }
    app_fields = {
        "brand_name": "STONE'S THROW",
        "class_type": "WHISKEY",
        "alcohol_content": "45% ALC/VOL",
        "net_contents": "750 ML",
        "government_warning": STANDARD_GOVERNMENT_WARNING,
    }

    result = verify_extracted_fields(label_fields, app_fields, processing_time_ms=100)
    assert result["alcohol_content"]["match"] is True


def test_missing_or_altered_government_warning_fails() -> None:
    label_fields = {
        "brand_name": "STONE'S THROW",
        "class_type": "WHISKEY",
        "alcohol_content": "45% ALC/VOL",
        "net_contents": "750 ML",
        "government_warning": "Government Warning: text changed",
    }
    app_fields = {
        "brand_name": "STONE'S THROW",
        "class_type": "WHISKEY",
        "alcohol_content": "45% ALC/VOL",
        "net_contents": "750 ML",
        "government_warning": STANDARD_GOVERNMENT_WARNING,
    }

    result = verify_extracted_fields(label_fields, app_fields, processing_time_ms=100)
    assert result["government_warning"]["match"] is False
    assert any("Government warning" in issue for issue in result["issues"])
