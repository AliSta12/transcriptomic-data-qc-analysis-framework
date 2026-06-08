from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.decomposition import PCA


@dataclass
class PCAAnalysisResult:
    pca_dataframe: pd.DataFrame
    explained_variance_ratio: list[float]
    plot_path: str
    summary_dataframe: pd.DataFrame


class PCAAnalysis:
    """
    Performs PCA on cleaned transcriptomic expression data.

    This module expects:
    - expression matrix in sample x gene format
    - first column named sample_id
    - metadata table containing sample_id and group columns
    """

    def generate(
        self,
        expression_df: pd.DataFrame,
        metadata_df: pd.DataFrame,
        output_directory: str,
    ) -> PCAAnalysisResult:

        self._validate_inputs(
            expression_df=expression_df,
            metadata_df=metadata_df,
        )

        gene_columns = [
            column
            for column in expression_df.columns
            if column != "sample_id"
        ]

        expression_values = expression_df[gene_columns]

        pca = PCA(n_components=2)

        principal_components = pca.fit_transform(expression_values)

        pca_dataframe = pd.DataFrame(
            {
                "sample_id": expression_df["sample_id"],
                "PC1": principal_components[:, 0],
                "PC2": principal_components[:, 1],
            }
        )

        pca_dataframe = pca_dataframe.merge(
            metadata_df[["sample_id", "group"]],
            on="sample_id",
            how="left",
        )

        output_dir = Path(output_directory)
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        plot_path = output_dir / "pca_plot.png"

        plt.figure(figsize=(8, 6))

        for group in pca_dataframe["group"].unique():
            group_data = pca_dataframe[
                pca_dataframe["group"] == group
            ]

            plt.scatter(
                group_data["PC1"],
                group_data["PC2"],
                label=group,
            )

        plt.title("PCA Plot")
        plt.xlabel(
            f"PC1 ({pca.explained_variance_ratio_[0] * 100:.1f}% variance)"
        )
        plt.ylabel(
            f"PC2 ({pca.explained_variance_ratio_[1] * 100:.1f}% variance)"
        )

        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()

        summary_dataframe = pd.DataFrame(
            [
                {
                    "metric": "pc1_variance_explained",
                    "value": float(
                        pca.explained_variance_ratio_[0]
                    ),
                },
                {
                    "metric": "pc2_variance_explained",
                    "value": float(
                        pca.explained_variance_ratio_[1]
                    ),
                },
            ]
        )

        return PCAAnalysisResult(
            pca_dataframe=pca_dataframe,
            explained_variance_ratio=list(
                pca.explained_variance_ratio_
            ),
            plot_path=str(plot_path),
            summary_dataframe=summary_dataframe,
        )

    def _validate_inputs(
        self,
        expression_df: pd.DataFrame,
        metadata_df: pd.DataFrame,
    ) -> None:

        if "sample_id" not in expression_df.columns:
            raise ValueError(
                "Expression dataframe must contain 'sample_id' column."
            )

        if "sample_id" not in metadata_df.columns:
            raise ValueError(
                "Metadata dataframe must contain 'sample_id' column."
            )

        if "group" not in metadata_df.columns:
            raise ValueError(
                "Metadata dataframe must contain 'group' column."
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
                "PCA requires at least two samples."
            )

        if len(gene_columns) < 2:
            raise ValueError(
                "PCA requires at least two gene columns."
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
