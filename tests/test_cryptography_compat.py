"""Regression checks for the only cryptography APIs used by emtl.

Uses synthetic text and a temporary in-memory RSA key, no broker/network
calls or persisted private keys. The production key stays unchanged.
"""

import base64
from importlib.metadata import version

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa

from emtl import utils


def test_approved_cryptography_runtime_version():
    assert version("cryptography") == "50.0.2"


def test_embedded_public_key_still_encrypts_with_legacy_pkcs1v15():
    """Keep the broker's existing wire format, do not switch to OAEP."""
    key = serialization.load_pem_public_key(utils.rsa_public_key.encode("utf-8"))
    assert isinstance(key, rsa.RSAPublicKey)
    assert key.key_size == 1024

    encoded = utils.emt_trade_encrypt("P4_FAKE_PASSWORD")
    encrypted = base64.b64decode(encoded, validate=True)
    assert len(encrypted) == key.key_size // 8


def test_encrypt_round_trip_with_ephemeral_synthetic_key(monkeypatch):
    """Exercise real PEM loading, RSA encryption, base64 and UTF-8 encoding."""
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    monkeypatch.setattr(utils, "rsa_public_key", public_pem.decode("ascii"))

    plaintext = "P4_FAKE_测试_PASSWORD"
    ciphertext_b64 = utils.emt_trade_encrypt(plaintext)
    ciphertext = base64.b64decode(ciphertext_b64, validate=True)

    assert len(ciphertext) == private.key_size // 8
    assert private.decrypt(ciphertext, padding.PKCS1v15()) == plaintext.encode("utf-8")
