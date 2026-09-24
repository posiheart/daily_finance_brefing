import json
import subprocess
from datetime import date
from pathlib import Path

import pytest
import yaml

from daily_finance_briefing.cli import build_parser
from daily_finance_briefing.models import DailyReport, MarketSnapshot
from daily_finance_briefing.render import render_site, report_filename
from daily_finance_briefing.service import collect_report, load_config, write_report


class StubProvider:
    def snapshot(self, market, report_date):
        return MarketSnapshot(
            symbol=market.symbol, name=market.name, category=market.category,
            decimals=market.decimals, unit=market.unit, status="ok", value=105,
            previous_value=100, change_percent=5, price_date="2026-09-18",
            previous_date="2026-09-17",
        )


def test_cli_writes_generated_html_to_output_by_default():
    parser = build_parser()

    assert parser.parse_args(["generate"]).output_dir == Path("output")
    assert parser.parse_args(["render"]).output_dir == Path("output")


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def construct_unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


def test_workflow_runs_daily_and_commits_generated_output():
    workflow = Path(".github/workflows/daily-summary.yml").read_text(encoding="utf-8")
    save_script = Path("scripts/save-generated-output.sh").read_text(encoding="utf-8")

    parsed_workflow = yaml.load(workflow, Loader=UniqueKeyLoader)
    steps = parsed_workflow["jobs"]["build-and-deploy"]["steps"]
    actions = {step["uses"] for step in steps if "uses" in step}
    assert 'cron: "*/5 * * * *"' in workflow
    assert parsed_workflow["jobs"]["build-and-deploy"]["runs-on"] == "ubuntu-24.04"
    assert actions == {
        "actions/checkout@v7",
        "actions/setup-python@v7",
        "actions/configure-pages@v6",
        "actions/upload-pages-artifact@v5",
        "actions/deploy-pages@v5",
    }
    assert "run: ./scripts/save-generated-output.sh" in workflow
    assert "path: output" in workflow
    assert "git add data" in save_script
    assert "git add --force output" in save_script
    subprocess.run(["bash", "-n", "scripts/save-generated-output.sh"], check=True)


def test_workflow_validation_rejects_duplicate_run_keys():
    with pytest.raises(ValueError, match="duplicate YAML key: run"):
        yaml.load("- name: broken\n  run: first\n  run: second\n", Loader=UniqueKeyLoader)


def test_indices_and_commodities_use_live_yahoo_tickers():
    _, markets = load_config(Path("config/markets.yaml"))
    symbols = {market.symbol: market.data_symbol for market in markets}

    assert symbols == {
        "KS11": "YAHOO:^KS11",
        "KQ11": "YAHOO:^KQ11",
        "DJI": "YAHOO:^DJI",
        "IXIC": "YAHOO:^IXIC",
        "SSEC": "YAHOO:000001.SS",
        "N225": "YAHOO:^N225",
        "USD/KRW": None,
        "USD/CNY": None,
        "GC=F": "YAHOO:GC=F",
        "SI=F": "YAHOO:SI=F",
        "CL=F": "YAHOO:CL=F",
    }


def test_report_filename_uses_report_date_and_generated_time():
    report = DailyReport(
        title="전일 시장 요약",
        report_date="2026-02-05",
        generated_at="2026-02-05T10:00:31+09:00",
        timezone="Asia/Seoul",
        snapshots=(),
    )

    assert report_filename(report) == "2026-02-05_AM10.00_brief.html"


def test_collect_write_and_render(tmp_path):
    config = tmp_path / "markets.yaml"
    config.write_text("title: 전일 시장 요약\nmarkets:\n  - {symbol: TEST, name: 코스피, category: 국내}\n", encoding="utf-8")
    report = collect_report(config, date(2026, 9, 19), StubProvider())
    path = write_report(report, tmp_path / "data")
    assert json.loads(path.read_text(encoding="utf-8"))["report_date"] == "2026-09-19"
    render_site(tmp_path / "data", tmp_path / "output")
    html = (tmp_path / "output" / "index.html").read_text(encoding="utf-8")
    assert "전일 시장 요약" in html
    assert "▲" in html
    assert "+5.00%" in html
    assert "투자 권유가 아닙니다" not in html
    assert len(list((tmp_path / "output").glob("2026-09-19_*_brief.html"))) == 1
