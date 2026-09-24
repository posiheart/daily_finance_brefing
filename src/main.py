"""Daily market briefing entrypoint.

Phase 1: domestic + overseas + forex + commodity sections with FinanceDataReader.
Supports optional target date for reproducible runs in GitHub Actions.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import FinanceDataReader as fdr


@dataclass
class IndexSummary:
    name: str
    close: float | None
    change_pct: float | None
    arrow: str
    color_class: str
    base_date: str | None
    decimals: int = 2
    error: str | None = None


def _parse_target_date(target_date: str | None) -> date | None:
    if not target_date:
        return None
    return datetime.strptime(target_date, "%Y-%m-%d").date()


def _format_close(value: float | None, decimals: int) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def _format_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{abs(value):.2f}%"


def fetch_index_summary(name: str, symbol: str, run_date: date, decimals: int = 2) -> IndexSummary:
    end_dt = datetime.combine(run_date, datetime.min.time())
    start_dt = end_dt - timedelta(days=40)

    try:
        df = fdr.DataReader(symbol, start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
        if "Close" not in df.columns:
            return IndexSummary(
                name=name,
                close=None,
                change_pct=None,
                arrow="-",
                color_class="na",
                base_date=None,
                decimals=decimals,
                error="not-enough-data",
            )

        close_series = df["Close"].dropna()
        # "전일 시장 요약" 기준: 실행일(run_date) 당일 데이터는 제외하고 직전 거래일을 기준일로 사용
        close_series = close_series[close_series.index.date < run_date]

        last_two = close_series.tail(2)
        if len(last_two) < 2:
            return IndexSummary(
                name=name,
                close=None,
                change_pct=None,
                arrow="-",
                color_class="na",
                base_date=None,
                decimals=decimals,
                error="not-enough-close-values",
            )

        prev_close = float(last_two.iloc[0])
        close = float(last_two.iloc[1])
        change_pct = ((close - prev_close) / prev_close) * 100

        if change_pct > 0:
            arrow = "▲"
            color_class = "up"
        elif change_pct < 0:
            arrow = "▼"
            color_class = "down"
        else:
            arrow = "-"
            color_class = "flat"

        return IndexSummary(
            name=name,
            close=close,
            change_pct=change_pct,
            arrow=arrow,
            color_class=color_class,
            base_date=last_two.index[-1].strftime("%Y-%m-%d"),
            decimals=decimals,
        )
    except Exception as exc:  # noqa: BLE001
        return IndexSummary(
            name=name,
            close=None,
            change_pct=None,
            arrow="-",
            color_class="na",
            base_date=None,
            decimals=decimals,
            error=str(exc),
        )


def _render_table_rows(items: list[IndexSummary], columns: int) -> str:
    rows: list[str] = []
    for i in range(0, len(items), columns):
        row_items = items[i : i + columns]
        header_row = "".join(f"<th>{item.name}</th>" for item in row_items)
        value_row = "".join(
            (
                "<td>"
                f'<span class="{item.color_class}">{_format_close(item.close, item.decimals)} {item.arrow} {_format_pct(item.change_pct)}</span>'
                "</td>"
            )
            for item in row_items
        )
        rows.append(f"<tr>{header_row}</tr>")
        rows.append(f"<tr>{value_row}</tr>")
    return "\n".join(rows)


def _render_section(title: str, items: list[IndexSummary], columns: int) -> str:
    return (
        f"<h2>{title}</h2>"
        "\n"
        "<table>"
        f"{_render_table_rows(items, columns)}"
        "</table>"
    )


def render_html(
    domestic_items: list[IndexSummary],
    overseas_items: list[IndexSummary],
    forex_items: list[IndexSummary],
    commodity_items: list[IndexSummary],
    generated_at: str,
    requested_target_date: str | None,
) -> str:
    all_items = domestic_items + overseas_items + forex_items + commodity_items
    base_dates = [item.base_date for item in all_items if item.base_date]
    base_date_text = max(base_dates) if base_dates else "확인 불가"
    request_date_text = requested_target_date if requested_target_date else "자동(오늘 실행)"

    warning = ""
    failed_items = [item for item in all_items if item.error]
    if failed_items:
        details = ", ".join(f"{item.name}: {item.error}" for item in failed_items)
        warning = f"<p class=\"warning\">일부 데이터를 불러오지 못했습니다 ({details}).</p>"

    domestic_html = _render_section("국내", domestic_items, columns=2)
    overseas_html = _render_section("해외", overseas_items, columns=2)
    forex_html = _render_section("환율", forex_items, columns=2)
    commodity_html = _render_section("상품", commodity_items, columns=1)

    return f"""<!doctype html>
<html lang=\"ko\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>전일 시장 요약</title>
    <style>
      body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", sans-serif;
        margin: 24px;
        color: #222;
      }}
      h1 {{ margin: 0 0 24px; }}
      h2 {{ margin: 24px 0 8px; }}
      table {{
        width: 100%;
        max-width: 720px;
        border-collapse: collapse;
        border-top: 1px solid #666;
        margin-bottom: 24px;
      }}
      th, td {{
        width: 50%;
        border: 1px solid #d6d6d6;
        text-align: center;
        padding: 14px 10px;
        font-size: 30px;
      }}
      th {{ font-weight: 700; background: #fafafa; }}
      .up {{ color: #f44336; }}
      .down {{ color: #1976d2; }}
      .flat {{ color: #444; }}
      .na {{ color: #888; }}
      .meta {{ color: #666; font-size: 20px; margin: 6px 0; }}
      .warning {{ color: #b26a00; font-size: 18px; max-width: 720px; }}
    </style>
  </head>
  <body>
    <h1>전일 시장 요약</h1>
    {domestic_html}
    {overseas_html}
    {forex_html}
    {commodity_html}
    <p class=\"meta\">요청 실행일: {request_date_text}</p>
    <p class=\"meta\">기준 거래일: {base_date_text}</p>
    <p class=\"meta\">생성 시각: {generated_at}</p>
    {warning}
  </body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--target-date", default=None, help="YYYY-MM-DD 형식. 테스트/재현 실행용(실행일)")
    args = parser.parse_args()

    run_date = _parse_target_date(args.target_date) or datetime.now().date()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    domestic_items = [
        fetch_index_summary("코스피", "KS11", run_date),
        fetch_index_summary("코스닥", "KQ11", run_date),
    ]
    overseas_items = [
        fetch_index_summary("다우 산업", "DJI", run_date),
        fetch_index_summary("나스닥 종합", "IXIC", run_date),
        fetch_index_summary("상해 종합", "SSEC", run_date),
        fetch_index_summary("니케이225", "N225", run_date),
    ]
    forex_items = [
        fetch_index_summary("원/달러", "USD/KRW", run_date, decimals=2),
        fetch_index_summary("중국 위안/달러", "USD/CNY", run_date, decimals=3),
    ]
    commodity_items = [
        fetch_index_summary("금", "GC=F", run_date, decimals=2),
        fetch_index_summary("은", "SI=F", run_date, decimals=2),
        fetch_index_summary("WTI", "CL=F", run_date, decimals=2),
    ]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename_date = run_date.strftime("%Y-%m-%d")
    output_path = output_dir / f"{filename_date}_brief.html"
    html = render_html(
        domestic_items,
        overseas_items,
        forex_items,
        commodity_items,
        generated_at,
        args.target_date,
    )
    output_path.write_text(html, encoding="utf-8")
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
