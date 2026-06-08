import pandas as pd

from src.analysis_engine.analysis_summary_generator import (
    AnalysisSummaryGenerator,
)


def test_analysis_summary_generator_creates_outputs(tmp_path):
    summary_1 = pd.DataFrame(
        [
            {
                "metric": "sample_count",
                "value": 10,
            }
        ]
    )

    summary_2 = pd.DataFrame(
        [
            {
                "metric": "gene_count",
                "value": 500,
            }
        ]
    )

    result = AnalysisSummaryGenerator().generate(
        summary_dataframes=[summary_1, summary_2],
        output_directory=str(tmp_path),
    )

    assert len(result.summary_dataframe) == 2

    assert result.csv_path.endswith(
        "analysis_summary.csv"
    )

    assert result.markdown_path.endswith(
        "analysis_summary.md"
    )

    assert (
        tmp_path / "analysis_summary.csv"
    ).exists()

    assert (
        tmp_path / "analysis_summary.md"
    ).exists()


def test_analysis_summary_generator_requires_input_data():
    try:
        AnalysisSummaryGenerator().generate(
            summary_dataframes=[],
            output_directory="test",
        )
    except ValueError as error:
        assert "At least one summary dataframe" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError was not raised."
        )


def test_analysis_summary_generator_rejects_empty_dataframe():
    empty_dataframe = pd.DataFrame()

    try:
        AnalysisSummaryGenerator().generate(
            summary_dataframes=[empty_dataframe],
            output_directory="test",
        )
    except ValueError as error:
        assert "cannot be empty" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError was not raised."
        )
