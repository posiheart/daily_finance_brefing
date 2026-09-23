from __future__ import annotations

from datetime import date, timedelta
from time import sleep
from typing import Any, Callable

from .models import MarketDefinition, MarketSnapshot, iso_date


class FinanceDataProvider:
    """FinanceDataReader를 감싸는 재시도 가능한 데이터 공급자."""

    def __init__(
        self,
        reader: Callable[..., Any] | None = None,
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        if reader is None:
            import FinanceDataReader as fdr

            reader = fdr.DataReader
        self.reader = reader
        self.retries = retries
        self.retry_delay = retry_delay

    def snapshot(self, market: MarketDefinition, report_date: date) -> MarketSnapshot:
        start = report_date - timedelta(days=14)
        try:
            # Some FinanceDataReader bare symbols use its GitHub cache, which
            # can lag behind the latest trading day. A configured source symbol
            # lets time-sensitive indices and commodities query Yahoo directly
            # without changing the stable symbol stored in reports.
            frame = self._read(market.data_symbol or market.symbol, start, report_date)
            close = frame["Close"].dropna()
            close = close[~close.index.duplicated(keep="last")].sort_index()
            if len(close) < 2:
                raise ValueError("최근 종가가 2개 미만입니다")
            previous, latest = float(close.iloc[-2]), float(close.iloc[-1])
            if previous == 0:
                raise ValueError("직전 종가가 0입니다")
            change = (latest / previous - 1) * 100
            return MarketSnapshot(
                symbol=market.symbol,
                name=market.name,
                category=market.category,
                decimals=market.decimals,
                unit=market.unit,
                status="ok",
                value=latest,
                previous_value=previous,
                change_percent=change,
                price_date=iso_date(close.index[-1]),
                previous_date=iso_date(close.index[-2]),
            )
        except Exception as exc:  # 개별 지표 실패가 전체 보고서를 막지 않게 한다.
            return MarketSnapshot(
                symbol=market.symbol,
                name=market.name,
                category=market.category,
                decimals=market.decimals,
                unit=market.unit,
                status="unavailable",
                error=str(exc),
            )

    def _read(self, symbol: str, start: date, end: date) -> Any:
        error: Exception | None = None
        for attempt in range(self.retries):
            try:
                return self.reader(symbol, start.isoformat(), end.isoformat())
            except Exception as exc:
                error = exc
                if attempt + 1 < self.retries:
                    sleep(self.retry_delay * (2**attempt))
        assert error is not None
        raise error
