from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

project_dir = Path(__file__).resolve().parent
data_dir = project_dir / "data" / "processed"
image_dir = project_dir / "images"
image_dir.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# 그래프 1: 일별 이용량과 7일 이동평균
daily = pd.read_csv(data_dir / "daily_counts.csv", parse_dates=["날짜"])
daily = daily.set_index("날짜").reindex(
    pd.date_range("2025-01-01", "2025-12-31")
)
daily.index.name = "날짜"
daily["7일 이동평균"] = daily["이용건수"].rolling(
    window=7, min_periods=7
).mean()

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(daily.index, daily["이용건수"], alpha=0.35, label="일별 이용건수")
ax.plot(daily.index, daily["7일 이동평균"], linewidth=2, label="7일 이동평균")
ax.set_title("누비자 일별 이용량 추이 (2025)")
ax.set_ylabel("대여 건수")
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m월"))
ax.set_xlim(pd.Timestamp("2025-01-01"), pd.Timestamp("2025-12-31"))
ax.legend()
fig.tight_layout()
fig.savefig(image_dir / "01_daily_trend.png", dpi=160)
plt.close(fig)

# 그래프 2: 월별 일평균 이용량
monthly = pd.read_csv(data_dir / "monthly_summary.csv", index_col=0)
monthly.index = monthly.index.astype(int)

fig, ax = plt.subplots(figsize=(10, 5))
valid_months = monthly["일평균이용건수"].dropna()
ax.bar(valid_months.index, valid_months.values, color="#4C78A8")
ax.set_xticks(range(1, 13))
ax.set_xticklabels([f"{m}월" for m in range(1, 13)])
ax.set_title("월별 하루 평균 누비자 이용량 (2025)")
ax.set_ylabel("하루 평균 대여 건수")
ax.text(7, valid_months.max() * 0.05, "자료 없음", ha="center", color="red")
fig.tight_layout()
fig.savefig(image_dir / "02_monthly_average.png", dpi=160)
plt.close(fig)

# 그래프 3: 평일·주말 시간대별 하루 평균
hourly = pd.read_csv(data_dir / "hourly_profile.csv", index_col=0)
hourly.index = hourly.index.astype(int)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(hourly.index, hourly["평일"], marker="o", label="평일")
ax.plot(hourly.index, hourly["주말"], marker="o", label="주말")
ax.set_xticks(range(0, 24, 2))
ax.set_title("평일·주말 시간대별 하루 평균 누비자 이용량 (2025)")
ax.set_xlabel("출발 시간")
ax.set_ylabel("시간대별 하루 평균 대여 건수")
ax.legend()
fig.tight_layout()
fig.savefig(image_dir / "03_hourly_profile.png", dpi=160)
plt.close(fig)

print("그래프 저장 위치:", image_dir)
print("생성 파일:")
for image_file in sorted(image_dir.glob("*.png")):
    print(image_file.name)