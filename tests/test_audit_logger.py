import pandas as pd
import pytest

from src.data_cleaner.audit_logger import AuditLogger, AUDIT_LOG_COLUMNS


def test_audit_logger_adds_entry():
    logger = AuditLogger()

    logger.log(
        module="Harmonization",
        action="Column Standardization",
        target="Sample ID",
        old_value="Sample ID",
        new_value="sample_id",
        rule_applied="standardize_column_names",
        decision="renamed",
        status="PASS",
        reason="Technical column names must be standardized.",
    )

    df = logger.to_dataframe()

    assert len(df) == 1
    assert list(df.columns) == AUDIT_LOG_COLUMNS
    assert df.loc[0, "module"] == "Harmonization"
    assert df.loc[0, "status"] == "PASS"
    assert df.loc[0, "reason"] == "Technical column names must be standardized."


def test_audit_logger_rejects_invalid_status():
    logger = AuditLogger()

    with pytest.raises(ValueError):
        logger.log(
            module="Missing Data",
            action="Check Missing Values",
            target="TP53",
            old_value="NA",
            new_value="NA",
            rule_applied="missing_data_check",
            decision="reported",
            status="OK",
            reason="Invalid status should be rejected.",
        )


def test_audit_logger_requires_reason():
    logger = AuditLogger()

    with pytest.raises(ValueError):
        logger.log(
            module="Missing Data",
            action="Check Missing Values",
            target="TP53",
            old_value="NA",
            new_value="NA",
            rule_applied="missing_data_check",
            decision="reported",
            status="WARNING",
            reason="",
        )


def test_audit_logger_saves_csv(tmp_path):
    logger = AuditLogger()

    logger.log(
        module="Constant Gene Detection",
        action="Remove Constant Gene",
        target="GAPDH",
        old_value="all_values_equal",
        new_value="removed",
        rule_applied="remove_constant_genes",
        decision="removed",
        status="WARNING",
        reason="Constant genes are not informative for exploratory analysis.",
    )

    output_file = tmp_path / "audit_log.csv"
    saved_path = logger.save(output_file)

    assert saved_path.exists()

    df = pd.read_csv(saved_path)

    assert len(df) == 1
    assert list(df.columns) == AUDIT_LOG_COLUMNS
    assert df.loc[0, "target"] == "GAPDH"
