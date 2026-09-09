from __future__ import annotations

import csv
import io
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from fastapi import Response

from .errors import ErclaveError


REPORT_MAX_ROWS = 50_000
_UNSAFE_SPREADSHEET_PREFIX = re.compile(r"^[\s]*[=+\-@]")


@dataclass(frozen=True)
class ReportColumn:
    key: str
    es: str
    en: str


@dataclass(frozen=True)
class ReportResult:
    filename: str
    columns: Sequence[ReportColumn]
    rows: Iterable[Mapping[str, object]]


def validate_date_range(date_from: date | None, date_to: date | None) -> None:
    if date_from and date_to and date_from > date_to:
        raise ErclaveError(
            "report_date_range_invalid",
            "The report start date cannot be after the end date.",
            status_code=422,
        )


def _cell(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, datetime):
        rendered = value.isoformat(timespec="seconds")
    elif isinstance(value, date):
        rendered = value.isoformat()
    elif isinstance(value, Decimal):
        return value
    elif isinstance(value, bool):
        return "true" if value else "false"
    else:
        rendered = str(value)
    return f"'{rendered}" if _UNSAFE_SPREADSHEET_PREFIX.match(rendered) else rendered


def csv_report_response(result: ReportResult, lang: str = "es") -> Response:
    rows = list(result.rows)
    if len(rows) > REPORT_MAX_ROWS:
        raise ErclaveError(
            "report_row_limit_exceeded",
            f"The report exceeds the limit of {REPORT_MAX_ROWS} rows. Narrow the filters and try again.",
            status_code=422,
            details={"max_rows": REPORT_MAX_ROWS},
        )
    if not rows:
        return Response(status_code=204)

    output = io.StringIO(newline="")
    writer = csv.writer(output, dialect="excel", lineterminator="\r\n")
    writer.writerow([column.en if lang == "en" else column.es for column in result.columns])
    for row in rows:
        writer.writerow([_cell(row.get(column.key)) for column in result.columns])

    payload = "\ufeff" + output.getvalue()
    safe_filename = re.sub(r"[^A-Za-z0-9._-]", "-", result.filename).strip("-") or "report.csv"
    if not safe_filename.lower().endswith(".csv"):
        safe_filename += ".csv"
    return Response(
        content=payload.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
