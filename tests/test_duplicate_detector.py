import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger
from src.data_cleaner.duplicate_detector import DuplicateDetector


def test_duplicate_sample_is_detected():
    df = pd.DataFrame(
        {
            "sample_id": ["S1", "S1", "S2"],
            "TP53": [1.0, 1.2, 2.0],
            "KRAS": [3.0, 3.1, 4.0],
        }
    )

    logger = AuditLogger()
    detector = DuplicateDetector()

    result = detector.apply_rules(df, logger)

    assert "S1" in result.duplicate_samples

    audit_df = logger.to_dataframe()

    assert "REQUIRES REVIEW" in audit_df["status"].tolist()


def test_no_duplicate_sample():
    df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "TP53": [1.0, 2.0, 3.0],
        }
    )

    detector = DuplicateDetector()

    result = detector.apply_rules(df)

    assert result.duplicate_samples == []


def test_requires_sample_id_column():
    df = pd.DataFrame(
        {
            "TP53": [1.0, 2.0],
        }
    )

    detector = DuplicateDetector()

    try:
        detector.apply_rules(df)
        assert False
    except ValueError as error:
        assert "sample_id" in str(error)
