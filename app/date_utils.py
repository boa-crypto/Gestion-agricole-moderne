"""Normalisation des dates renvoyées par la base.

Avec SQLite, les colonnes `Date` / `DateTime` peuvent revenir sous forme de
chaînes (« 2026-08-17 », « 2026-08-17 21:01:31.316258+00:00 »). Toute
soustraction ou comparaison directe avec `datetime.date` lève alors un
`TypeError`. Ces utilitaires convertissent silencieusement n'importe quelle
valeur en `datetime.date` / `datetime.datetime` (ou `None`).
"""

from __future__ import annotations

import datetime

__all__ = ["as_date", "as_datetime", "iso_or_empty"]


def as_datetime(value: object) -> datetime.datetime | None:
    """Convertit une valeur base de données en `datetime` naïf ou aware."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime(value.year, value.month, value.day)
    raw = str(value).strip()
    if not raw:
        return None
    candidate = raw.replace("Z", "+00:00").replace("T", " ")
    try:
        return datetime.datetime.fromisoformat(candidate)
    except ValueError:
        pass
    for pattern in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ):
        try:
            return datetime.datetime.strptime(candidate[:26], pattern)
        except ValueError:
            continue
    return None


def as_date(value: object) -> datetime.date | None:
    """Convertit une valeur base de données en `datetime.date` ou `None`."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    stamp = as_datetime(value)
    return stamp.date() if stamp is not None else None


def iso_or_empty(value: object) -> str:
    """Renvoie la date au format ISO, ou une chaîne vide si absente."""
    day = as_date(value)
    return "" if day is None else day.isoformat()
