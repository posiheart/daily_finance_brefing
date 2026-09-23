from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class MarketDefinition:
    symbol: str
    name: str
    category: str
    decimals: int = 2
    unit: str = ""
    data_symbol: str | None = None


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    name: str
    category: str
    decimals: int
    unit: str
    status: str
    value: float | None = None
    previous_value: float | None = None
    change_percent: float | None = None
    price_date: str | None = None
    previous_date: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class DailyReport:
    title: str
    report_date: str
    generated_at: str
    timezone: str
    snapshots: tuple[MarketSnapshot, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "DailyReport":
        return cls(
            title=value["title"],
            report_date=value["report_date"],
            generated_at=value["generated_at"],
            timezone=value["timezone"],
            snapshots=tuple(MarketSnapshot(**item) for item in value["snapshots"]),
        )


def iso_date(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    if hasattr(value, "date"):
        return value.date().isoformat()
    return str(value)[:10]
