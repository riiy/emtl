"""Check tox isolation before pytest can clear the environment."""

import os

assert not os.environ.get("EM_USERNAME")
assert not os.environ.get("EM_PASSWORD")
assert not any(key.startswith("EM_") and key not in {"EM_USERNAME", "EM_PASSWORD"} for key in os.environ)
assert all(
    key not in os.environ for key in ("P0_FAKE_ACCOUNT_CREDENTIAL", "P1_FAKE_ACCOUNT_CREDENTIAL", "NETRC", "SSH_AUTH_SOCK", "SSH_AGENT_PID")
)
print("account environment isolated")
