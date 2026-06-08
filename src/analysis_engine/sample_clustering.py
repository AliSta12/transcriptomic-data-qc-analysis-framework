from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage


@dataclass
class SampleClusteringResult:
    linkage_matrix: list
    plot_path: str
    summary_dataframe: pd.DataFrame


class SampleClustering:
    """
    Performs hierarchical clustering of samples and generates a dendrogram.

    This module expects:
    - expression matrix in sample x gene format
    - first column named sample_id
    """

    def generate(
        self,
        expression_df: pd.DataFrame,
        output_directory: str,
    ) -> SampleClusteringResult:

        self._validate_inputs(expression_df)

        gene_columns = [
            column
            for column in expression_df.columns
            if column != "sample_id"
        ]

        expression_values = expression_df[gene_columns]

        linkage_matrix = linkage(
            expression_values,
            method="ward",
        )

        output_dir = Path(output_directory)
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        plot_path = output_dir / "sample_clustering_dendrogram.png"

        plt.figure(figsize=(10, 6))

        dendrogram(
            linkage_matrix,
            labels=expression_df["sample_id"].tolist(),
            leaf_rotation=90,
        )

        plt.title("Sample Clustering Dendrogram")
        plt.xlabel("Sample ID")
        plt.ylabel("Distance")
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()

        summary_dataframe = pd.DataFrame(
            [
                {
                    "metric": "sample_count",
                    "value": len(expression_df),
                },
                {
                    "metric": "gene_count",
                    "value": len(gene_columns),
                },
                {
                    "metric": "clustering_method",
                    "value": "ward",
                },
            ]
        )

        return SampleClusteringResult(
            linkage_matrix=linkage_matrix.tolist(),
            plot_path=str(plot_path),
            summary_dataframe=summary_dataframe,
        )

    def _validate_inputs(
        self,
        expression_df: pd.DataFrame,
    ) -> None:

        if "sample_id" not in expression_df.columns:
            raise ValueError(
                "Expression dataframe must contain 'sample_id' column."
            )

        gene_columns = [
            column
            for column in expression_df.columns
            if column != "sample_id"
        ]

        if not gene_columns:
            raise ValueError(
                "Expression dataframe must contain at least one gene column."
            )

        if len(expression_df) < 2:
            raise ValueError(
                "Sample clustering requires at least two samples."
            )

        non_numeric_columns = [
            column
            for column in gene_columns
            if not pd.api.types.is_numeric_dtype(expression_df[column])
        ]

        if non_numeric_columns:
            raise ValueError(
                "All gene expression columns must be numeric. "
                f"Non-numeric columns detected: {non_numeric_columns}"
            )
