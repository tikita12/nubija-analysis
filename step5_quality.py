from collections import Counter
from pathlib import Path

import pandas as pd

file_path = Path(input("CSV 파일의 전체 경로를 붙여 넣으세요: ").strip().strip('"'))

missing_counts = Counter()
total_rows = 0
invalid_departures = 0
valid_departures = 0
first_departure = None
last_departure = None

for chunk in pd.read_csv(file_path, encoding="cp949", chunksize=100_000):
    total_rows += len(chunk)
    missing_counts.update(chunk.isna().sum().to_dict())

    departure = pd.to_datetime(
        chunk["출발일"].astype("string").str.strip()
        + " "
        + chunk["출발시간"].astype("string").str.strip(),
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )

    valid = departure.dropna()
    invalid_departures += int(departure.isna().sum())
    valid_departures += len(valid)

    if not valid.empty:
        chunk_first = valid.min()
        chunk_last = valid.max()
        first_departure = (
            chunk_first if first_departure is None else min(first_departure, chunk_first)
        )
        last_departure = (
            chunk_last if last_departure is None else max(last_departure, chunk_last)
        )

print("전체 기록 수:", total_rows)
print("컬럼별 빈 값 수:", dict(missing_counts))
print("유효한 출발 날짜·시간 기록:", valid_departures)
print("읽을 수 없는 출발 날짜·시간 기록:", invalid_departures)
print("출발 기록 기간:", first_departure, "~", last_departure)