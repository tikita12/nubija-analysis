# 누비자 이용 데이터 분석

2025년 창원시 공영자전거 누비자 대여 이력과 과거 월별 이용현황을 분석해 일별·월별·시간대·공휴일 패턴과 장기 추이를 확인하는 프로젝트입니다.

## 실행 환경

- Python 3.14
- pandas 3.0.6
- numpy 2.5.3
- matplotlib 3.11.2

## 필요한 파일 배치

프로젝트 폴더에 다음 구조로 원자료를 둡니다. 큰 원본 CSV는 저장소에 올리는 대신, 허가된 공식 출처에서 받은 뒤 아래 위치에 직접 복사하는 것을 권장합니다.

```text
nubija-analysis/
├─ run_analysis.py
├─ data/
│  ├─ 경상남도 창원시_공영자전거 누비자 대여 반납 이력_20251231.csv
│  ├─ 경상남도 창원시_누비자  이용현황_20230331.csv
│  └─ reference/
│     └─ holidays_2025.csv
├─ images/                 # 실행 시 그래프 생성
├─ data/processed/         # 실행 시 분석 CSV 생성
├─ README.md
├─ REPORT.md
└─ AI_USAGE_LOG.md
```

공휴일 CSV는 UTF-8-SIG 인코딩이며 `date,name` 두 컬럼을 사용합니다. 날짜는 `YYYY-MM-DD` 형식입니다.

```csv
date,name
2025-01-01,신정
```

원자료 출처:

- [공공데이터포털: 경상남도 창원시 공영자전거 누비자 대여·반납 이력 (2025년 파일 포함)](https://www.data.go.kr/data/15126280/fileData.do)
- [공공데이터포털: 경상남도 창원시 누비자 이용현황](https://www.data.go.kr/data/15075281/fileData.do)
- [대한민국 정책브리핑: 2025년 월력요항](https://www.korea.kr/news/policyNewsView.do?newsId=148936865)
- [대한민국 정책브리핑: 2025년 1월 27일 임시공휴일 지정](https://www.korea.kr/news/policyNewsView.do?newsId=148938559)
- [대한민국 정책브리핑: 2025년 6월 3일 임시공휴일 지정](https://www.korea.kr/news/policyNewsView.do?newsId=148941443)

## 설치와 실행

프로젝트 폴더에서 가상환경을 활성화한 뒤 필요한 라이브러리를 설치합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pandas==3.0.6 numpy==2.5.3 matplotlib==3.11.2
python run_analysis.py
```

스크립트는 프로젝트의 `data` 폴더에서 파일을 찾아 처리하고, 분석 결과를 `data/processed`와 `images`에 저장합니다. 기본 실행은 원자료 파일을 변경하지 않습니다.

결과를 다른 위치에 두려면 다음처럼 출력 폴더를 지정할 수 있습니다.

```powershell
python run_analysis.py --output-dir .\run-output
```

## 생성 결과

`data/processed/`에는 일별·시간대별 집계, 월별·요일별 요약, 공휴일 요약, 장기 월별 비교 CSV가 저장됩니다. `images/`에는 다음 그래프 5개가 생성됩니다.

- `01_daily_trend.png`: 일별 대여량과 7일 이동평균
- `02_monthly_average.png`: 월별 하루 평균 대여량
- `03_hourly_profile.png`: 평일·주말 시간대별 하루 평균
- `04_holiday_comparison.png`: 공휴일과 일반일 비교
- `05_long_term_monthly.png`: 과거와 2025년 월별 장기 추이

## 해석 시 주의

- 2025년 7월은 원자료에 기록이 없어 0건으로 처리하지 않았습니다. 따라서 2025년 합계는 관측된 11개월의 합입니다.
- 과거 자료는 2023년 3월까지이며, 2023년 4월부터 2024년 12월까지 공백이 있습니다.
- 공휴일 비교는 관측 평균의 비교입니다. 특히 공휴일 주말은 표본이 2일뿐이므로 일반화에 주의해야 합니다.
- 데이터만으로 날씨·행사·통근 같은 원인을 확정하지 않습니다.

분석 결과와 한계는 [REPORT.md](REPORT.md), AI 활용 내역은 [AI_USAGE_LOG.md](AI_USAGE_LOG.md)에 기록했습니다.
