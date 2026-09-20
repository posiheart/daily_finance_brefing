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


def test_snapshot_returns_unavailable_instead_of_stopping_report():
    def fail(*_):
        raise ConnectionError("temporary")

    result = FinanceDataProvider(reader=fail, retries=2, retry_delay=0).snapshot(
        MarketDefinition("TEST", "테스트", "국내"), date(2026, 9, 19)
    )
    assert result.status == "unavailable"
    assert "temporary" in result.error
