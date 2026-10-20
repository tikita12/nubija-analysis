"""Audit source records without deleting or changing trips."""

from pathlib import Path
import json

import numpy as np
import pandas as pd


def audit_quality(raw_path: Path, daily: pd.DataFrame, output_dir: Path) -> dict:
    """Use hashes to find candidates, then compare complete rows exactly."""
    counts = {
        "total_rows": 0,
        "invalid_departures": 0,
        "invalid_arrivals": 0,
        "arrival_before_departure": 0,
        "zero_duration": 0,
        "duration_over_24h": 0,
    }
    hashes = []
    for chunk in pd.read_csv(raw_path, encoding="cp949", dtype="string", chunksize=100_000):
        counts["total_rows"] += len(chunk)
        departure = pd.to_datetime(
            chunk["출발일"].str.strip() + " " + chunk["출발시간"].str.strip(),
            format="%Y-%m-%d %H:%M:%S", errors="coerce",
        )
        arrival = pd.to_datetime(
            chunk["도착일"].str.strip() + " " + chunk["도착시간"].str.strip(),
            format="%Y-%m-%d %H:%M:%S", errors="coerce",
        )
        duration = (arrival - departure).dt.total_seconds()
        counts["invalid_departures"] += int(departure.isna().sum())
        counts["invalid_arrivals"] += int(arrival.isna().sum())
        counts["arrival_before_departure"] += int(duration.lt(0).sum())
        counts["zero_duration"] += int(duration.eq(0).sum())
        counts["duration_over_24h"] += int(duration.gt(86400).sum())
        hashes.append(pd.util.hash_pandas_object(chunk, index=False).to_numpy())

    unique, frequencies = np.unique(np.concatenate(hashes), return_counts=True)
    repeated = unique[frequencies > 1]
    del hashes, unique, frequencies
    candidates = []
    if len(repeated):
        for chunk in pd.read_csv(raw_path, encoding="cp949", dtype="string", chunksize=100_000):
            row_hash = pd.util.hash_pandas_object(chunk, index=False)
            candidates.append(chunk.loc[row_hash.isin(repeated)])
    # Hash collisions cannot produce a duplicate verdict: verify all column values.
    duplicate_rows = pd.concat(candidates, ignore_index=True) if candidates else pd.DataFrame()
    counts["exact_duplicate_excess_rows"] = int(duplicate_rows.duplicated().sum())
    counts["exact_duplicate_all_members"] = int(duplicate_rows.duplicated(keep=False).sum())

    observed = daily.dropna(subset=["이용건수"]).copy()
    q1, q3 = observed["이용건수"].quantile([0.25, 0.75])
    lower, upper = float(q1 - 1.5 * (q3 - q1)), float(q3 + 1.5 * (q3 - q1))
    observed["이상치후보"] = (
        observed["이용건수"].lt(lower) | observed["이용건수"].gt(upper)
    )
    counts.update({
        "observed_days": len(observed),
        "daily_iqr_lower": lower,
        "daily_iqr_upper": upper,
        "daily_outlier_candidates": int(observed["이상치후보"].sum()),
        "policy": (
            "출발 시점 기준 제공 기록 수를 분석한다. 출발 시각 변환 실패는 집계에서 제외한다. "
            "중복 후보와 반납 시간 이상은 오류 원인이 확인되지 않아 자동 삭제하지 않는다. "
            "0초 및 24시간 초과는 검토 기준이며 서비스 규정에 따른 오류 판정이 아니다. "
            "일별 IQR 후보도 실제 변동일 수 있어 자동 삭제하지 않는다."
        ),
    })
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "quality_summary.json").write_text(
        json.dumps(counts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    observed.to_csv(output_dir / "daily_outlier_checks.csv", index=False, encoding="utf-8-sig")
    return counts


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    from run_analysis import find_one

    raw = find_one(root / "data", "*대여 반납 이력_20251231.csv", "2025 누비자 원본")
    processed = root / "data" / "processed"
    result = audit_quality(raw, pd.read_csv(processed / "daily_counts.csv"), processed)
    print(json.dumps(result, ensure_ascii=False, indent=2))
