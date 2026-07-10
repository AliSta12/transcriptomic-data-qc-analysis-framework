# PANCAN Controlled Messy Analysis-Ready Dataset

This dataset is derived from the real TCGA PANCAN expression dataset.

It is a smaller demo subset intended for fast local testing and Streamlit demonstration.

## Subset design

- Selected groups: BRCA, KIRC, LUAD, PRAD
- Samples per group: 25
- Total samples: 100
- Selected genes: 500

The dataset preserves real sample identifiers, expression values and cancer class labels from the source dataset.

## Introduced issues

| Issue | Target | Expected Data Cleaner behavior |
|---|---|---|
| Non-numeric expression value | gene_9176 | Convert invalid value to missing value, then impute because missingness is low |
| Low missingness gene | gene_9175 | Impute missing values using gene median |
| High missingness gene | gene_15898 | Remove gene from analytical dataset |
| Constant gene | gene_15301 | Remove gene because all expression values are identical |
| Metadata column Class instead of group | Class | Harmonize Class to group |

## Purpose

This is a controlled messy real-data demo dataset.

It is intended to demonstrate rule-based cleaning, transparent QC reporting and exploratory analysis readiness.
It is not intended to represent natural missingness patterns in TCGA PANCAN.
