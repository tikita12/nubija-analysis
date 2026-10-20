import pandas as pd
from pathlib import Path

file_path = Path(input("CSV 파일의 전체 경로를 붙여 넣으세요: ").strip().strip('"'))

print("파일 존재:", file_path.exists())
print("파일 크기:", file_path.stat().st_size, "바이트")

for encoding in ("utf-8-sig", "cp949"):
    try:
        sample = pd.read_csv(file_path, nrows=5, encoding=encoding)
        print("문자 인코딩:", encoding)
        break
    except UnicodeDecodeError:
        continue
else:
    raise ValueError("CSV 인코딩을 확인하지 못했습니다.")

print("\n컬럼 이름:")
print(sample.columns.tolist())

print("\n첫 5개 기록:")
print(sample.to_string(index=False))

row_count = 0
for chunk in pd.read_csv(
    file_path,
    encoding=encoding,
    chunksize=100_000
):
    row_count += len(chunk)

print("\n전체 기록 수:", row_count)