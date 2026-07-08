from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.shared.plot_style import MISSING_DATA_COLOR


@dataclass
class MissingDataPlotResult:
    plot_path: str


class MissingDataPlot:
    """
    Generates a missing data summary plot for Data Cleaner reporting.

    The plot summarizes the number of missing values per gene.
    It is intended for exploratory QC reporting, not for statistical inference.
    """

    def generate(
        self,
        gene_missing_summary: pd.DataFrame,
        output_directory: str,
    ) -> MissingDataPlotResult:

        self._validate_inputs(gene_missing_summary)

        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        plot_path = output_dir / "missing_data_plot.png"

        max_genes_to_display = 20

        total_missing_values = gene_missing_summary[
            "missing_count"
        ].sum()

        genes_with_missing_values = gene_missing_summary[
            gene_missing_summary["missing_count"] > 0
        ]

        plot_df = (
            genes_with_missing_values
            .sort_values(by="missing_count", ascending=False)
            .head(max_genes_to_display)
            .copy()
        )

        plot_df["gene_label"] = plot_df["gene"].astype(str).apply(
            lambda label: self._truncate_label(label, max_length=32)
        )

        plt.figure(figsize=(10, 7))

        if total_missing_values == 0:
            plt.text(
                0.5,
                0.5,
                "No missing values detected",
                ha="center",
                va="center",
                fontsize=16,
            )
            plt.title("Missing Data Summary")
            plt.axis("off")
        else:
            display_df = plot_df.sort_values(
                by="missing_count",
                ascending=True,
            )

            plt.barh(
                display_df["gene_label"],
                display_df["missing_count"],
                color=MISSING_DATA_COLOR,
                edgecolor="white",
                linewidth=0.8,
            )

            plt.title("Missing Data Summary (Top Genes by Missing Values)")
            plt.xlabel("Missing Value Count")
            plt.ylabel("Gene")

            if len(genes_with_missing_values) > max_genes_to_display:
                plt.figtext(
                    0.5,
                    0.01,
                    (
                        f"Showing top {max_genes_to_display} genes only. "
                        "Full missing-value details are available in QC tables."
                    ),
                    ha="center",
                    fontsize=8,
                )
                plt.tight_layout(rect=[0, 0.04, 1, 1])
            else:
                plt.tight_layout()

        if total_missing_values == 0:
            plt.tight_layout()
        plt.savefig(
            plot_path,
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

        return MissingDataPlotResult(
            plot_path=str(plot_path),
        )

    def _truncate_label(self, label: str, max_length: int) -> str:
        if len(label) <= max_length:
            return label

        return f"{label[:max_length - 3]}..."

    def _validate_inputs(
        self,
        gene_missing_summary: pd.DataFrame,
    ) -> None:

        required_columns = {
            "gene",
            "missing_count",
        }

        missing_columns = required_columns - set(gene_missing_summary.columns)

        if missing_columns:
            raise ValueError(
                "Gene missing summary is missing required columns: "
                f"{sorted(missing_columns)}"
            )
