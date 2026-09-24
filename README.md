# Daily Finance Briefing

FinanceDataReader로 국내외 지수, 환율, 상품의 최근 두 거래일 종가를 수집하고 전일 대비 등락률을 담은 정적 HTML을 만듭니다. GitHub Actions가 5분마다 보고서를 생성하고 GitHub Pages에 배포합니다.

## 로컬 실행

참고 저장소의 GitHub Actions 환경과 동일하게 Python 3.11을 사용합니다. `pyenv`를 사용하면 저장소의 `.python-version`이 자동으로 적용됩니다.

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

결과는 `data/YYYY-MM-DD/market-summary.json`과 `output/index.html`에 생성됩니다. 날짜별 HTML은 `output/2026-02-05_AM10.00_brief.html` 형식의 이름으로 같은 폴더에 누적됩니다. 예약 실행과 **Run workflow** 수동 실행 모두 실행할 때 생성한 HTML을 `output/`에 커밋합니다. 개별 지표 수집 실패는 `데이터 없음`으로 표시되어 다른 지표의 보고서 생성을 막지 않습니다.

## GitHub Pages 설정

저장소의 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 선택합니다. `.github/workflows/daily-market-briefing.yml`은 참고 저장소와 같은 `ubuntu-latest`, Python 3.11, `Asia/Seoul` 환경을 사용하며, UTC 기준 매 5분(`*/5 * * * *`)마다 기본 브랜치에서 실행됩니다. 보고서 생성·커밋 작업은 Pages 배포 작업과 분리되어 있으므로 Pages 환경 승인이 대기 중이거나 배포 설정에 문제가 생겨도 다음 예약 보고서 생성 자체를 막지 않습니다. 다만 GitHub Actions의 예약 실행은 서비스 부하에 따라 지연될 수 있으며 정확히 5분 간격의 실행을 보장하지는 않습니다.

필요하면 Actions의 **Daily Market Briefing → Run workflow**에서 `target_date`를 입력해 수동으로 다시 생성할 수 있습니다. 보호된 기본 브랜치에서 Actions의 직접 push가 차단되어 있다면 `data/` 저장용 브랜치를 별도로 사용하도록 워크플로를 조정해야 합니다.

## 데이터 주의사항

- 보고서 날짜가 아니라 각 카드에 표시된 실제 종가 날짜를 확인하세요.
- 국내·해외 지수와 상품은 FinanceDataReader의 주기적 GitHub 캐시가 아닌 Yahoo 티커를 명시적으로 사용해 기준일 현재 최근 거래일 종가를 조회합니다.
- 환율은 설정에 적힌 통화쌍의 숫자 변화 방향을 그대로 표시합니다.
- 금·은·WTI 심볼은 선물 가격이며 단위는 카드에 표시됩니다.
