import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger
from src.data_cleaner.missing_data_handler import MissingDataHandler


def test_gene_missing_exactly_5_percent_is_imputed():
    dataframe = pd.DataFrame(
        {
            "sample_id": [f"S{i}" for i in range(1, 21)],
            "TP53": [
                1.0, 2.0, 3.0, 4.0, 5.0,
                6.0, 7.0, 8.0, 9.0, 10.0,
                11.0, 12.0, 13.0, 14.0, 15.0,
                16.0, 17.0, 18.0, 19.0, None,
            ],
            "BRCA1": list(range(101, 121)),
        }
    )

    audit_logger = AuditLogger()
    result = MissingDataHandler().apply_rules(dataframe, audit_logger)

    assert "TP53" in result.imputed_genes
    assert result.cleaned_dataframe["TP53"].isna().sum() == 0
    assert "impute_low_missing_gene" in audit_logger.to_dataframe()["rule_applied"].tolist()


def test_gene_missing_exactly_20_percent_is_kept_with_warning():
    dataframe = pd.DataFrame(
        {
            "sample_id": [f"S{i}" for i in range(1, 21)],
            "TP53": [
                1.0, 2.0, 3.0, 4.0,
                None, None, None, None,
                9.0, 10.0, 11.0, 12.0,
                13.0, 14.0, 15.0, 16.0,
                17.0, 18.0, 19.0, 20.0,
            ],
            "BRCA1": list(range(101, 121)),
        }
    )

    audit_logger = AuditLogger()
    result = MissingDataHandler().apply_rules(dataframe, audit_logger)

    assert "TP53" in result.cleaned_dataframe.columns
    assert result.cleaned_dataframe["TP53"].isna().sum() == 4
    assert "keep_moderate_missing_gene" in audit_logger.to_dataframe()["rule_applied"].tolist()


def test_gene_missing_just_above_20_percent_is_removed():
    dataframe = pd.DataFrame(
        {
            "sample_id": [f"S{i}" for i in range(1, 21)],
            "TP53": [
                1.0, 2.0, 3.0,
                None, None, None, None, None,
                9.0, 10.0, 11.0, 12.0,
                13.0, 14.0, 15.0, 16.0,
                17.0, 18.0, 19.0, 20.0,
            ],
            "BRCA1": list(range(101, 121)),
        }
    )

    audit_logger = AuditLogger()
    result = MissingDataHandler().apply_rules(dataframe, audit_logger)

    assert "TP53" not in result.cleaned_dataframe.columns
    assert "TP53" in result.removed_genes
    assert "remove_high_missing_gene" in audit_logger.to_dataframe()["rule_applied"].tolist()


def test_sample_missing_exactly_20_percent_does_not_require_review():
    dataframe = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "GENE1": [None, 2.0, 3.0],
            "GENE2": [2.0, 3.0, 4.0],
            "GENE3": [3.0, 4.0, 5.0],
            "GENE4": [4.0, 5.0, 6.0],
            "GENE5": [5.0, 6.0, 7.0],
        }
    )

    audit_logger = AuditLogger()
    result = MissingDataHandler().apply_rules(dataframe, audit_logger)

    assert "S1" not in result.review_samples

    audit_df = audit_logger.to_dataframe()
    review_entries = audit_df[
        audit_df["rule_applied"] == "review_high_missing_sample"
    ]

    assert "S1" not in review_entries["target"].tolist()


def test_sample_missing_above_20_percent_requires_review():
    dataframe = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "GENE1": [None, 2.0, 3.0],
            "GENE2": [None, 3.0, 4.0],
            "GENE3": [3.0, 4.0, 5.0],
            "GENE4": [4.0, 5.0, 6.0],
            "GENE5": [5.0, 6.0, 7.0],
        }
    )

    audit_logger = AuditLogger()
    result = MissingDataHandler().apply_rules(dataframe, audit_logger)

    assert "S1" in result.review_samples

    audit_df = audit_logger.to_dataframe()
    review_entries = audit_df[
        audit_df["rule_applied"] == "review_high_missing_sample"
    ]

    assert "S1" in review_entries["target"].tolist()
