from src.reporting.data_quality_report import (
    DataQualityReport,
    DATA_QUALITY_REPORT_COLUMNS,
)


def test_adds_quality_check():

    report = DataQualityReport()

    report.add_check(
        check="Missing Data",
        status="WARNING",
        metric="8.3%",
        threshold="<5%",
        details="Missing values exceed recommended threshold.",
    )

    df = report.to_dataframe()

    assert len(df) == 1
    assert list(df.columns) == DATA_QUALITY_REPORT_COLUMNS

    assert df.loc[0, "check"] == "Missing Data"
    assert df.loc[0, "status"] == "WARNING"


def test_multiple_checks():

    report = DataQualityReport()

    report.add_check(
        check="Missing Data",
        status="WARNING",
        metric="8.3%",
        threshold="<5%",
        details="Missing values detected.",
    )

    report.add_check(
        check="Metadata Consistency",
        status="PASS",
        metric="100%",
        threshold="100%",
        details="All samples matched.",
    )

    df = report.to_dataframe()

    assert len(df) == 2


def test_empty_report():

    report = DataQualityReport()

    df = report.to_dataframe()

    assert list(df.columns) == DATA_QUALITY_REPORT_COLUMNS


def test_save_report(tmp_path):

    report = DataQualityReport()

    report.add_check(
        check="Duplicate Samples",
        status="REQUIRES REVIEW",
        metric="2",
        threshold="0",
        details="Duplicate sample IDs detected.",
    )

    output_file = tmp_path / "data_quality_report.csv"

    result = report.save(output_file)

    assert result.output_path.exists()

    saved_df = result.report_dataframe

    assert len(saved_df) == 1
    assert saved_df.loc[0, "check"] == "Duplicate Samples"
from src.reporting.data_quality_report import (
    DataQualityReport,
    DATA_QUALITY_REPORT_COLUMNS,
)


def test_adds_quality_check():

    report = DataQualityReport()

    report.add_check(
        check="Missing Data",
        status="WARNING",
        metric="8.3%",
        threshold="<5%",
        details="Missing values exceed recommended threshold.",
    )

    df = report.to_dataframe()

    assert len(df) == 1
    assert list(df.columns) == DATA_QUALITY_REPORT_COLUMNS

    assert df.loc[0, "check"] == "Missing Data"
    assert df.loc[0, "status"] == "WARNING"


def test_multiple_checks():

    report = DataQualityReport()

    report.add_check(
        check="Missing Data",
        status="WARNING",
        metric="8.3%",
        threshold="<5%",
        details="Missing values detected.",
    )

    report.add_check(
        check="Metadata Consistency",
        status="PASS",
        metric="100%",
        threshold="100%",
        details="All samples matched.",
    )

    df = report.to_dataframe()

    assert len(df) == 2


def test_empty_report():

    report = DataQualityReport()

    df = report.to_dataframe()

    assert list(df.columns) == DATA_QUALITY_REPORT_COLUMNS


def test_save_report(tmp_path):

    report = DataQualityReport()

    report.add_check(
        check="Duplicate Samples",
        status="REQUIRES REVIEW",
        metric="2",
        threshold="0",
        details="Duplicate sample IDs detected.",
    )

    output_file = tmp_path / "data_quality_report.csv"

    result = report.save(output_file)

    assert result.output_path.exists()

    saved_df = result.report_dataframe

    assert len(saved_df) == 1
    assert saved_df.loc[0, "check"] == "Duplicate Samples"
