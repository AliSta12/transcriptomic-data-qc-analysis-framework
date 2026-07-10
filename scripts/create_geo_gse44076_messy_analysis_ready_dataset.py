from pathlib import Path

import pandas as pd


INPUT_DIR = Path("data/processed/geo_gse44076")
OUTPUT_DIR = Path("data/demo/geo_gse44076_messy")

EXPRESSION_INPUT = INPUT_DIR / "expression_matrix.tsv"
METADATA_INPUT = INPUT_DIR / "metadata.tsv"

EXPRESSION_OUTPUT = OUTPUT_DIR / "expression_matrix.tsv"
METADATA_OUTPUT = OUTPUT_DIR / "metadata.tsv"
README_OUTPUT = OUTPUT_DIR / "README_geo_gse44076_messy_dataset.md"


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
    gene_low_missing = gene_columns[1]
    gene_high_missing = gene_columns[2]
    gene_constant = gene_columns[3]

    # 1. Non-numeric expression value.
    # This should be converted to missing and then imputed because missingness is <=5%.
    expression.loc[0, gene_non_numeric] = "bad_value"

    # 2. Low missingness gene: 12 / 246 = 4.88%.
    # Expected behavior: impute using gene median.
    expression.loc[0:11, gene_low_missing] = None

    # 3. High missingness gene: 50 / 246 = 20.33%.
    # Expected behavior: remove gene from analytical dataset.
    expression.loc[0:49, gene_high_missing] = None

    # 4. Constant gene.
    # Expected behavior: remove constant gene.
    expression[gene_constant] = "5.0"

    # 5. Class instead of group, to validate metadata harmonization.
    metadata = metadata.rename(columns={"group": "Class"})

    expression.to_csv(EXPRESSION_OUTPUT, sep="\t", index=False)
    metadata.to_csv(METADATA_OUTPUT, sep="\t", index=False)

    README_OUTPUT.write_text(
        f"""# GSE44076 Controlled Messy Analysis-Ready Dataset

This dataset is derived from the real GEO dataset GSE44076.

It preserves the real sample identifiers, expression values and three biological groups:

- Mucosa
- Normal
- Tumor

This variant intentionally contains only issues that the Data Cleaner should resolve automatically,
so the cleaned output can proceed to the Analysis Engine.

## Introduced issues

| Issue | Target | Expected Data Cleaner behavior |
|---|---|---|
| Non-numeric expression value | {gene_non_numeric} | Convert invalid value to missing value, then impute because missingness is low |
| Low missingness gene | {gene_low_missing} | Impute missing values using gene median |
| High missingness gene | {gene_high_missing} | Remove gene from analytical dataset |
| Constant gene | {gene_constant} | Remove gene because all expression values are identical |
| Metadata column Class instead of group | Class | Harmonize Class to group |

## Purpose

This is a controlled messy real-data validation dataset.

It is intended to demonstrate that the Data Cleaner can resolve common input problems
and produce a cleaned dataset that is ready for exploratory analysis.
"""
    )

    print(f"Saved expression matrix: {EXPRESSION_OUTPUT}")
    print(f"Saved metadata: {METADATA_OUTPUT}")
    print(f"Saved README: {README_OUTPUT}")
    print(f"Expression shape: {expression.shape}")
    print(f"Metadata shape: {metadata.shape}")
    print("Metadata columns:")
    print(metadata.columns.tolist())


if __name__ == "__main__":
    main()
