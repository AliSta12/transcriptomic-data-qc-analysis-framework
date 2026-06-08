from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


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

        plt.figure(figsize=(12, 6))

        plt.bar(
            top_50_genes["gene"],
            top_50_genes["variance"],
        )

        plt.title("Top 50 Variable Genes")
        plt.xlabel("Gene")
        plt.ylabel("Variance")

        plt.xticks(rotation=90)

        plt.tight_layout()
        plt.savefig(barplot_path)
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
