import base64
import logging
import math

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa

rsa_public_key = """
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDHdsyxT66pDG4p73yope7jxA92
c0AT4qIJ/xtbBcHkFPK77upnsfDTJiVEuQDH+MiMeb+XhCLNKZGp0yaUU6GlxZdp
+nLW8b7Kmijr3iepaDhcbVTsYBWchaWUXauj9Lrhz58/6AE/NF0aMolxIGpsi+ST
2hSHPu3GSXMdhPCkWQIDAQAB
-----END PUBLIC KEY-----
"""


def get_logger(name):
    """Logger."""
    formater = "%(asctime)s %(name)-20s %(funcName)s %(lineno)d: %(levelname)-8s: %(message)s"
    logging.basicConfig(format=formater, force=True, level=logging.INFO)
    logger = logging.getLogger(name)
    return logger


def emt_trade_encrypt(content: str) -> str:
    _pub_key: rsa.RSAPublicKey = serialization.load_pem_public_key(rsa_public_key.encode("utf-8"))  # type:ignore
    encrypt_text = _pub_key.encrypt(content.encode(), padding.PKCS1v15())
    return base64.b64encode(encrypt_text).decode("utf-8")


def double_equal(a, b) -> bool:
    return math.fabs(a - b) < 1e-6


def get_float(data: dict, key: str) -> float:
    if v := data[key].strip():
        return float(v)
    return 0.0


def get_int(data: dict, key: str) -> int:
    if v := data[key].strip():
        return int(v)
    return 0
