from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw/pancan/TCGA-PANCAN-HiSeq-801x20531")
OUTPUT_DIR = Path("data/demo/pancan_messy")

EXPRESSION_INPUT = RAW_DATA_DIR / "data.csv"
METADATA_INPUT = RAW_DATA_DIR / "labels.csv"

EXPRESSION_OUTPUT = OUTPUT_DIR / "expression_matrix.tsv"
METADATA_OUTPUT = OUTPUT_DIR / "metadata.tsv"
README_OUTPUT = OUTPUT_DIR / "README_pancan_messy_dataset.md"

GROUP_COUNT = 4
SAMPLES_PER_GROUP = 25
GENE_COUNT = 500


def rename_first_column_to_sample_id(dataframe: pd.DataFrame) -> pd.DataFrame:
    first_column = dataframe.columns[0]

    if first_column == "sample_id":
        return dataframe

    return dataframe.rename(columns={first_column: "sample_id"})


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    expression = pd.read_csv(EXPRESSION_INPUT)
    metadata = pd.read_csv(METADATA_INPUT)

    expression = rename_first_column_to_sample_id(expression)
    metadata = rename_first_column_to_sample_id(metadata)

    if "Class" not in metadata.columns:
        raise ValueError("Expected PANCAN metadata to contain a 'Class' column.")

    group_table = (
        metadata["Class"]
        .value_counts()
        .rename_axis("Class")
        .reset_index(name="sample_count")
        .sort_values(["sample_count", "Class"], ascending=[False, True])
    )

    selected_groups = group_table.head(GROUP_COUNT)["Class"].tolist()

    selected_metadata = (
        metadata[metadata["Class"].isin(selected_groups)]
        .sort_values(["Class", "sample_id"])
        .groupby("Class", group_keys=False)
        .head(SAMPLES_PER_GROUP)
        .reset_index(drop=True)
    )

    selected_sample_ids = selected_metadata["sample_id"].tolist()

    expression_subset = (
        selected_metadata[["sample_id"]]
        .merge(expression, on="sample_id", how="left")
    )

    if expression_subset.drop(columns=["sample_id"]).isna().all(axis=1).any():
        raise ValueError("At least one selected metadata sample is missing from expression data.")

    gene_columns = [column for column in expression_subset.columns if column != "sample_id"]

    numeric_expression = expression_subset[gene_columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    gene_variance = numeric_expression.var(axis=0, skipna=True)

    selected_genes = (
        gene_variance[gene_variance > 0]
        .sort_values(ascending=False)
        .head(GENE_COUNT)
        .index
        .tolist()
    )

    if len(selected_genes) < 10:
        raise ValueError("Not enough variable genes to create a PANCAN messy demo dataset.")

    expression_subset = expression_subset[["sample_id"] + selected_genes].copy()
    expression_subset[selected_genes] = expression_subset[selected_genes].astype("object")

    metadata_subset = selected_metadata[["sample_id", "Class"]].copy()

    gene_non_numeric = selected_genes[0]
    gene_low_missing = selected_genes[1]
    gene_high_missing = selected_genes[2]
    gene_constant = selected_genes[3]

    sample_count = len(expression_subset)

    low_missing_count = max(1, int(sample_count * 0.05))
    high_missing_count = int(sample_count * 0.20) + 1

    # 1. Non-numeric expression value.
    # Expected behavior: convert invalid value to missing and impute because missingness is low.
    expression_subset.loc[0, gene_non_numeric] = "bad_value"

    # 2. Low missingness gene.
    # Expected behavior: impute missing values using gene median.
    expression_subset.loc[0:low_missing_count - 1, gene_low_missing] = None

    # 3. High missingness gene.
    # Expected behavior: remove gene from analytical dataset.
    expression_subset.loc[0:high_missing_count - 1, gene_high_missing] = None

    # 4. Constant gene.
    # Expected behavior: remove constant gene.
    expression_subset[gene_constant] = "5.0"

    # 5. Metadata intentionally keeps Class instead of group.
    # Expected behavior: harmonize Class to group.

    expression_subset.to_csv(EXPRESSION_OUTPUT, sep="\t", index=False)
    metadata_subset.to_csv(METADATA_OUTPUT, sep="\t", index=False)

    README_OUTPUT.write_text(
        f"""# PANCAN Controlled Messy Analysis-Ready Dataset

This dataset is derived from the real TCGA PANCAN expression dataset.

It is a smaller demo subset intended for fast local testing and Streamlit demonstration.

## Subset design

- Selected groups: {", ".join(selected_groups)}
- Samples per group: {SAMPLES_PER_GROUP}
- Total samples: {len(expression_subset)}
- Selected genes: {len(selected_genes)}

The dataset preserves real sample identifiers, expression values and cancer class labels from the source dataset.

## Introduced issues

| Issue | Target | Expected Data Cleaner behavior |
|---|---|---|
| Non-numeric expression value | {gene_non_numeric} | Convert invalid value to missing value, then impute because missingness is low |
| Low missingness gene | {gene_low_missing} | Impute missing values using gene median |
| High missingness gene | {gene_high_missing} | Remove gene from analytical dataset |
| Constant gene | {gene_constant} | Remove gene because all expression values are identical |
| Metadata column Class instead of group | Class | Harmonize Class to group |

## Purpose

This is a controlled messy real-data demo dataset.

It is intended to demonstrate rule-based cleaning, transparent QC reporting and exploratory analysis readiness.
It is not intended to represent natural missingness patterns in TCGA PANCAN.
"""
    )

    print(f"Saved expression matrix: {EXPRESSION_OUTPUT}")
    print(f"Saved metadata: {METADATA_OUTPUT}")
    print(f"Saved README: {README_OUTPUT}")
    print(f"Expression shape: {expression_subset.shape}")
    print(f"Metadata shape: {metadata_subset.shape}")
    print(f"Selected groups: {selected_groups}")


if __name__ == "__main__":
    main()
