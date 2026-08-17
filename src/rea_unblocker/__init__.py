"""Self-hosted REA HTML acquisition gateway and Kasada observability."""

from rea_unblocker.classifier.html import classify_html
from rea_unblocker.providers.base import FetchResult, HtmlProvider

__all__ = ["FetchResult", "HtmlProvider", "classify_html"]
__version__ = "0.1.0"
