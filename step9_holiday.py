from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent

daily_path = PROJECT_DIR / "data" / "processed" / "daily_counts.csv"
holiday_path = PROJECT_DIR / "data" / "reference" / "holidays_2025.csv"
output_dir = PROJECT_DIR / "data" / "processed"
image_dir = PROJECT_DIR / "images"

# 일별 집계 파일에서 앞의 두 열을 날짜와 이용건수로 사용합니다.
daily = pd.read_csv(daily_path, encoding="utf-8-sig")
daily = daily.iloc[:, :2].copy()
daily.columns = ["date", "trips"]

daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
daily["trips"] = pd.to_numeric(daily["trips"], errors="coerce")
daily = daily.dropna(subset=["date", "trips"])

# 공휴일 파일을 읽고 날짜를 연결합니다.
holidays = pd.read_csv(holiday_path, encoding="utf-8-sig")
holidays["date"] = pd.to_datetime(holidays["date"], errors="coerce")
holidays = holidays.dropna(subset=["date"])

daily = daily.merge(
    holidays[["date", "name"]],
    on="date",
    how="left",
)
daily = daily.rename(columns={"name": "holiday_name"})
daily["is_holiday"] = daily["holiday_name"].notna()
daily["weekday"] = daily["date"].dt.weekday

# 공휴일 여부와 주말 여부를 나누어 비교합니다.
conditions = [
    daily["is_holiday"] & daily["weekday"].lt(5),
    daily["is_holiday"] & daily["weekday"].ge(5),
    ~daily["is_holiday"] & daily["weekday"].ge(5),
]
choices = ["공휴일(평일)", "공휴일(주말)", "일반 주말"]
daily["구분"] = np.select(conditions, choices, default="일반 평일")

order = ["일반 평일", "공휴일(평일)", "일반 주말", "공휴일(주말)"]
summary = (
    daily.groupby("구분")["trips"]
    .agg(["mean", "median", "count"])
    .reindex(order)
    .rename(columns={
        "mean": "하루평균이용건수",
        "median": "하루중앙값",
        "count": "관측일수",
    })
)

output_dir.mkdir(parents=True, exist_ok=True)
image_dir.mkdir(parents=True, exist_ok=True)

summary.to_csv(output_dir / "holiday_summary.csv", encoding="utf-8-sig")

holiday_daily = daily[daily["is_holiday"]][
    ["date", "holiday_name", "trips"]
].sort_values("date")
holiday_daily.to_csv(
    output_dir / "holiday_daily_counts.csv",
    index=False,
    encoding="utf-8-sig",
)

# 그래프에 한글이 보이도록 Windows 기본 한글 글꼴을 지정합니다.
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

plot_data = summary.dropna(subset=["하루평균이용건수"])

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(
    plot_data.index,
    plot_data["하루평균이용건수"],
    color=["#4C78A8", "#F58518", "#4C78A8", "#F58518"],
)

for bar, (_, row) in zip(bars, plot_data.iterrows()):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        f"{row['하루평균이용건수']:,.0f}건\n(n={int(row['관측일수'])})",
        ha="center",
        va="bottom",
    )

ax.set_title("공휴일과 일반일의 누비자 하루 평균 이용량 (2025)")
ax.set_ylabel("하루 평균 대여 건수")
ax.set_xlabel("날짜 구분")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(image_dir / "04_holiday_comparison.png", dpi=150)
plt.close(fig)

print("공휴일 및 일반일 요약:")
print(summary.round(1))
print(f"\n공휴일별 이용량: {output_dir / 'holiday_daily_counts.csv'}")
print(f"그래프: {image_dir / '04_holiday_comparison.png'}")