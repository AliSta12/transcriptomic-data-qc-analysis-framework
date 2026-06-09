from pathlib import Path

import pandas as pd

from src.reporting.qc_status_summary_plot import QCStatusSummaryPlot


def test_qc_status_summary_plot_generates_png(tmp_path):

    data_quality_report = pd.DataFrame(
        {
            "check": ["Missing Data", "Duplicate Genes", "Metadata Consistency"],
            "status": ["PASS", "WARNING", "REQUIRES REVIEW"],
        }
    )

    result = QCStatusSummaryPlot().generate(
        data_quality_report=data_quality_report,
        output_directory=str(tmp_path),
    )

    assert Path(result.plot_path).exists()
    assert result.plot_path.endswith("qc_status_summary_plot.png")


def test_qc_status_summary_plot_requires_status_column(tmp_path):

    data_quality_report = pd.DataFrame(
        {
            "check": ["Missing Data"],
        }
    )

    try:
        QCStatusSummaryPlot().generate(
            data_quality_report=data_quality_report,
            output_directory=str(tmp_path),
        )
        assert False
    except ValueError:
        assert True
