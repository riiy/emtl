"""Test-only network and OCR isolation, installed before importing emtl."""

import socket
import sys
import types

import requests

_originals = []
_original_ocr = None
_installed = False


def blocked(*args, **kwargs):
    raise RuntimeError("network disabled in tests")


class FakeOcr:
    def __init__(self, *args, **kwargs):
        pass

    def classification(self, *args, **kwargs):
        raise RuntimeError("unconfigured test OCR")


def install():
    """Install process-wide guards; safe to invoke more than once."""
    global _installed, _original_ocr
    if _installed:
        return
    targets = [
        (requests.sessions.Session, "request"),
        (requests.sessions.Session, "send"),
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (socket, "gethostbyname"),
        (socket, "gethostbyname_ex"),
        (socket, "gethostbyaddr"),
        (socket, "getnameinfo"),
    ]
    targets.extend((socket.socket, name) for name in ("send", "sendall", "sendto", "sendmsg") if hasattr(socket.socket, name))
    for owner, name in targets:
        _originals.append((owner, name, getattr(owner, name)))
        setattr(owner, name, blocked)
    _original_ocr = sys.modules.get("ddddocr")
    module = types.ModuleType("ddddocr")
    module.DdddOcr = FakeOcr
    sys.modules["ddddocr"] = module
    _installed = True


def restore():
    global _installed
    if not _installed:
        return
    for owner, name, original in reversed(_originals):
        setattr(owner, name, original)
    _originals.clear()
    if _original_ocr is None:
        sys.modules.pop("ddddocr", None)
    else:
        sys.modules["ddddocr"] = _original_ocr
    _installed = False
