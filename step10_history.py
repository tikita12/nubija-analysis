from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent

history_path = (
    PROJECT_DIR
    / "data"
    / "경상남도 창원시_누비자  이용현황_20230331.csv"
)
daily_path = PROJECT_DIR / "data" / "processed" / "daily_counts.csv"
output_dir = PROJECT_DIR / "data" / "processed"
image_dir = PROJECT_DIR / "images"

# 과거 월별 자료: CP949 인코딩
history = pd.read_csv(history_path, encoding="cp949")
history = history.iloc[:, :2].copy()
history.columns = ["date", "trips"]
history["date"] = pd.to_datetime(history["date"], errors="coerce")
history["trips"] = pd.to_numeric(history["trips"], errors="coerce")
history = history.dropna(subset=["date", "trips"]).sort_values("date")

# 2025년 일별 자료를 월별 이용량으로 합산
daily = pd.read_csv(daily_path, encoding="utf-8-sig")
daily = daily.iloc[:, :2].copy()
daily.columns = ["date", "trips"]
daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
daily["trips"] = pd.to_numeric(daily["trips"], errors="coerce")
daily = daily.dropna(subset=["date", "trips"])

monthly_2025 = (
    daily.set_index("date")["trips"]
    .resample("MS")
    .sum(min_count=1)
    .reindex(pd.date_range("2025-01-01", "2025-12-01", freq="MS"))
)

# 과거 자료와 2025년 자료를 구간별로 저장
history_output = history.assign(period="과거 월별 자료")
current_output = (
    monthly_2025.rename_axis("date")
    .reset_index()
    .assign(period="2025년 일별 자료에서 집계")
)
combined = pd.concat([history_output, current_output], ignore_index=True)
combined.to_csv(
    output_dir / "long_term_monthly_comparison.csv",
    index=False,
    encoding="utf-8-sig",
)

# 그래프
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(13, 6))

ax.plot(
    history["date"],
    history["trips"],
    color="#4C78A8",
    linewidth=1.5,
    label="과거 월별 자료 (2008.10–2023.03)",
)

# 2025년은 따로 그려 과거 자료의 끝과 연결하지 않습니다.
ax.plot(
    monthly_2025.index,
    monthly_2025.values,
    color="#F58518",
    marker="o",
    linewidth=1.8,
    label="2025년 자료",
)

ax.set_title("누비자 월별 이용량 장기 추이")
ax.set_xlabel("연월")
ax.set_ylabel("월 이용 건수")
ax.legend()
ax.grid(alpha=0.25)

fig.text(
    0.5,
    0.01,
    "자료 공백: 2023년 4월–2024년 12월, 2025년 7월은 기록 없음",
    ha="center",
    color="dimgray",
)
fig.tight_layout(rect=(0, 0.04, 1, 1))

image_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(image_dir / "05_long_term_monthly.png", dpi=150)
plt.close(fig)

# 완전한 연도끼리 과거 연간 이용량 비교
history["year"] = history["date"].dt.year
annual = history.groupby("year").agg(
    연간이용건수=("trips", "sum"),
    관측월수=("trips", "count"),
)
complete_years = annual[annual["관측월수"] == 12]

print("월별 과거 자료 행 수:", len(history))
print("과거 자료 기간:", history["date"].min().date(), "~", history["date"].max().date())
print("완전한 연도 중 이용량이 가장 많은 해:")
print(complete_years["연간이용건수"].idxmax(), complete_years["연간이용건수"].max())
print("2025년 관측 월 수:", int(monthly_2025.notna().sum()))
print("2025년 관측 월 이용량 합계:", int(monthly_2025.sum()))
print("그래프:", image_dir / "05_long_term_monthly.png")