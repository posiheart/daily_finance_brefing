# GitHub Actions로 반복 작업 자동화하기

네, 가능합니다. 현재 저장소는 **국내 + 해외 + 환율 + 상품 섹션**을 자동 생성하도록 구성되어 있습니다.

## 추천 아키텍처
1. `src/main.py`를 단일 실행 진입점으로 둡니다.
2. 워크플로우에서 Python/의존성(`FinanceDataReader`, `pandas`, `jinja2`)을 설치합니다.
3. `python src/main.py --output-dir output`으로 HTML을 생성합니다.
4. 변경된 `output/*.html`이 있으면 자동 커밋/푸시합니다.

## 스케줄 설정
- GitHub Actions `cron`은 **UTC 기준**입니다.
- 한국시간 오전 10시 17분은 UTC 01:17이므로 아래처럼 설정합니다.

```yaml
schedule:
  - cron: "17 1 * * 1-5"
```

> 참고: `1-5`는 월~금 실행이며, 공휴일 구분은 별도 로직이 필요합니다.

## 테스트 실행: target date 지정
수동 실행(`workflow_dispatch`)에서 `target_date`를 입력하면 해당 날짜를 **실행일(run date)** 로 간주해 계산할 수 있습니다.

- 입력 형식: `YYYY-MM-DD` (예: `2026-02-10`)
- 의미: `2026-02-10`을 넣으면 **당일(2/10)은 제외**하고 전일 거래일(2/9)을 기준으로 요약을 생성합니다.
- 워크플로우 실행 명령:
  - 입력값 있음: `python src/main.py --output-dir output --target-date <YYYY-MM-DD>`
  - 입력값 없음: `python src/main.py --output-dir output`

로컬에서도 동일하게 재현 가능합니다.

```bash
python src/main.py --output-dir output --target-date 2026-02-10
```

## 현재 구현 범위
- 국내:
  - 코스피(`KS11`), 코스닥(`KQ11`)
- 해외:
  - 다우 산업(`DJI`), 나스닥 종합(`IXIC`), 상해 종합(`SSEC`), 니케이225(`N225`)
- 환율:
  - 원/달러(`USD/KRW`), 중국 위안/달러(`USD/CNY`)
- 상품:
  - 금(`GC=F`), 은(`SI=F`), WTI(`CL=F`)
- 각 지수/환율별 최근 2개 거래일 종가로 전일 대비 등락률을 계산해 `▲/▼`와 색상(상승 빨강, 하락 파랑)으로 표시합니다.
- 각 지수/환율/상품별 최근 2개 거래일 종가로 전일 대비 등락률을 계산해 `▲/▼`와 색상(상승 빨강, 하락 파랑)으로 표시합니다.
- 데이터 수집 실패 시 전체 생성은 유지하고, HTML 하단에 경고 메시지를 출력합니다.

## 다음 확장 권장
- Jinja2 템플릿 분리
- 실패 알림(Slack/Webhook) 연동
