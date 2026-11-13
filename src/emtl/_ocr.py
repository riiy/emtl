"""Private CAPTCHA engine factory. Explicit selection never silently falls back."""

import os
import sys


def make_ocr():
    """Build an independent OCR engine using EMTL_OCR_ENGINE."""
    engine = os.getenv("EMTL_OCR_ENGINE", "lightweight").strip().lower()
    if engine == "lightweight":
        from ._ocr_lightweight import TinyCaptchaOCR

        return TinyCaptchaOCR()
    if engine == "ddddocr":
        if sys.version_info[:2] != (3, 11):
            raise RuntimeError("ddddocr legacy engine is supported on Python 3.11 only")
        try:
            from ddddocr import DdddOcr
        except ImportError as exc:
            raise RuntimeError("ddddocr is not installed; run: pip install 'emtl[ddddocr]'") from exc
        return DdddOcr(show_ad=False)
    raise ValueError("unknown EMTL_OCR_ENGINE; expected 'lightweight' or 'ddddocr'")
