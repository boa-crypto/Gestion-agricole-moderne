"""Export CSV simple des listes visibles (aucune dépendance externe)."""

from __future__ import annotations

import csv
import io

__all__ = ["to_csv"]


def to_csv(headers: list[str], rows: list[list[str]]) -> str:
    """Sérialise un tableau en CSV (séparateur `;`, compatible tableurs FR)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow([str(value) for value in row])
    return buffer.getvalue()
