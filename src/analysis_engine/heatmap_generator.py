from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


@dataclass
class HeatmapGeneratorResult:
    heatmap_dataframe: pd.DataFrame
    plot_path: str
    summary_dataframe: pd.DataFrame


class HeatmapGenerator:
    """
    Generates a heatmap for the top variable genes.

    This module expects:
    - expression matrix in sample x gene format
    - first column named sample_id
    - dataframe containing a 'gene' column
    """

    def generate(
        self,
        expression_df: pd.DataFrame,
        top_variable_genes_df: pd.DataFrame,
        output_directory: str,
    ) -> HeatmapGeneratorResult:

        self._validate_inputs(
            expression_df=expression_df,
            top_variable_genes_df=top_variable_genes_df,
        )

        selected_genes = top_variable_genes_df["gene"].tolist()

        heatmap_dataframe = expression_df[
            ["sample_id"] + selected_genes
        ].copy()

        heatmap_values = heatmap_dataframe.drop(
            columns=["sample_id"]
        )

        output_dir = Path(output_directory)
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        plot_path = (
            output_dir /
            "heatmap_top50_variable_genes.png"
        )

        plt.figure(figsize=(12, 8))

        plt.imshow(
            heatmap_values.T,
            aspect="auto",
        )

        plt.colorbar(
            label="Expression"
        )

        plt.title(
            "Top 50 Variable Genes Heatmap"
        )

        plt.xlabel(
            "Samples"
        )

        plt.ylabel(
            "Genes"
        )

        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()

        summary_dataframe = pd.DataFrame(
            [
                {
                    "metric": "sample_count",
                    "value": len(heatmap_dataframe),
                },
                {
                    "metric": "gene_count",
                    "value": len(selected_genes),
                },
            ]
        )

        return HeatmapGeneratorResult(
            heatmap_dataframe=heatmap_dataframe,
            plot_path=str(plot_path),
            summary_dataframe=summary_dataframe,
        )

    def _validate_inputs(
        self,
        expression_df: pd.DataFrame,
        top_variable_genes_df: pd.DataFrame,
    ) -> None:

        if "sample_id" not in expression_df.columns:
            raise ValueError(
                "Expression dataframe must contain 'sample_id' column."
            )

        if "gene" not in top_variable_genes_df.columns:
            raise ValueError(
                "Top variable genes dataframe must contain 'gene' column."
            )

        selected_genes = top_variable_genes_df["gene"].tolist()

        missing_genes = [
            gene
            for gene in selected_genes
            if gene not in expression_df.columns
        ]

        if missing_genes:
            raise ValueError(
                f"Genes not found in expression dataframe: {missing_genes}"
            )

        if not selected_genes:
            raise ValueError(
                "At least one gene is required for heatmap generation."
            )

