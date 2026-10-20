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
├─ quality_checks.py       # 중복·대여 시간·일별 이상치 점검
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

## 데이터 수집 방법 및 이용조건

누비자 원자료는 위 공공데이터포털의 파일데이터 페이지에서 대상 파일을 다운로드해 `data/`에 배치합니다. 대여·반납 이력은 `20251231`, 월별 이용현황은 `20230331` 파일을 사용합니다. 최신 파일이 변경된 경우 페이지의 주기성 과거 데이터에서 해당 기준일 자료를 확인합니다. 이 프로젝트에는 원본 CSV 대신 집계 결과와 다운로드 경로를 제공합니다.

아래 내용은 **2026년 10월 20일 각 공식 페이지의 안내를 확인한 결과**입니다.

| 자료 | 공식 페이지에 표시된 이용조건 | 이 프로젝트의 사용 방식 |
|---|---|---|
| [누비자 대여·반납 이력](https://www.data.go.kr/data/15126280/fileData.do) | 무료, 이용허락범위 제한 없음 | 출발 날짜·시간별 건수 집계 |
| [누비자 월별 이용현황](https://www.data.go.kr/data/15075281/fileData.do) | 무료, 이용허락범위 제한 없음 | 월별 장기 추이 분석 |
| [2025년 월력요항 안내](https://www.korea.kr/news/policyNewsView.do?newsId=148936865) | 기사 텍스트: 공공누리 제4유형(출처표시·상업적 이용금지·변경금지) | 공휴일 날짜와 명칭 확인 |
| [1월 27일 임시공휴일 지정 안내](https://www.korea.kr/news/policyNewsView.do?newsId=148938559) | 기사 텍스트: 공공누리 제1유형(출처표시) | 해당 날짜와 명칭 확인 |
| [6월 3일 임시공휴일 지정 안내](https://www.korea.kr/news/policyNewsView.do?newsId=148941443) | 기사 텍스트: 공공누리 제1유형(출처표시) | 해당 날짜와 명칭 확인 |

`data/reference/holidays_2025.csv`는 위 안내의 날짜와 공휴일 명칭을 분석용으로 정리한 파일입니다. 기사 본문이나 사진·이미지는 저장소에 포함하지 않았습니다. 기사 텍스트의 이용조건을 사진·이미지 등 다른 자료에 그대로 적용하지 않습니다.

이 저장소에서 작성한 Python 코드에는 [MIT 라이선스](LICENSE)를 적용합니다. 외부 원자료와 참고 기사에는 각 제공처의 이용조건이 적용되며, 저장소의 MIT 라이선스가 해당 조건을 대체하지 않습니다. 데이터나 참고 자료를 재사용할 때는 연결된 공식 페이지의 최신 이용조건을 확인하세요. 집계 CSV와 그래프는 창원시 제공 자료를 이 프로젝트에서 가공한 분석 결과이며, 공식 통계 발표물이 아닙니다.

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

전체 실행에는 품질 점검도 포함됩니다. `data/processed/quality_summary.json`에 중복·출발/반납 시각·대여 시간·일별 IQR 점검 요약을, `daily_outlier_checks.csv`에 관측일별 후보 여부를 저장합니다. 후보는 자동 삭제하지 않으며, 기준과 유지 이유는 보고서에 설명했습니다. 기존 일별 집계가 있을 때 품질 점검만 다시 실행하려면 `python quality_checks.py`를 사용합니다.

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
