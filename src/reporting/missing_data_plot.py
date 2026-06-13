from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


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

        plot_df = (
            gene_missing_summary
            .sort_values(by="missing_count", ascending=False)
            .head(30)
        )

        total_missing_values = gene_missing_summary[
            "missing_count"
        ].sum()

        plt.figure(figsize=(12, 6))

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
            plt.bar(
                plot_df["gene"],
                plot_df["missing_count"],
            )

            plt.title("Missing Data Summary")
            plt.xlabel("Gene")
            plt.ylabel("Missing Value Count")
            plt.xticks(rotation=90)

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
