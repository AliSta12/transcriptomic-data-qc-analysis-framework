from src.reporting.data_readiness_report import (
    DataReadinessReport,
    DATA_READINESS_REPORT_COLUMNS,
)


def test_ready_for_analysis():

    report = DataReadinessReport()

    report.add_summary(
        pass_count=10,
        warning_count=0,
        review_count=0,
        details="All QC checks passed.",
    )

    df = report.to_dataframe()

    assert df.loc[0, "overall_status"] == "READY_FOR_ANALYSIS"


def test_ready_with_warnings():

    report = DataReadinessReport()

    report.add_summary(
        pass_count=8,
        warning_count=2,
        review_count=0,
        details="Minor QC issues detected.",
    )

    df = report.to_dataframe()

    assert df.loc[0, "overall_status"] == "READY_WITH_WARNINGS"


def test_requires_review():

    report = DataReadinessReport()

    report.add_summary(
        pass_count=5,
        warning_count=3,
        review_count=1,
        details="Manual review required.",
    )

    df = report.to_dataframe()

    assert df.loc[0, "overall_status"] == "REQUIRES_REVIEW"


def test_empty_report():

    report = DataReadinessReport()

    df = report.to_dataframe()

    assert list(df.columns) == DATA_READINESS_REPORT_COLUMNS


def test_save_report(tmp_path):

    report = DataReadinessReport()

    report.add_summary(
        pass_count=10,
        warning_count=0,
        review_count=0,
        details="All checks passed.",
    )

    output_file = tmp_path / "data_readiness_report.csv"

    result = report.save(output_file)

    assert result.output_path.exists()

    saved_df = result.report_dataframe

    assert len(saved_df) == 1
    assert (
        saved_df.loc[0, "overall_status"]
        == "READY_FOR_ANALYSIS"
    )
