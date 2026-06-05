import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger
from src.data_cleaner.constant_gene_detector import (
    ConstantGeneDetector,
)


def test_removes_constant_gene():

    df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "TP53": [1.0, 2.0, 3.0],
            "GAPDH": [5.0, 5.0, 5.0],
        }
    )

    logger = AuditLogger()
    detector = ConstantGeneDetector()

    result = detector.apply_rules(df, logger)

    assert "GAPDH" in result.removed_genes
    assert "GAPDH" not in result.cleaned_dataframe.columns
    assert result.removed_gene_count == 1


def test_keeps_variable_gene():

    df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "TP53": [1.0, 2.0, 3.0],
        }
    )

    detector = ConstantGeneDetector()

    result = detector.apply_rules(df)

    assert result.removed_genes == []
    assert "TP53" in result.cleaned_dataframe.columns


def test_logs_removed_gene():

    df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "GAPDH": [10.0, 10.0],
        }
    )

    logger = AuditLogger()
    detector = ConstantGeneDetector()

    result = detector.apply_rules(df, logger)

    audit_df = logger.to_dataframe()

    assert len(audit_df) == 1
    assert audit_df.loc[0, "target"] == "GAPDH"
    assert audit_df.loc[0, "status"] == "WARNING"


def test_requires_sample_id_column():

    df = pd.DataFrame(
        {
            "TP53": [1.0, 2.0],
        }
    )

    detector = ConstantGeneDetector()

    try:
        detector.apply_rules(df)
        assert False
    except ValueError:
        assert True
