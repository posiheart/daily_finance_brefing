from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from .models import DailyReport, MarketDefinition
from .provider import FinanceDataProvider

SEOUL = ZoneInfo("Asia/Seoul")


def load_config(path: Path) -> tuple[str, list[MarketDefinition]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    markets = [MarketDefinition(**item) for item in raw["markets"]]
    return raw.get("title", "전일 시장 요약"), markets


def collect_report(
    config_path: Path,
    report_date: date,
    provider: FinanceDataProvider | None = None,
) -> DailyReport:
    title, markets = load_config(config_path)
    provider = provider or FinanceDataProvider()
    return DailyReport(
        title=title,
        report_date=report_date.isoformat(),
        generated_at=datetime.now(SEOUL).isoformat(timespec="seconds"),
        timezone="Asia/Seoul",
        snapshots=tuple(provider.snapshot(market, report_date) for market in markets),
    )


def write_report(report: DailyReport, data_root: Path) -> Path:
    destination = data_root / report.report_date / "market-summary.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, destination)
    return destination

