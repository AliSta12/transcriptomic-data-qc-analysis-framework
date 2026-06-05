import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger
from src.data_cleaner.metadata_consistency_checker import (
    MetadataConsistencyChecker,
)


def test_detects_missing_metadata_sample():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "TP53": [1, 2, 3],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "A"],
        }
    )

    logger = AuditLogger()
    checker = MetadataConsistencyChecker()

    result = checker.check(
        expression_df,
        metadata_df,
        logger,
    )

    assert "S3" in result.missing_metadata_samples
    assert result.status == "REQUIRES REVIEW"


def test_detects_extra_metadata_sample():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "TP53": [1, 2],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "group": ["A", "A", "B"],
        }
    )

    checker = MetadataConsistencyChecker()

    result = checker.check(
        expression_df,
        metadata_df,
    )

    assert "S3" in result.extra_metadata_samples
    assert result.status == "WARNING"


def test_detects_duplicate_metadata_sample():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "TP53": [1, 2],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S1", "S2"],
            "group": ["A", "A", "B"],
        }
    )

    checker = MetadataConsistencyChecker()

    result = checker.check(
        expression_df,
        metadata_df,
    )

    assert "S1" in result.duplicated_metadata_samples
    assert result.status == "REQUIRES REVIEW"


def test_detects_missing_group():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "TP53": [1, 2],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", None],
        }
    )

    checker = MetadataConsistencyChecker()

    result = checker.check(
        expression_df,
        metadata_df,
    )

    assert "S2" in result.samples_without_group
    assert result.status == "REQUIRES REVIEW"


def test_passes_when_metadata_are_consistent():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "TP53": [1, 2],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    checker = MetadataConsistencyChecker()

    result = checker.check(
        expression_df,
        metadata_df,
    )

    assert result.status == "PASS"


def test_requires_sample_id_column():

    expression_df = pd.DataFrame(
        {
            "TP53": [1, 2],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    checker = MetadataConsistencyChecker()

    try:
        checker.check(expression_df, metadata_df)
        assert False
    except ValueError:
        assert True
