from pathlib import Path

import pandas as pd

from src.reporting.missing_data_plot import MissingDataPlot


def test_missing_data_plot_generates_png(tmp_path):

    gene_missing_summary = pd.DataFrame(
        {
            "gene": ["TP53", "KRAS", "EGFR"],
            "missing_count": [2, 0, 1],
        }
    )

    result = MissingDataPlot().generate(
        gene_missing_summary=gene_missing_summary,
        output_directory=str(tmp_path),
    )

    assert Path(result.plot_path).exists()
    assert result.plot_path.endswith("missing_data_plot.png")


def test_missing_data_plot_requires_gene_column(tmp_path):

    gene_missing_summary = pd.DataFrame(
        {
            "missing_count": [1, 2],
        }
    )

    try:
        MissingDataPlot().generate(
            gene_missing_summary=gene_missing_summary,
            output_directory=str(tmp_path),
        )
        assert False
    except ValueError:
        assert True

