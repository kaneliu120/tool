def greet(name: str) -> str:
    """Return a greeting for name."""
    return f"hello {name}"


class Cache:
    def warm(self) -> None:
        """Load cache before traffic."""
        return None
