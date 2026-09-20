from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .render import render_site
from .service import SEOUL, collect_report, write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="일일 시장 요약 생성기")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate", help="데이터 수집 후 사이트 생성")
    generate.add_argument("--report-date", help="기준일(YYYY-MM-DD)")
    generate.add_argument("--config", type=Path, default=Path("config/markets.yaml"))
    generate.add_argument("--data-dir", type=Path, default=Path("data"))
    generate.add_argument("--public-dir", type=Path, default=Path("public"))
    render = subparsers.add_parser("render", help="저장된 JSON으로 사이트만 재생성")
    render.add_argument("--data-dir", type=Path, default=Path("data"))
    render.add_argument("--public-dir", type=Path, default=Path("public"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "render":
        render_site(args.data_dir, args.public_dir)
        return
    report_date = (
        datetime.strptime(args.report_date, "%Y-%m-%d").date()
        if args.report_date
        else datetime.now(SEOUL).date()
    )
    report = collect_report(args.config, report_date)
    write_report(report, args.data_dir)
    render_site(args.data_dir, args.public_dir)
    failed = sum(item.status != "ok" for item in report.snapshots)
    print(f"{report.report_date}: {len(report.snapshots) - failed}개 성공, {failed}개 누락")


if __name__ == "__main__":
    main()
