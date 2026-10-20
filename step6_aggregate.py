from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

project_dir = Path(__file__).resolve().parent
file_path = Path(input("CSV 파일의 전체 경로를 붙여 넣으세요: ").strip().strip('"'))
output_dir = project_dir / "data" / "processed"
output_dir.mkdir(parents=True, exist_ok=True)

daily_counts = Counter()
hourly_counts = Counter()
total_rows = 0

for chunk in pd.read_csv(file_path, encoding="cp949", chunksize=100_000):
    departure = pd.to_datetime(
        chunk["출발일"].astype("string").str.strip()
        + " "
        + chunk["출발시간"].astype("string").str.strip(),
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )

    valid = departure.notna()
    total_rows += int(valid.sum())

    data = pd.DataFrame({
        "날짜": departure[valid].dt.strftime("%Y-%m-%d"),
        "요일구분": np.where(
            departure[valid].dt.dayofweek >= 5, "주말", "평일"
        ),
        "시간": departure[valid].dt.hour,
    })

    daily_counts.update(data.groupby("날짜").size().to_dict())
    hourly_counts.update(
        data.groupby(["날짜", "요일구분", "시간"]).size().to_dict()
    )

expected_dates = set(
    pd.date_range("2025-01-01", "2025-12-31").strftime("%Y-%m-%d")
)
missing_dates = sorted(expected_dates - set(daily_counts))

if not missing_dates:
    for date in daily_counts:
        day_type = "주말" if pd.Timestamp(date).dayofweek >= 5 else "평일"
        for hour in range(24):
            hourly_counts.setdefault((date, day_type, hour), 0)

daily_df = pd.DataFrame(
    sorted(daily_counts.items()),
    columns=["날짜", "이용건수"],
)

hourly_df = pd.DataFrame(
    [
        (date, day_type, hour, count)
        for (date, day_type, hour), count in sorted(hourly_counts.items())
    ],
    columns=["날짜", "요일구분", "시간", "이용건수"],
)

daily_df.to_csv(output_dir / "daily_counts.csv", index=False, encoding="utf-8-sig")
hourly_df.to_csv(output_dir / "hourly_counts.csv", index=False, encoding="utf-8-sig")

print("처리한 출발 기록:", total_rows)
print("날짜별 데이터 행 수:", len(daily_df))
print("2025년에 기록이 없는 날짜:", missing_dates)
print("일별 파일:", output_dir / "daily_counts.csv")
print("시간대별 파일:", output_dir / "hourly_counts.csv")