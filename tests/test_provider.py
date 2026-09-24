from datetime import date

import pandas as pd
import pytest

from daily_finance_briefing.models import MarketDefinition
from daily_finance_briefing.provider import FinanceDataProvider


def test_snapshot_uses_latest_two_non_null_closes():
    frame = pd.DataFrame(
        {"Close": [100.0, None, 105.0]},
        index=pd.to_datetime(["2026-09-15", "2026-09-16", "2026-09-18"]),
    )
    provider = FinanceDataProvider(reader=lambda *_: frame, retry_delay=0)
    result = provider.snapshot(MarketDefinition("TEST", "테스트", "국내"), date(2026, 9, 19))
    assert result.status == "ok"
    assert result.value == 105
    assert result.change_percent == pytest.approx(5)
    assert result.price_date == "2026-09-18"


def test_snapshot_uses_configured_data_symbol_but_keeps_report_symbol():
    calls = []
    frame = pd.DataFrame(
        {"Close": [100.0, 101.0]},
        index=pd.to_datetime(["2026-09-22", "2026-09-23"]),
    )

    def reader(symbol, start, end):
        calls.append((symbol, start, end))
        return frame

    provider = FinanceDataProvider(reader=reader, retry_delay=0)
    market = MarketDefinition(
        "KS11", "코스피", "국내", data_symbol="YAHOO:^KS11"
    )

    result = provider.snapshot(market, date(2026, 9, 23))

    assert calls == [("YAHOO:^KS11", "2026-09-09", "2026-09-24")]
    assert result.symbol == "KS11"
    assert result.price_date == "2026-09-23"


def test_snapshot_requests_day_after_report_date_to_include_that_days_close():
    calls = []
    frame = pd.DataFrame(
        {"Close": [7007.72, 7123.45]},
        index=pd.to_datetime(["2026-09-23", "2026-09-24"]),
    )

    def reader(symbol, start, end):
        calls.append((symbol, start, end))
        return frame

    provider = FinanceDataProvider(reader=reader, retry_delay=0)
    result = provider.snapshot(
        MarketDefinition("KS11", "코스피", "국내", data_symbol="YAHOO:^KS11"),
        date(2026, 9, 24),
    )

    assert calls == [("YAHOO:^KS11", "2026-09-10", "2026-09-25")]
    assert result.value == 7123.45
    assert result.price_date == "2026-09-24"
    assert result.previous_date == "2026-09-23"


def test_snapshot_requeries_yahoo_through_previous_day_when_today_is_missing():
    calls = []
    stale = pd.DataFrame(
        {"Close": [6894.23, 7007.72]},
        index=pd.to_datetime(["2026-09-18", "2026-09-21"]),
    )
    refreshed = pd.DataFrame(
        {"Close": [7007.72, 7100.0]},
        index=pd.to_datetime(["2026-09-21", "2026-09-23"]),
    )

    def reader(symbol, start, end):
        calls.append((symbol, start, end))
        return stale if end == "2026-09-25" else refreshed

    provider = FinanceDataProvider(reader=reader, retry_delay=0)
    result = provider.snapshot(
        MarketDefinition("KQ11", "코스닥", "국내", data_symbol="YAHOO:^KQ11"),
        date(2026, 9, 24),
    )

    assert calls == [
        ("YAHOO:^KQ11", "2026-09-10", "2026-09-25"),
        ("YAHOO:^KQ11", "2026-09-10", "2026-09-24"),
    ]
    assert result.value == 7100.0
    assert result.price_date == "2026-09-23"
    assert result.previous_date == "2026-09-21"


def test_snapshot_returns_unavailable_instead_of_stopping_report():
    def fail(*_):
        raise ConnectionError("temporary")

    result = FinanceDataProvider(reader=fail, retries=2, retry_delay=0).snapshot(
        MarketDefinition("TEST", "테스트", "국내"), date(2026, 9, 19)
    )
    assert result.status == "unavailable"
    assert "temporary" in result.error
