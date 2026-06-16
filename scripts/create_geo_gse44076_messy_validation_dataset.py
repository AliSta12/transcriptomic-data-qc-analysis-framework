from pathlib import Path

import pandas as pd


INPUT_DIR = Path("data/processed/geo_gse44076")
OUTPUT_DIR = Path("data/processed/geo_gse44076_messy")

EXPRESSION_INPUT = INPUT_DIR / "expression_matrix.tsv"
METADATA_INPUT = INPUT_DIR / "metadata.tsv"

EXPRESSION_OUTPUT = OUTPUT_DIR / "expression_matrix.tsv"
METADATA_OUTPUT = OUTPUT_DIR / "metadata.tsv"
README_OUTPUT = OUTPUT_DIR / "README_messy_dataset.md"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    expression = pd.read_csv(EXPRESSION_INPUT, sep="\t", dtype=str)
    metadata = pd.read_csv(METADATA_INPUT, sep="\t", dtype=str)

    gene_columns = [column for column in expression.columns if column != "sample_id"]

    if len(expression) < 20:
        raise ValueError("This script expects at least 20 samples.")

    if len(gene_columns) < 10:
        raise ValueError("This script expects at least 10 genes.")

    gene_non_numeric = gene_columns[0]
    gene_5_percent_missing = gene_columns[1]
    gene_20_percent_missing = gene_columns[2]
    gene_above_20_percent_missing = gene_columns[3]
    sample_high_missing = expression.loc[0, "sample_id"]

    # 1. Non-numeric expression value.
    expression.loc[0, gene_non_numeric] = "bad_value"

    # 2. Exactly 5% missing: 12 / 246 = 4.88%, below/equal low threshold.
    # The project rule is <= 5%, and with 246 samples an exact 5% count is not possible.
    expression.loc[0:11, gene_5_percent_missing] = None

    # 3. Approximately 20% missing: 49 / 246 = 19.92%, below/equal high threshold.
    # The project rule is <= 20%, and with 246 samples an exact 20% count is not possible.
    expression.loc[0:48, gene_20_percent_missing] = None

    # 4. Above 20% missing: 50 / 246 = 20.33%.
    expression.loc[0:49, gene_above_20_percent_missing] = None

    # 5. One sample with >20% missing values across genes.
    high_missing_gene_subset = gene_columns[10:421]
    expression.loc[
        expression["sample_id"] == sample_high_missing,
        high_missing_gene_subset,
    ] = None

    # 6. Duplicate gene column.
    expression[f"{gene_columns[4]}_temporary_duplicate"] = expression[gene_columns[4]]
    expression = expression.rename(
        columns={f"{gene_columns[4]}_temporary_duplicate": gene_columns[4]}
    )

    # 7. Duplicate sample row.
    duplicate_sample_row = expression.iloc[[1]].copy()
    expression = pd.concat([expression, duplicate_sample_row], ignore_index=True)

    # 8. Expression sample without metadata.
    expression_only_row = expression.iloc[[2]].copy()
    expression_only_row.loc[:, "sample_id"] = "GSE44076_EXPRESSION_ONLY_SAMPLE"
    expression = pd.concat([expression, expression_only_row], ignore_index=True)

    # 9. Extra metadata sample without expression.
    extra_metadata = metadata.iloc[[0]].copy()
    extra_metadata.loc[:, "sample_id"] = "GSE44076_METADATA_ONLY_SAMPLE"
    metadata = pd.concat([metadata, extra_metadata], ignore_index=True)

    # 10. Class instead of group, to validate metadata harmonization.
    metadata = metadata.rename(columns={"group": "Class"})

    expression.to_csv(EXPRESSION_OUTPUT, sep="\t", index=False)
    metadata.to_csv(METADATA_OUTPUT, sep="\t", index=False)

    README_OUTPUT.write_text(
        f"""# GSE44076 Controlled Messy Validation Dataset

This dataset is derived from the real GEO dataset GSE44076.

It preserves the real sample identifiers, expression values and three biological groups:

- Mucosa
- Normal
- Tumor

The dataset was intentionally modified to validate the Rule-Based Transcriptomic Data Cleaner.

## Introduced issues

| Issue | Target | Expected Data Cleaner behavior |
|---|---|---|
| Non-numeric expression value | {gene_non_numeric} | Convert invalid value to missing value and log WARNING |
| Low missingness gene | {gene_5_percent_missing} | Impute missing values using gene median |
| Moderate missingness gene | {gene_20_percent_missing} | Keep gene unchanged with WARNING |
| High missingness gene | {gene_above_20_percent_missing} | Remove gene from analytical dataset |
| High missingness sample | {sample_high_missing} | Retain sample and mark REQUIRES REVIEW |
| Duplicate gene | {gene_columns[4]} | Aggregate duplicate gene columns using mean |
| Duplicate sample | {duplicate_sample_row.iloc[0]["sample_id"]} | Retain duplicated sample and mark REQUIRES REVIEW |
| Expression sample without metadata | GSE44076_EXPRESSION_ONLY_SAMPLE | Mark metadata consistency as REQUIRES REVIEW |
| Metadata sample without expression | GSE44076_METADATA_ONLY_SAMPLE | Report metadata consistency WARNING |
| Metadata column Class instead of group | Class | Harmonize Class to group |

## Purpose

This is a controlled messy real-data validation dataset.

It is not intended to represent natural missingness in GEO.
It is intended to demonstrate that the Data Cleaner detects, cleans and reports common real-world input problems using transparent rules.
"""
    )

    print(f"Saved messy expression matrix: {EXPRESSION_OUTPUT}")
    print(f"Saved messy metadata: {METADATA_OUTPUT}")
    print(f"Saved messy dataset README: {README_OUTPUT}")
    print(f"Messy expression shape: {expression.shape}")
    print(f"Messy metadata shape: {metadata.shape}")


if __name__ == "__main__":
    main()
