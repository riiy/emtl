"""OCR v1 offline contract checks; no broker requests or private CAPTCHA fixtures."""

import base64
import hashlib
import io
import re
import sys
from importlib import resources
from unittest.mock import Mock

import pytest
from PIL import Image

from emtl import _protocol
from emtl._ocr import make_ocr
from emtl._ocr_lightweight import TinyCaptchaOCR

MODEL_SHA256 = "27dc2423ad452a3a723ba0d3ccc8d57a81bfda0238497baf94ce22926585cf4a"


def test_packaged_weights_are_exactly_frozen_v1():
    model = resources.files("emtl").joinpath("models", "tiny_captcha_model.b64")
    assert hashlib.sha256(base64.b64decode(model.read_bytes())).hexdigest() == MODEL_SHA256


def test_default_engine_decodes_an_image_offline(monkeypatch):
    monkeypatch.delenv("EMTL_OCR_ENGINE", raising=False)
    engine = make_ocr()
    assert isinstance(engine, TinyCaptchaOCR)
    image = Image.new("RGB", (101, 36), (255, 255, 255))
    stream = io.BytesIO()
    image.save(stream, format="JPEG")
    result = engine.classification(stream.getvalue())
    assert re.fullmatch(r"[0-9]{4}", result)
    assert isinstance(make_ocr(), TinyCaptchaOCR)
    assert make_ocr() is not engine


def test_unknown_engine_does_not_silently_fallback(monkeypatch):
    monkeypatch.setenv("EMTL_OCR_ENGINE", "incorrect")
    with pytest.raises(ValueError, match="unknown EMTL_OCR_ENGINE"):
        make_ocr()


def test_legacy_selector_explicit_and_py311_only(monkeypatch):
    monkeypatch.setenv("EMTL_OCR_ENGINE", "ddddocr")
    if sys.version_info[:2] != (3, 11):
        with pytest.raises(RuntimeError, match="Python 3.11 only"):
            make_ocr()
    else:
        # The offline bootstrap injects a test-only ddddocr module before import.
        engine = make_ocr()
        assert callable(engine.classification)


def test_captcha_preserves_leading_zero_and_never_casts_to_int():
    response = Mock(status_code=200, content=b"synthetic JPEG")
    recognizer = Mock(return_value="0072")
    seen = []

    def get_image(url, **kwargs):
        seen.append(url)
        return response

    nonce, code = _protocol.captcha(get_image, recognizer, lambda: Mock(random=lambda: 0.5), lambda _: None, Mock(), lambda: None)
    assert (nonce, code) == (0.5, "0072")
    assert _protocol.login_form(" test ", "password", 30, nonce, code, lambda x: x)["identifyCode"] == "0072"
    assert len(seen) == 1


@pytest.mark.parametrize("bad", [None, False, 0, "", "123", "12345", "12a4", "１２３４", " 1234"])
def test_invalid_ocr_retried_before_authentication(bad):
    values = iter([bad, "0019"])
    get_image = Mock(return_value=Mock(status_code=200, content=b"synthetic JPEG"))
    check = Mock()

    def random_factory():
        return Mock(random=lambda: 0.5)

    def recognize(_image):
        return next(values)

    log = Mock()

    def retry():
        return _protocol.captcha(get_image, recognize, random_factory, check, log, retry)

    assert retry() == (0.5, "0019")
    assert get_image.call_count == 2
    log.error.assert_called_once_with("captcha recognition failed")
