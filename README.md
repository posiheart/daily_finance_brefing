# Daily Finance Briefing

FinanceDataReader로 국내외 지수, 환율, 상품의 최근 두 거래일 종가를 수집하고 전일 대비 등락률을 담은 정적 HTML을 만듭니다. GitHub Actions가 매일 한국 시간 오전 10시 7분에 보고서를 생성하고 GitHub Pages에 배포합니다.

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
daily-finance-briefing generate
```

날짜를 지정하거나 저장된 데이터로 화면만 다시 만들 수도 있습니다.

```bash
daily-finance-briefing generate --report-date 2026-09-19
daily-finance-briefing render
```

결과는 `data/YYYY-MM-DD/market-summary.json`과 `public/`에 생성됩니다. 개별 지표 수집 실패는 `데이터 없음`으로 표시되어 다른 지표의 보고서 생성을 막지 않습니다.

## GitHub Pages 설정

저장소의 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 선택합니다. 예약 작업은 UTC 01:07에 실행되며 한국 표준시로 오전 10시 7분입니다. Actions의 예약 실행은 서비스 부하에 따라 지연될 수 있습니다.

필요하면 Actions의 **Daily market summary → Run workflow**에서 날짜를 입력해 수동으로 다시 생성할 수 있습니다. 보호된 기본 브랜치에서 Actions의 직접 push가 차단되어 있다면 `data/` 저장용 브랜치를 별도로 사용하도록 워크플로를 조정해야 합니다.

## 데이터 주의사항

- 보고서 날짜가 아니라 각 카드에 표시된 실제 종가 날짜를 확인하세요.
- 환율은 설정에 적힌 통화쌍의 숫자 변화 방향을 그대로 표시합니다.
- 금·은·WTI 심볼은 선물 가격이며 단위는 카드에 표시됩니다.
- 이 보고서는 참고 정보이며 투자 권유가 아닙니다.
