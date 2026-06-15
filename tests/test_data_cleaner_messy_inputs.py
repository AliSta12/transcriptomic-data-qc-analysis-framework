import pandas as pd
import pytest

from src.data_cleaner.data_cleaner_pipeline import DataCleanerPipeline


def test_class_column_is_harmonized_to_group():
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "TP53": [1.0, 2.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "Class": ["control", "case"],
        }
    )

    result = DataCleanerPipeline().run(expression_df, metadata_df)

    assert "group" in result.clean_metadata.columns
    assert result.clean_metadata["group"].tolist() == ["control", "case"]


def test_missing_group_column_raises_value_error():
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "TP53": [1.0, 2.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "condition": ["control", "case"],
        }
    )

    with pytest.raises(ValueError, match="group"):
        DataCleanerPipeline().run(expression_df, metadata_df)


def test_duplicate_expression_samples_require_review_and_are_retained():
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S1", "S2"],
            "TP53": [1.0, 1.5, 2.0],
            "BRCA1": [3.0, 3.5, 4.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    result = DataCleanerPipeline().run(expression_df, metadata_df)

    duplicate_samples_row = result.data_quality_report.loc[
        result.data_quality_report["check"] == "Duplicate Samples"
    ].iloc[0]

    assert duplicate_samples_row["status"] == "REQUIRES REVIEW"
    assert result.cleaned_expression_matrix["sample_id"].tolist().count("S1") == 2
    assert "review_duplicate_sample" in result.audit_log["rule_applied"].tolist()


def test_duplicate_genes_are_aggregated_by_mean():
    expression_df = pd.DataFrame(
        [
            ["S1", 1.0, 3.0, 10.0],
            ["S2", 2.0, 4.0, 20.0],
        ],
        columns=["sample_id", "TP53", "TP53", "BRCA1"],
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    result = DataCleanerPipeline().run(expression_df, metadata_df)

    assert result.cleaned_expression_matrix.columns.tolist().count("TP53") == 1
    assert result.cleaned_expression_matrix["TP53"].tolist() == [2.0, 3.0]
    assert "aggregate_duplicate_gene" in result.audit_log["rule_applied"].tolist()


def test_low_missing_gene_is_imputed_by_median():
    expression_df = pd.DataFrame(
        {
            "sample_id": [f"S{i}" for i in range(1, 22)],
            "TP53": [
                1.0, 2.0, 3.0, 4.0, 5.0,
                6.0, 7.0, 8.0, 9.0, 10.0,
                11.0, 12.0, 13.0, 14.0, 15.0,
                16.0, 17.0, 18.0, 19.0, 20.0,
                None,
            ],
            "BRCA1": [10.0] * 21,
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": [f"S{i}" for i in range(1, 22)],
            "group": ["A"] * 10 + ["B"] * 11,
        }
    )

    result = DataCleanerPipeline().run(expression_df, metadata_df)

    assert result.cleaned_expression_matrix["TP53"].isna().sum() == 0
    assert "impute_low_missing_gene" in result.audit_log["rule_applied"].tolist()


def test_high_missing_gene_is_removed():
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3", "S4"],
            "TP53": [1.0, None, None, None],
            "BRCA1": [1.0, 2.0, 3.0, 4.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3", "S4"],
            "group": ["A", "A", "B", "B"],
        }
    )

    result = DataCleanerPipeline().run(expression_df, metadata_df)

    assert "TP53" not in result.cleaned_expression_matrix.columns
    assert "remove_high_missing_gene" in result.audit_log["rule_applied"].tolist()


def test_expression_sample_without_metadata_requires_review():
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "TP53": [1.0, 2.0, 3.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    result = DataCleanerPipeline().run(expression_df, metadata_df)

    metadata_row = result.data_quality_report.loc[
        result.data_quality_report["check"] == "Metadata Consistency"
    ].iloc[0]

    assert metadata_row["status"] == "REQUIRES REVIEW"
    assert "detect_missing_metadata" in result.audit_log["rule_applied"].tolist()


def test_extra_metadata_sample_gives_warning():
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "TP53": [1.0, 2.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "group": ["A", "B", "C"],
        }
    )

    result = DataCleanerPipeline().run(expression_df, metadata_df)

    metadata_row = result.data_quality_report.loc[
        result.data_quality_report["check"] == "Metadata Consistency"
    ].iloc[0]

    assert metadata_row["status"] == "WARNING"
    assert "detect_extra_metadata" in result.audit_log["rule_applied"].tolist()


def test_gene_by_sample_orientation_is_transposed_to_sample_by_gene():
    expression_df = pd.DataFrame(
        {
            "gene": ["TP53", "BRCA1"],
            "S1": [1.0, 3.0],
            "S2": [2.0, 4.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    result = DataCleanerPipeline().run(expression_df, metadata_df)

    assert result.cleaned_expression_matrix["sample_id"].tolist() == ["S1", "S2"]
    assert "TP53" in result.cleaned_expression_matrix.columns
    assert "BRCA1" in result.cleaned_expression_matrix.columns
