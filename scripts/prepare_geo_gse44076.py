from pathlib import Path
import gzip
from io import StringIO
import re

import pandas as pd


RAW_PATH = Path("data/raw/geo_gse44076/GSE44076_series_matrix.txt.gz")
OUTPUT_DIR = Path("data/processed/geo_gse44076")
EXPRESSION_OUTPUT = OUTPUT_DIR / "expression_matrix.tsv"
METADATA_OUTPUT = OUTPUT_DIR / "metadata.tsv"


def _clean_geo_value(value: str) -> str:
    return value.strip().strip('"')


def _extract_sample_row(lines: list[str], prefix: str) -> list[str]:
    for line in lines:
        if line.startswith(prefix):
            parts = line.rstrip("\n").split("\t")
            return [_clean_geo_value(value) for value in parts[1:]]
    raise ValueError(f"Missing GEO metadata row: {prefix}")


def _extract_characteristic(lines: list[str], key: str) -> list[str]:
    key_prefix = f"{key}:"
    for line in lines:
        if line.startswith("!Sample_characteristics_ch1"):
            parts = [_clean_geo_value(value) for value in line.rstrip("\n").split("\t")[1:]]
            if parts and parts[0].lower().startswith(key_prefix.lower()):
                return [value.split(":", 1)[1].strip() for value in parts]
    raise ValueError(f"Missing GEO characteristic: {key}")


def _standardize_sample_id(value: str) -> str:
    value = value.strip().strip('"')
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value.strip("_")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    metadata_lines = []
    expression_rows = []
    inside_table = False

    with gzip.open(RAW_PATH, "rt", errors="replace") as handle:
        for line in handle:
            if line.startswith("!series_matrix_table_begin"):
                inside_table = True
                continue

            if line.startswith("!series_matrix_table_end"):
                break

            if inside_table:
                expression_rows.append(line)
            else:
                metadata_lines.append(line)

    if not expression_rows:
        raise ValueError("No expression table found in GEO series matrix.")

    expression_table = pd.read_csv(StringIO("".join(expression_rows)), sep="\t", dtype=str)

    geo_sample_ids = expression_table.columns[1:].tolist()
    sample_ids = [_standardize_sample_id(sample_id) for sample_id in geo_sample_ids]

    sample_type = _extract_characteristic(metadata_lines, "sample type")
    individual_id = _extract_characteristic(metadata_lines, "individual id")
    stage = _extract_characteristic(metadata_lines, "Stage")
    location = _extract_characteristic(metadata_lines, "location")
    gender = _extract_characteristic(metadata_lines, "gender")
    age = _extract_characteristic(metadata_lines, "age")

    if len(sample_ids) != len(sample_type):
        raise ValueError("Sample count mismatch between expression table and metadata.")

    metadata = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "group": sample_type,
            "dataset": "GSE44076",
            "stage": stage,
            "location": location,
            "gender": gender,
            "age": age,
            "individual_id": individual_id,
        }
    )

    expression_table = expression_table.rename(columns={"ID_REF": "gene"})
    expression_table = expression_table.rename(
        columns=dict(zip(geo_sample_ids, sample_ids))
    )

    # Keep a manageable real-data subset for validation and demo.
    # This preserves all samples and groups, but limits the number of genes.
    expression_table = expression_table.head(2000)

    expression_matrix = expression_table.set_index("gene").T.reset_index()
    expression_matrix = expression_matrix.rename(columns={"index": "sample_id"})

    expression_matrix.to_csv(EXPRESSION_OUTPUT, sep="\t", index=False)
    metadata.to_csv(METADATA_OUTPUT, sep="\t", index=False)

    print(f"Saved expression matrix: {EXPRESSION_OUTPUT}")
    print(f"Saved metadata: {METADATA_OUTPUT}")
    print(f"Expression shape: {expression_matrix.shape}")
    print(f"Metadata shape: {metadata.shape}")
    print("Group counts:")
    print(metadata["group"].value_counts())


if __name__ == "__main__":
    main()
