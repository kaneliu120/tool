#!/usr/bin/env python3
"""Regenerate Argonaut HTML fixtures with correctly nested JSON."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def wrap(data_obj: dict) -> str:
    inner = json.dumps(data_obj, separators=(",", ":"))
    cache = {"q1": {"data": inner}}
    root = {
        "resi-property_listing-experience-web": {
            "urqlClientCache": json.dumps(cache, separators=(",", ":"))
        }
    }
    return "window.ArgonautExchange=" + json.dumps(root, separators=(",", ":")) + ";"


def write(name: str, title: str, data: dict, pad_n: int) -> None:
    html = f"""<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
<script>
{wrap(data)}
</script>
<div id="pad">{"Z" * pad_n}</div>
</body>
</html>
"""
    path = FIXTURES / name
    path.write_text(html, encoding="utf-8")
    print(f"{name}: {path.stat().st_size} bytes")


def main() -> None:
    write(
        "argonaut_sale_srp.html",
        "Buy",
        {
            "buySearch": {
                "results": {
                    "items": [
                        {
                            "listing": {
                                "id": "149100001",
                                "listingType": "sale",
                                "url": "https://www.realestate.com.au/property-house-vic-richmond-149100001",
                                "address": {
                                    "display": {
                                        "shortAddress": "1 Test St, Richmond",
                                        "fullAddress": "1 Test St, Richmond, Vic 3121",
                                    }
                                },
                                "price": {"display": "$1,200,000"},
                                "status": "published",
                            }
                        },
                        {
                            "listing": {
                                "id": "149100002",
                                "listingType": "sale",
                                "url": "https://www.realestate.com.au/property-apartment-vic-southbank-149100002",
                                "address": {
                                    "display": {
                                        "shortAddress": "2 River Rd, Southbank",
                                        "fullAddress": "2 River Rd, Southbank, Vic 3006",
                                    }
                                },
                                "price": {"display": "$850,000"},
                                "status": "published",
                            }
                        },
                    ]
                }
            }
        },
        110_000,
    )
    write(
        "argonaut_rent_srp.html",
        "Rent",
        {
            "rentSearch": {
                "results": {
                    "items": [
                        {
                            "listing": {
                                "id": "149200001",
                                "listingType": "rent",
                                "url": "https://www.realestate.com.au/property-apartment-vic-melbourne-149200001",
                                "address": {
                                    "display": {
                                        "shortAddress": "10 Collins St, Melbourne",
                                        "fullAddress": "10 Collins St, Melbourne, Vic 3000",
                                    }
                                },
                                "price": {"display": "$650 per week"},
                                "status": "published",
                            }
                        },
                        {
                            "listing": {
                                "id": "149200002",
                                "listingType": "rent",
                                "url": "https://www.realestate.com.au/property-house-vic-carlton-149200002",
                                "address": {
                                    "display": {
                                        "shortAddress": "3 Park Ave, Carlton",
                                        "fullAddress": "3 Park Ave, Carlton, Vic 3053",
                                    }
                                },
                                "price": {"display": "$780 per week"},
                                "status": "published",
                            }
                        },
                    ]
                }
            }
        },
        110_000,
    )
    write(
        "argonaut_sale_ldp.html",
        "Sale Detail",
        {
            "details": {
                "listing": {
                    "id": "149000000",
                    "listingType": "sale",
                    "url": "https://www.realestate.com.au/property-house-vic-richmond-149000000",
                    "address": {
                        "display": {
                            "shortAddress": "22 Sale Detail St, Richmond",
                            "fullAddress": "22 Sale Detail St, Richmond, Vic 3121",
                        }
                    },
                    "price": {"display": "Offers over $1,450,000"},
                    "status": "published",
                    "channel": "sale",
                }
            }
        },
        35_000,
    )
    write(
        "argonaut_rent_ldp.html",
        "Rent Detail",
        {
            "details": {
                "listing": {
                    "id": "149000001",
                    "listingType": "rent",
                    "url": "https://www.realestate.com.au/property-apartment-vic-melbourne-149000001",
                    "address": {
                        "display": {
                            "shortAddress": "88 Rent Detail Rd, Melbourne",
                            "fullAddress": "88 Rent Detail Rd, Melbourne, Vic 3000",
                        }
                    },
                    "price": {"display": "$720 per week"},
                    "status": "published",
                    "channel": "rent",
                }
            }
        },
        35_000,
    )


if __name__ == "__main__":
    main()
