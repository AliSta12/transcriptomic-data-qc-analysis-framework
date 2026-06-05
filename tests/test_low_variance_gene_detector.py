import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger
from src.data_cleaner.low_variance_gene_detector import (
    LowVarianceGeneDetector,
)


def test_removes_low_variance_gene():

    df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3", "S4"],
            "TP53": [1.0, 2.0, 3.0, 4.0],
            "LOW_VAR": [5.00, 5.01, 5.00, 5.01],
        }
    )

    detector = LowVarianceGeneDetector()

    result = detector.apply_rules(df)

    assert "LOW_VAR" in result.removed_genes
    assert "LOW_VAR" not in result.cleaned_dataframe.columns


def test_keeps_high_variance_gene():

    df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3", "S4"],
            "TP53": [1.0, 3.0, 5.0, 7.0],
        }
    )

    detector = LowVarianceGeneDetector()

    result = detector.apply_rules(df)

    assert result.removed_genes == []
    assert "TP53" in result.cleaned_dataframe.columns


def test_logs_removed_gene():

    df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3", "S4"],
            "LOW_VAR": [10.0, 10.01, 10.0, 10.01],
        }
    )

    logger = AuditLogger()
    detector = LowVarianceGeneDetector()

    result = detector.apply_rules(df, logger)

    audit_df = logger.to_dataframe()

    assert len(audit_df) == 1
    assert audit_df.loc[0, "status"] == "WARNING"
    assert audit_df.loc[0, "decision"] == "removed"


def test_requires_sample_id_column():

    df = pd.DataFrame(
        {
            "TP53": [1.0, 2.0],
        }
    )

    detector = LowVarianceGeneDetector()

    try:
        detector.apply_rules(df)
        assert False
    except ValueError:
        assert True
