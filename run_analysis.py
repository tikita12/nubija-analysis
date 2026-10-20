"""Run the complete Nubija usage analysis and recreate its tables and figures.

Place this file in the project root (next to the data/ and images/ folders),
then run it with the project's Python environment.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


def find_one(folder: Path, pattern: str, description: str) -> Path:
    matches = sorted(folder.glob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"{description}를 하나만 찾을 수 없습니다. 검색 경로: {folder / pattern} "
            f"(검색 결과 {len(matches)}개)"
        )
    return matches[0]


def aggregate_raw_trips(raw_path: Path, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, int, int, dict[str, int], pd.Timestamp, pd.Timestamp]:
    """Read the large CP949 trip log in chunks and aggregate by date/hour."""
    daily_counts: Counter[str] = Counter()
    hourly_counts: Counter[tuple[str, str, int]] = Counter()
    missing_counts: Counter[str] = Counter()
    total_rows = 0
    valid_rows = 0
    first_departure: pd.Timestamp | None = None
    last_departure: pd.Timestamp | None = None

    required = ["출발일", "출발시간"]
    for chunk in pd.read_csv(raw_path, encoding="cp949", chunksize=100_000):
        total_rows += len(chunk)
        for column in chunk.columns:
            missing_counts[column] += int(chunk[column].isna().sum())
        absent = [column for column in required if column not in chunk.columns]
        if absent:
            raise ValueError(f"원본 CSV에 필요한 컬럼이 없습니다: {absent}")

        departure = pd.to_datetime(
            chunk["출발일"].astype("string").str.strip()
            + " "
            + chunk["출발시간"].astype("string").str.strip(),
            format="%Y-%m-%d %H:%M:%S",
            errors="coerce",
        )
        valid = departure.notna()
        valid_rows += int(valid.sum())
        if not valid.any():
            continue

        valid_departures = departure[valid]
        chunk_min = valid_departures.min()
        chunk_max = valid_departures.max()
        first_departure = chunk_min if first_departure is None else min(first_departure, chunk_min)
        last_departure = chunk_max if last_departure is None else max(last_departure, chunk_max)

        grouped = pd.DataFrame(
            {
                "date": valid_departures.dt.strftime("%Y-%m-%d"),
                "day_type": np.where(valid_departures.dt.dayofweek >= 5, "주말", "평일"),
                "hour": valid_departures.dt.hour,
            }
        )
        daily_counts.update(grouped.groupby("date").size().to_dict())
        hourly_counts.update(grouped.groupby(["date", "day_type", "hour"]).size().to_dict())

    if first_departure is None or last_departure is None:
        raise ValueError("읽을 수 있는 출발 날짜·시간 기록이 없습니다.")

    date_index = pd.date_range("2025-01-01", "2025-12-31", freq="D", name="날짜")
    daily_series = pd.Series(daily_counts, dtype="int64", name="이용건수")
    daily_series.index = pd.to_datetime(daily_series.index)
    # Keep dates without source records as NaN. In particular, missing July is not zero.
    daily_series = daily_series.reindex(date_index)
    daily_df = daily_series.rename_axis("날짜").reset_index()

    observed_dates = daily_series.dropna().index
    hourly_rows = []
    for date in observed_dates:
        day_type = "주말" if date.dayofweek >= 5 else "평일"
        date_text = date.strftime("%Y-%m-%d")
        for hour in range(24):
            hourly_rows.append(
                {
                    "날짜": date,
                    "요일구분": day_type,
                    "시간": hour,
                    "이용건수": int(hourly_counts.get((date_text, day_type, hour), 0)),
                }
            )
    hourly_df = pd.DataFrame(hourly_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    daily_df.to_csv(output_dir / "daily_counts.csv", index=False, encoding="utf-8-sig")
    hourly_df.to_csv(output_dir / "hourly_counts.csv", index=False, encoding="utf-8-sig")
    return daily_df, hourly_df, total_rows, valid_rows, dict(missing_counts), first_departure, last_departure


def summarize_2025(daily_df: pd.DataFrame, hourly_df: pd.DataFrame, output_dir: Path):
    daily = daily_df.copy()
    daily["날짜"] = pd.to_datetime(daily["날짜"])
    daily = daily.set_index("날짜").reindex(pd.date_range("2025-01-01", "2025-12-31", freq="D"))
    daily.index.name = "날짜"
    daily["요일구분"] = np.where(daily.index.dayofweek >= 5, "주말", "평일")
    daily["월"] = daily.index.month
    observed = daily.dropna(subset=["이용건수"])

    monthly = daily.groupby("월")["이용건수"].agg(["mean", "count"])
    monthly = monthly.rename(columns={"mean": "일평균이용건수", "count": "관측일수"})
    weekday = observed.groupby("요일구분")["이용건수"].agg(["mean", "median", "count"])
    weekday = weekday.rename(
        columns={"mean": "하루평균이용건수", "median": "하루중앙값", "count": "관측일수"}
    )

    hourly_grid = hourly_df.pivot_table(
        index="날짜", columns="시간", values="이용건수", aggfunc="sum"
    ).reindex(index=observed.index, columns=range(24), fill_value=0)
    day_type = pd.Series(
        np.where(hourly_grid.index.dayofweek >= 5, "주말", "평일"),
        index=hourly_grid.index,
        name="요일구분",
    )
    hourly_profile = hourly_grid.assign(요일구분=day_type).groupby("요일구분").mean().T
    hourly_profile.index.name = "시간"

    monthly.to_csv(output_dir / "monthly_summary.csv", encoding="utf-8-sig")
    weekday.to_csv(output_dir / "weekday_summary.csv", encoding="utf-8-sig")
    hourly_profile.to_csv(output_dir / "hourly_profile.csv", encoding="utf-8-sig")
    return daily, observed, monthly, weekday, hourly_profile


def analyze_holidays(daily: pd.DataFrame, holiday_path: Path, output_dir: Path, image_dir: Path):
    holidays = pd.read_csv(holiday_path, encoding="utf-8-sig")
    if not {"date", "name"}.issubset(holidays.columns):
        raise ValueError("공휴일 CSV에는 date,name 컬럼이 필요합니다.")
    holidays["date"] = pd.to_datetime(holidays["date"], errors="coerce")
    holidays = holidays.dropna(subset=["date"]).drop_duplicates(subset=["date"])

    comparison = daily.reset_index().rename(columns={"index": "date", "날짜": "date"})
    comparison = comparison.merge(holidays[["date", "name"]], on="date", how="left")
    comparison = comparison.rename(columns={"name": "holiday_name", "이용건수": "trips"})
    comparison["is_holiday"] = comparison["holiday_name"].notna()
    comparison["weekday"] = comparison["date"].dt.weekday
    conditions = [
        comparison["is_holiday"] & comparison["weekday"].lt(5),
        comparison["is_holiday"] & comparison["weekday"].ge(5),
        ~comparison["is_holiday"] & comparison["weekday"].ge(5),
    ]
    comparison["구분"] = np.select(
        conditions,
        ["공휴일(평일)", "공휴일(주말)", "일반 주말"],
        default="일반 평일",
    )
    order = ["일반 평일", "공휴일(평일)", "일반 주말", "공휴일(주말)"]
    summary = (
        comparison.dropna(subset=["trips"])
        .groupby("구분")["trips"]
        .agg(["mean", "median", "count"])
        .reindex(order)
        .rename(
            columns={"mean": "하루평균이용건수", "median": "하루중앙값", "count": "관측일수"}
        )
    )
    summary.to_csv(output_dir / "holiday_summary.csv", encoding="utf-8-sig")
    comparison.loc[comparison["is_holiday"] & comparison["trips"].notna(), [
        "date", "holiday_name", "trips"
    ]].sort_values("date").to_csv(
        output_dir / "holiday_daily_counts.csv", index=False, encoding="utf-8-sig"
    )

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
    ax.set_ylim(0, plot_data["하루평균이용건수"].max() * 1.18)
    ax.set_title("공휴일과 일반일의 누비자 하루 평균 이용량 (2025)")
    ax.set_ylabel("하루 평균 대여 건수")
    ax.set_xlabel("날짜 구분")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(image_dir / "04_holiday_comparison.png", dpi=150)
    plt.close(fig)
    return summary


def analyze_history(daily: pd.DataFrame, history_path: Path, output_dir: Path, image_dir: Path):
    history = pd.read_csv(history_path, encoding="cp949")
    history = history.iloc[:, :2].copy()
    history.columns = ["date", "trips"]
    history["date"] = pd.to_datetime(history["date"], errors="coerce")
    history["trips"] = pd.to_numeric(history["trips"], errors="coerce")
    history = history.dropna(subset=["date", "trips"]).sort_values("date")

    monthly_2025 = (
        daily["이용건수"]
        .resample("MS")
        .sum(min_count=1)
        .reindex(pd.date_range("2025-01-01", "2025-12-01", freq="MS"))
    )
    history_output = history.assign(period="과거 월별 자료")
    current_output = (
        monthly_2025.rename_axis("date")
        .reset_index(name="trips")
        .assign(period="2025년 일별 자료에서 집계")
    )
    pd.concat([history_output, current_output], ignore_index=True).to_csv(
        output_dir / "long_term_monthly_comparison.csv",
        index=False,
        encoding="utf-8-sig",
    )

    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(
        history["date"], history["trips"], color="#4C78A8", linewidth=1.5,
        label="과거 월별 자료 (2008.10–2023.03)",
    )
    ax.plot(
        monthly_2025.index, monthly_2025.values, color="#F58518", marker="o",
        linewidth=1.8, label="2025년 자료",
    )
    ax.set_title("누비자 월별 이용량 장기 추이")
    ax.set_xlabel("연월")
    ax.set_ylabel("월 이용 건수")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.text(
        0.5, 0.01,
        "자료 공백: 2023년 4월–2024년 12월, 2025년 7월은 기록 없음",
        ha="center", color="dimgray",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(image_dir / "05_long_term_monthly.png", dpi=150)
    plt.close(fig)

    history["year"] = history["date"].dt.year
    annual = history.groupby("year").agg(
        연간이용건수=("trips", "sum"), 관측월수=("trips", "count")
    )
    complete_years = annual[annual["관측월수"] == 12]
    return history, monthly_2025, complete_years


def make_2025_plots(daily: pd.DataFrame, monthly: pd.DataFrame, hourly_profile: pd.DataFrame, image_dir: Path):
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False

    daily["7일 이동평균"] = daily["이용건수"].rolling(window=7, min_periods=7).mean()
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

    fig, ax = plt.subplots(figsize=(10, 5))
    valid_months = monthly["일평균이용건수"].dropna()
    ax.bar(valid_months.index, valid_months.values, color="#4C78A8")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([f"{month}월" for month in range(1, 13)])
    ax.set_title("월별 하루 평균 누비자 이용량 (2025)")
    ax.set_ylabel("하루 평균 대여 건수")
    if 7 not in valid_months.index:
        ax.text(7, valid_months.max() * 0.05, "자료 없음", ha="center", color="red")
    fig.tight_layout()
    fig.savefig(image_dir / "02_monthly_average.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(hourly_profile.index, hourly_profile["평일"], marker="o", label="평일")
    ax.plot(hourly_profile.index, hourly_profile["주말"], marker="o", label="주말")
    ax.set_xticks(range(0, 24, 2))
    ax.set_title("평일·주말 시간대별 하루 평균 누비자 이용량 (2025)")
    ax.set_xlabel("출발 시간")
    ax.set_ylabel("시간대별 하루 평균 대여 건수")
    ax.legend()
    fig.tight_layout()
    fig.savefig(image_dir / "03_hourly_profile.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="누비자 전체 이용량 분석을 실행합니다.")
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="data와 images 폴더가 있는 프로젝트 경로 (기본값: 이 파일이 있는 폴더)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="결과 저장 위치 (생략하면 프로젝트 폴더에 저장)",
    )
    args = parser.parse_args()
    project_dir = args.project_dir.resolve()
    data_dir = project_dir / "data"
    output_root = args.output_dir.resolve() if args.output_dir else project_dir
    output_dir = output_root / "data" / "processed"
    image_dir = output_root / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    raw_path = find_one(data_dir, "*대여 반납 이력_20251231.csv", "2025 누비자 원본 파일")
    history_path = find_one(data_dir, "*누비자*이용현황*20230331.csv", "과거 월별 자료")
    holiday_path = data_dir / "reference" / "holidays_2025.csv"
    if not holiday_path.exists():
        raise FileNotFoundError(f"공휴일 파일이 없습니다: {holiday_path}")

    daily_df, hourly_df, rows, valid, missing, first_date, last_date = aggregate_raw_trips(
        raw_path, output_dir
    )
    daily, observed, monthly, weekday, hourly_profile = summarize_2025(
        daily_df, hourly_df, output_dir
    )
    holiday_summary = analyze_holidays(daily, holiday_path, output_dir, image_dir)
    history, monthly_2025, complete_years = analyze_history(
        daily, history_path, output_dir, image_dir
    )
    make_2025_plots(daily, monthly, hourly_profile, image_dir)

    print("원본 파일:", raw_path)
    print("전체 원본 행 수:", rows)
    print("유효한 출발 날짜·시간 기록:", valid)
    print("컬럼별 빈 값 수:", missing)
    print("출발 기록 기간:", first_date, "~", last_date)
    print("관측된 날짜 수:", len(observed))
    print("2025년 기록이 없는 날짜 수:", int(daily["이용건수"].isna().sum()))
    print("2025년 관측 월 수:", int(monthly_2025.notna().sum()))
    print("2025년 관측 월 이용량 합계:", int(monthly_2025.sum()))
    print("완전한 연도 중 이용량이 가장 많은 해:")
    print(complete_years["연간이용건수"].idxmax(), int(complete_years["연간이용건수"].max()))
    print("\n월별 요약:")
    print(monthly.round(1).to_string())
    print("\n평일·주말 요약:")
    print(weekday.round(1).to_string())
    print("\n공휴일 및 일반일 요약:")
    print(holiday_summary.round(1).to_string())
    print("\n처리 결과:", output_dir)
    print("그래프:", image_dir)


if __name__ == "__main__":
    main()
