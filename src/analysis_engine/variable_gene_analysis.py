from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from src.shared.plot_style import VARIABLE_GENE_GRADIENT, VARIABLE_GENE_SINGLE_COLOR


@dataclass
class VariableGeneAnalysisResult:
    top_50_genes: pd.DataFrame
    top_100_genes: pd.DataFrame
    top_50_path: str
    top_100_path: str
    barplot_path: str
    summary_dataframe: pd.DataFrame


class VariableGeneAnalysis:
    """
    Identifies the most variable genes in a cleaned expression matrix.

    This module expects:
    - expression matrix in sample x gene format
    - first column named sample_id

    The ranking is exploratory and does not represent differential expression analysis.
    """

    def generate(
        self,
        expression_df: pd.DataFrame,
        output_directory: str,
    ) -> VariableGeneAnalysisResult:

        self._validate_inputs(expression_df)

        gene_columns = [col for col in expression_df.columns if col != "sample_id"]
        expression_values = expression_df[gene_columns]

        gene_variances = expression_values.var(axis=0)

        variable_genes_df = gene_variances.reset_index()
        variable_genes_df.columns = ["gene", "variance"]

        variable_genes_df = (
            variable_genes_df
            .sort_values(by="variance", ascending=False)
            .reset_index(drop=True)
        )

        top_50_genes = variable_genes_df.head(50).copy()
        top_100_genes = variable_genes_df.head(100).copy()

        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        top_50_path = output_dir / "top_50_variable_genes.csv"
        top_100_path = output_dir / "top_100_variable_genes.csv"

        barplot_path = output_dir / "top_variable_genes_barplot.png"

        top_50_genes.to_csv(top_50_path, index=False)
        top_100_genes.to_csv(top_100_path, index=False)

        variance_cmap = LinearSegmentedColormap.from_list(
            "project_variance",
            VARIABLE_GENE_GRADIENT,
        )

        max_genes_to_display = 20

        plot_genes = top_50_genes.head(max_genes_to_display).copy()
        plot_genes["gene_label"] = plot_genes["gene"].astype(str).apply(
            lambda label: self._truncate_label(label, max_length=32)
        )

        variance_values = plot_genes["variance"]

        if variance_values.max() == variance_values.min():
            bar_colors = [
                VARIABLE_GENE_SINGLE_COLOR
                for _ in variance_values
            ]
        else:
            normalized_variance = (
                (variance_values - variance_values.min()) /
                (variance_values.max() - variance_values.min())
            )
            bar_colors = [
                variance_cmap(value)
                for value in normalized_variance
            ]

        display_genes = plot_genes.sort_values(
            by="variance",
            ascending=True,
        )

        plt.figure(figsize=(10, 7))

        plt.barh(
            display_genes["gene_label"],
            display_genes["variance"],
            color=list(reversed(bar_colors)),
            edgecolor="white",
            linewidth=0.8,
        )

        plt.title("Top 20 Most Variable Genes (Exploratory Ranking)")
        plt.xlabel("Variance")
        plt.ylabel("Gene")

        if len(top_50_genes) > max_genes_to_display:
            plt.figtext(
                0.5,
                0.01,
                (
                    f"Showing top {max_genes_to_display} genes for readability. "
                    "Full top 50 and top 100 rankings are exported as CSV files."
                ),
                ha="center",
                fontsize=8,
            )
            plt.tight_layout(rect=[0, 0.04, 1, 1])
        else:
            plt.tight_layout()
        plt.savefig(barplot_path, dpi=300, bbox_inches="tight")
        plt.close()
        
        summary_dataframe = pd.DataFrame(
            [
                {
                    "metric": "total_genes_analyzed",
                    "value": len(gene_columns),
                },
                {
                    "metric": "top_50_genes_reported",
                    "value": len(top_50_genes),
                },
                {
                    "metric": "top_100_genes_reported",
                    "value": len(top_100_genes),
                },
                {
                    "metric": "highest_variance",
                    "value": float(variable_genes_df["variance"].max()),
                },
                {
                    "metric": "lowest_variance",
                    "value": float(variable_genes_df["variance"].min()),
                },
            ]
        )

        return VariableGeneAnalysisResult(
            top_50_genes=top_50_genes,
            top_100_genes=top_100_genes,
            top_50_path=str(top_50_path),
            top_100_path=str(top_100_path),
            barplot_path=str(barplot_path),
            summary_dataframe=summary_dataframe,
        )

    def _truncate_label(self, label: str, max_length: int) -> str:
        if len(label) <= max_length:
            return label

        return f"{label[:max_length - 3]}..."

    def _validate_inputs(
        self,
        expression_df: pd.DataFrame,
    ) -> None:

        if "sample_id" not in expression_df.columns:
            raise ValueError("Expression dataframe must contain 'sample_id' column.")

        gene_columns = [col for col in expression_df.columns if col != "sample_id"]

        if not gene_columns:
            raise ValueError("Expression dataframe must contain at least one gene column.")

        non_numeric_columns = [
            col for col in gene_columns if not pd.api.types.is_numeric_dtype(expression_df[col])
        ]

        if non_numeric_columns:
            raise ValueError(
                "All gene expression columns must be numeric. "
                f"Non-numeric columns detected: {non_numeric_columns}"
            )
