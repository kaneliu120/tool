"""Thin Apify Actor errors."""


class ActorError(Exception):
    """Base Actor error."""


class AcquisitionError(ActorError):
    """Worker HTTP / auth / URL contract failed."""


class NoRowsCollectedError(ActorError):
    """Worker returned zero items."""


class FreeTierLimitError(ActorError):
    """Free Apify-plan usage limit reached (developer policy, not a platform bug)."""
