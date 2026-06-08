import pandas as pd

from src.data_cleaner.data_cleaner_pipeline import (
    DataCleanerPipeline,
)


def test_pipeline_runs_end_to_end():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "TP53": [1.0, 2.0, 3.0],
            "GAPDH": [5.0, 5.0, 5.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "group": ["A", "A", "B"],
        }
    )

    pipeline = DataCleanerPipeline()

    result = pipeline.run(
        expression_df,
        metadata_df,
    )

    assert result.final_status in [
        "READY_FOR_ANALYSIS",
        "READY_WITH_WARNINGS",
        "REQUIRES_REVIEW",
    ]

    assert "TP53" in result.cleaned_expression_matrix.columns
    assert "GAPDH" not in result.cleaned_expression_matrix.columns

    assert len(result.audit_log) >= 1
    assert len(result.data_quality_report) > 0
    assert len(result.data_readiness_report) == 1


def test_pipeline_returns_clean_metadata():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "TP53": [1.0, 2.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    pipeline = DataCleanerPipeline()

    result = pipeline.run(
        expression_df,
        metadata_df,
    )

    assert result.clean_metadata.columns.tolist() == [
        "sample_id",
        "group",
        "dataset",
    ]

    assert result.clean_metadata["dataset"].tolist() == [
        "unknown",
        "unknown",
    ]


def test_pipeline_generates_reports():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "TP53": [1.0, 2.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    pipeline = DataCleanerPipeline()

    result = pipeline.run(
        expression_df,
        metadata_df,
    )

    assert not result.harmonization_report.empty
    assert not result.data_quality_report.empty
    assert not result.data_readiness_report.empty


