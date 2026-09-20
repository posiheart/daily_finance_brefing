import json
from datetime import date

from daily_finance_briefing.models import MarketSnapshot
from daily_finance_briefing.render import render_site
from daily_finance_briefing.service import collect_report, write_report


class StubProvider:
    def snapshot(self, market, report_date):
        return MarketSnapshot(
            symbol=market.symbol, name=market.name, category=market.category,
            decimals=market.decimals, unit=market.unit, status="ok", value=105,
            previous_value=100, change_percent=5, price_date="2026-09-18",
            previous_date="2026-09-17",
        )


def test_collect_write_and_render(tmp_path):
    config = tmp_path / "markets.yaml"
    config.write_text("title: 전일 시장 요약\nmarkets:\n  - {symbol: TEST, name: 코스피, category: 국내}\n", encoding="utf-8")
    report = collect_report(config, date(2026, 9, 19), StubProvider())
    path = write_report(report, tmp_path / "data")
    assert json.loads(path.read_text(encoding="utf-8"))["report_date"] == "2026-09-19"
    render_site(tmp_path / "data", tmp_path / "public")
    html = (tmp_path / "public" / "index.html").read_text(encoding="utf-8")
    assert "전일 시장 요약" in html
    assert "▲" in html
    assert "+5.00%" in html

