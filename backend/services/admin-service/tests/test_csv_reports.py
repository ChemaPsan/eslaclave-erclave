from datetime import date, datetime

import pytest

import erclave_common.csv_reports as csv_reports
from erclave_common.csv_reports import ReportColumn, ReportResult, csv_report_response, validate_date_range
from erclave_common.errors import ErclaveError


def test_csv_report_is_excel_compatible_bilingual_and_formula_safe():
    result = ReportResult(
        "sample.csv",
        [ReportColumn("name", "Nombre", "Name"), ReportColumn("at", "Fecha", "Date")],
        [{"name": "=2+2", "at": datetime(2026, 9, 3, 10, 30)}],
    )

    response = csv_report_response(result, "en")

    assert response.status_code == 200
    assert response.media_type == "text/csv; charset=utf-8"
    assert response.body.startswith(b"\xef\xbb\xbf")
    decoded = response.body.decode("utf-8-sig")
    assert decoded.startswith("Name,Date\r\n")
    assert "'=2+2,2026-09-03T10:30:00" in decoded
    assert response.headers["content-disposition"] == 'attachment; filename="sample.csv"'


def test_csv_report_returns_no_content_when_filters_match_no_rows():
    response = csv_report_response(ReportResult("empty.csv", [ReportColumn("id", "ID", "ID")], []))
    assert response.status_code == 204
    assert response.body == b""


def test_report_date_range_rejects_inverted_dates():
    with pytest.raises(ErclaveError) as error:
        validate_date_range(date(2026, 9, 4), date(2026, 9, 3))
    assert error.value.code == "report_date_range_invalid"
    assert error.value.status_code == 422


def test_csv_report_requires_narrower_filters_over_the_row_limit(monkeypatch):
    monkeypatch.setattr(csv_reports, "REPORT_MAX_ROWS", 1)
    result = ReportResult("large.csv", [ReportColumn("id", "ID", "ID")], [{"id": 1}, {"id": 2}])
    with pytest.raises(ErclaveError) as error:
        csv_report_response(result)
    assert error.value.code == "report_row_limit_exceeded"
    assert error.value.details == {"max_rows": 1}
