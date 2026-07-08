from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.shared.plot_style import QC_STATUS_COLORS


@dataclass
class QCStatusSummaryPlotResult:
    plot_path: str


class QCStatusSummaryPlot:
    """
    Generates a QC status summary plot based on the Data Quality Report.

    The plot counts PASS, WARNING, FAIL and REQUIRES REVIEW statuses.
    """

    def generate(
        self,
        data_quality_report: pd.DataFrame,
        output_directory: str,
    ) -> QCStatusSummaryPlotResult:

        self._validate_inputs(data_quality_report)

        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        plot_path = output_dir / "qc_status_summary_plot.png"

        status_counts = (
            data_quality_report["status"]
            .value_counts()
            .reindex(
                ["PASS", "WARNING", "FAIL", "REQUIRES REVIEW"],
                fill_value=0,
            )
        )

        bar_colors = [
            QC_STATUS_COLORS.get(status, "#999999")
            for status in status_counts.index
        ]

        plt.figure(figsize=(9, 5.5))
        bars = plt.bar(
            status_counts.index,
            status_counts.values,
            color=bar_colors,
            edgecolor="white",
            linewidth=0.8,
        )

        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                int(height),
                ha="center",
                va="bottom",
                fontsize=10,
            )

        max_count = status_counts.max()
        upper_limit = max_count * 1.20 if max_count > 0 else 1
        plt.ylim(0, upper_limit)

        plt.title("QC Status Summary")
        plt.xlabel("QC Status")
        plt.ylabel("Number of Checks")
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()

        return QCStatusSummaryPlotResult(
            plot_path=str(plot_path),
        )

    def _validate_inputs(
        self,
        data_quality_report: pd.DataFrame,
    ) -> None:

        if "status" not in data_quality_report.columns:
            raise ValueError(
                "Data quality report must contain 'status' column."
            )
