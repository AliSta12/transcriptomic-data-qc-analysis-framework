import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger
from src.data_cleaner.missing_data_handler import MissingDataHandler


def test_low_missing_gene_is_imputed():
    df = pd.DataFrame(
    {
        "sample_id": [f"S{i}" for i in range(1, 21)],
        "TP53": [1.0, None] + [3.0] * 18,
        "KRAS": [2.0] * 20,
        "EGFR": [4.0] * 20,
        "BRCA1": [5.0] * 20,
        "MYC": [6.0] * 20,
        "PTEN": [7.0] * 20,
    }
)

    logger = AuditLogger()
    handler = MissingDataHandler()

    result = handler.apply_rules(df, logger)

    assert "TP53" in result.imputed_genes
    assert result.cleaned_dataframe["TP53"].isna().sum() == 0
    assert len(logger.to_dataframe()) == 1
    assert logger.to_dataframe().loc[0, "decision"] == "imputed"


def test_moderate_missing_gene_is_kept_with_warning():
    df = pd.DataFrame(
        {
            "sample_id": [f"S{i}" for i in range(1, 21)],
            "TP53": [None, None] + [3.0] * 18,
            "KRAS": [2.0] * 20,
        }
    )

    logger = AuditLogger()
    handler = MissingDataHandler()

    result = handler.apply_rules(df, logger)

    assert "TP53" in result.cleaned_dataframe.columns
    assert "TP53" not in result.imputed_genes
    assert "TP53" not in result.removed_genes
    assert result.cleaned_dataframe["TP53"].isna().sum() == 2
    assert logger.to_dataframe().loc[0, "decision"] == "kept_with_warning"


def test_high_missing_gene_is_removed():
    df = pd.DataFrame(
        {
            "sample_id": [f"S{i}" for i in range(1, 21)],
            "TP53": [None, None, None, None, None] + [3.0] * 15,
            "KRAS": [2.0] * 20,
        }
    )

    logger = AuditLogger()
    handler = MissingDataHandler()

    result = handler.apply_rules(df, logger)

    assert "TP53" in result.removed_genes
    assert "TP53" not in result.cleaned_dataframe.columns
    assert logger.to_dataframe().loc[0, "decision"] == "removed"


def test_high_missing_sample_is_marked_for_review():
    df = pd.DataFrame(
        {
            "sample_id": [f"S{i}" for i in range(1, 21)],
            "TP53": [None] + [1.0] * 19,
            "KRAS": [None] + [2.0] * 19,
            "EGFR": [3.0] * 20,
            "BRCA1": [4.0] * 20,
            "MYC": [5.0] * 20,
        }
    )

    logger = AuditLogger()
    handler = MissingDataHandler()

    result = handler.apply_rules(df, logger)

    assert "S1" in result.review_samples
    assert "S1" in result.cleaned_dataframe["sample_id"].tolist()

    audit_df = logger.to_dataframe()
    assert "REQUIRES REVIEW" in audit_df["status"].tolist()


def test_missing_data_handler_requires_sample_id():
    df = pd.DataFrame(
        {
            "TP53": [1.0, None],
            "KRAS": [2.0, 3.0],
        }
    )

    handler = MissingDataHandler()

    try:
        handler.apply_rules(df)
        assert False
    except ValueError as error:
        assert "sample_id" in str(error)
