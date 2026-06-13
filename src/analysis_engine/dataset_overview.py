from dataclasses import dataclass

import pandas as pd


@dataclass
class DatasetOverviewResult:
    sample_count: int
    gene_count: int
    group_count: int
    group_distribution: dict
    min_expression: float
    max_expression: float
    mean_expression: float
    median_expression: float
    summary_dataframe: pd.DataFrame


class DatasetOverview:
    """
    Generates a basic overview of a cleaned transcriptomic dataset.

    This module expects:
    - expression matrix in sample x gene format
    - first column named sample_id
    - metadata table containing sample_id and group columns
    """

    def generate(
        self,
        expression_df: pd.DataFrame,
        metadata_df: pd.DataFrame,
    ) -> DatasetOverviewResult:
        self._validate_inputs(expression_df, metadata_df)

        gene_columns = [col for col in expression_df.columns if col != "sample_id"]
        expression_values = expression_df[gene_columns]

        sample_count = len(expression_df)
        gene_count = len(gene_columns)
        group_distribution = metadata_df["group"].value_counts().to_dict()
        group_count = len(group_distribution)

        min_expression = float(expression_values.min().min())
        max_expression = float(expression_values.max().max())
        mean_expression = float(expression_values.mean().mean())
        median_expression = float(expression_values.median().median())

        summary_dataframe = pd.DataFrame(
            [
                {
                    "metric": "sample_count",
                    "value": int(sample_count),
                },
                {
                    "metric": "gene_count",
                    "value": int(gene_count),
                },
                {
                    "metric": "group_count",
                    "value": int(group_count),
                },
                {
                    "metric": "min_expression",
                    "value": round(min_expression, 2),
                },
                {
                    "metric": "max_expression",
                    "value": round(max_expression, 2),
                },
                {
                    "metric": "mean_expression",
                    "value": round(mean_expression, 2),
                },
                {
                    "metric": "median_expression",
                    "value": round(median_expression, 2),
                },
            ]
        )

        return DatasetOverviewResult(
            sample_count=sample_count,
            gene_count=gene_count,
            group_count=group_count,
            group_distribution=group_distribution,
            min_expression=min_expression,
            max_expression=max_expression,
            mean_expression=mean_expression,
            median_expression=median_expression,
            summary_dataframe=summary_dataframe,
        )

    def _validate_inputs(
        self,
        expression_df: pd.DataFrame,
        metadata_df: pd.DataFrame,
    ) -> None:
        if "sample_id" not in expression_df.columns:
            raise ValueError("Expression dataframe must contain 'sample_id' column.")

        if "sample_id" not in metadata_df.columns:
            raise ValueError("Metadata dataframe must contain 'sample_id' column.")

        if "group" not in metadata_df.columns:
            raise ValueError("Metadata dataframe must contain 'group' column.")

        gene_columns = [col for col in expression_df.columns if col != "sample_id"]

        if not gene_columns:
            raise ValueError("Expression dataframe must contain at least one gene column.")
