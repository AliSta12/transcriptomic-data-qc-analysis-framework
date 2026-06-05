from pathlib import Path

import pandas as pd

from src.analysis_engine.class_distribution_analysis import (
    ClassDistributionAnalysis,
)


def test_generates_class_distribution(tmp_path):

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3", "S4"],
            "group": ["A", "A", "B", "B"],
        }
    )

    analysis = ClassDistributionAnalysis()

    result = analysis.generate(
        metadata_df=metadata_df,
        output_directory=str(tmp_path),
    )

    assert result.group_distribution == {
        "A": 2,
        "B": 2,
    }

    assert Path(result.plot_path).exists()

    assert len(result.summary_dataframe) == 2


def test_requires_group_column(tmp_path):

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
        }
    )

    analysis = ClassDistributionAnalysis()

    try:
        analysis.generate(
            metadata_df=metadata_df,
            output_directory=str(tmp_path),
        )
        assert False
    except ValueError:
        assert True


def test_requires_sample_id_column(tmp_path):

    metadata_df = pd.DataFrame(
        {
            "group": ["A", "B"],
        }
    )

    analysis = ClassDistributionAnalysis()

    try:
        analysis.generate(
            metadata_df=metadata_df,
            output_directory=str(tmp_path),
        )
        assert False
    except ValueError:
        assert True
