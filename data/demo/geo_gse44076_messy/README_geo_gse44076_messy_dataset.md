# GSE44076 Controlled Messy Analysis-Ready Dataset

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
| Non-numeric expression value | 11715100_at | Convert invalid value to missing value, then impute because missingness is low |
| Low missingness gene | 11715101_s_at | Impute missing values using gene median |
| High missingness gene | 11715102_x_at | Remove gene from analytical dataset |
| Constant gene | 11715103_x_at | Remove gene because all expression values are identical |
| Metadata column Class instead of group | Class | Harmonize Class to group |

## Purpose

This is a controlled messy real-data validation dataset.

It is intended to demonstrate that the Data Cleaner can resolve common input problems
and produce a cleaned dataset that is ready for exploratory analysis.
