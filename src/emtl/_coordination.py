"""Process-local account scheduling; never hold the registry guard during I/O."""

from threading import Lock
from threading import RLock
from weakref import WeakValueDictionary

_registry_guard = Lock()
_accounts = WeakValueDictionary()
_owners = WeakValueDictionary()


class _AccountEntry:
    def __init__(self):
        self.lock = RLock()


def account_entry(username):
    with _registry_guard:
        entry = _accounts.get(username)
        if entry is None:
            entry = _AccountEntry()
            _accounts[username] = entry
        return entry


def claim(owner, *resources):
    """Reject shared mutable resources without touching another owner's state."""
    with _registry_guard:
        for resource in resources:
            current = _owners.get(id(resource))
            if current is not None and current is not owner:
                raise ValueError("client resource is already in use")
        for resource in resources:
            _owners[id(resource)] = owner
            owner._owned_resources.append(resource)


def release(owner):
    with _registry_guard:
        for resource in owner._owned_resources:
            key = id(resource)
            if _owners.get(key) is owner:
                del _owners[key]
        owner._owned_resources.clear()
