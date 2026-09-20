from __future__ import annotations

import json
import shutil
from collections import OrderedDict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import DailyReport


def format_number(value: float, decimals: int) -> str:
    return f"{value:,.{decimals}f}"


def load_reports(data_root: Path) -> list[DailyReport]:
    reports = []
    for path in sorted(data_root.glob("*/market-summary.json")):
        reports.append(DailyReport.from_dict(json.loads(path.read_text(encoding="utf-8"))))
    return reports


def render_site(data_root: Path, public_root: Path) -> None:
    reports = load_reports(data_root)
    if not reports:
        raise ValueError("렌더링할 보고서가 없습니다")
    package_root = Path(__file__).parent
    environment = Environment(
        loader=FileSystemLoader(package_root / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    environment.filters["number"] = format_number
    template = environment.get_template("daily_summary.html")
    css = (package_root / "static" / "summary.css").read_text(encoding="utf-8")
    public_root.mkdir(parents=True, exist_ok=True)

    for report in reports:
        groups: OrderedDict[str, list] = OrderedDict()
        for snapshot in report.snapshots:
            groups.setdefault(snapshot.category, []).append(snapshot)
        html = template.render(
            report=report, groups=groups, css=css, archive=reports, root_prefix="../../../"
        )
        target = public_root / "archive" / report.report_date / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")

    latest = reports[-1]
    groups = OrderedDict()
    for snapshot in latest.snapshots:
        groups.setdefault(snapshot.category, []).append(snapshot)
    (public_root / "latest").mkdir(exist_ok=True)
    (public_root / "latest" / "index.html").write_text(
        template.render(report=latest, groups=groups, css=css, archive=reports, root_prefix="../"),
        encoding="utf-8",
    )
    shutil.copy2(data_root / latest.report_date / "market-summary.json", public_root / "latest" / "market-summary.json")
    (public_root / "index.html").write_text(
        template.render(report=latest, groups=groups, css=css, archive=reports, root_prefix=""),
        encoding="utf-8",
    )
