def emt(user, password):
    return user, password


def login(user: str, password: str) -> str:
    """Login."""
    valide_key = user + password
    return valide_key
