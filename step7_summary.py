from pathlib import Path

import numpy as np
import pandas as pd

project_dir = Path(__file__).resolve().parent
data_dir = project_dir / "data" / "processed"

daily = pd.read_csv(data_dir / "daily_counts.csv", parse_dates=["날짜"])
daily = daily.set_index("날짜").reindex(
    pd.date_range("2025-01-01", "2025-12-31")
)
daily.index.name = "날짜"

daily["요일구분"] = np.where(daily.index.dayofweek >= 5, "주말", "평일")
daily["월"] = daily.index.month
observed = daily.dropna(subset=["이용건수"])

monthly = daily.groupby("월")["이용건수"].agg(["mean", "count"])
monthly = monthly.rename(columns={"mean": "일평균이용건수", "count": "관측일수"})

weekday = observed.groupby("요일구분")["이용건수"].agg(["mean", "median", "count"])
weekday = weekday.rename(columns={
    "mean": "하루평균이용건수",
    "median": "하루중앙값",
    "count": "관측일수",
})

hourly = pd.read_csv(data_dir / "hourly_counts.csv", parse_dates=["날짜"])
hour_grid = hourly.pivot_table(
    index="날짜", columns="시간", values="이용건수", aggfunc="sum"
)
hour_grid = hour_grid.reindex(
    index=observed.index, columns=range(24)
).fillna(0)

day_type = pd.Series(
    np.where(hour_grid.index.dayofweek >= 5, "주말", "평일"),
    index=hour_grid.index,
    name="요일구분",
)
hourly_profile = hour_grid.assign(요일구분=day_type).groupby("요일구분").mean().T
hourly_profile.index.name = "시간"

monthly.to_csv(data_dir / "monthly_summary.csv", encoding="utf-8-sig")
weekday.to_csv(data_dir / "weekday_summary.csv", encoding="utf-8-sig")
hourly_profile.to_csv(data_dir / "hourly_profile.csv", encoding="utf-8-sig")

print("관측된 날짜 수:", len(observed))
print("\n월별 요약 (7월은 결측으로 표시되어야 함):")
print(monthly.round(1).to_string())
print("\n평일·주말 요약:")
print(weekday.round(1).to_string())
print("\n시간대별 하루 평균 이용건수:")
print(hourly_profile.round(1).to_string())