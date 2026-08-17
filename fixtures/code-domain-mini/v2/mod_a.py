def greet_user(name: str) -> str:
    """Return a greeting for name (renamed in v2)."""
    return f"hello {name}"


class Cache:
    def warm(self) -> None:
        """Load cache before traffic."""
        return None
