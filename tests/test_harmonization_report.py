from pathlib import Path
import pandas as pd

from src.reporting.harmonization_report import (
    HarmonizationReport,
    HARMONIZATION_REPORT_COLUMNS,
)


def test_adds_report_entry():

    report = HarmonizationReport()

    report.add_entry(
        original_element="Gene Symbol",
        standardized_element="gene_symbol",
        element_type="column",
        transformation="rename",
        reason="Column names must follow project naming convention.",
    )

    df = report.to_dataframe()

    assert len(df) == 1
    assert list(df.columns) == HARMONIZATION_REPORT_COLUMNS

    assert df.loc[0, "original_element"] == "Gene Symbol"
    assert df.loc[0, "standardized_element"] == "gene_symbol"


def test_requires_reason():

    report = HarmonizationReport()

    try:
        report.add_entry(
            original_element="Gene Symbol",
            standardized_element="gene_symbol",
            element_type="column",
            transformation="rename",
            reason="",
        )
        assert False
    except ValueError:
        assert True


def test_saves_report(tmp_path):

    report = HarmonizationReport()

    report.add_entry(
        original_element="gene x sample",
        standardized_element="sample x gene",
        element_type="orientation",
        transformation="transpose",
        reason="Project internal format is sample x gene.",
    )

    output_file = tmp_path / "harmonization_report.csv"

    result = report.save(output_file)

    assert result.output_path.exists()

    saved_df = pd.read_csv(result.output_path)

    assert len(saved_df) == 1

    assert (
        saved_df.loc[0, "transformation"]
        == "transpose"
    )


def test_empty_report_creates_dataframe():

    report = HarmonizationReport()

    df = report.to_dataframe()

    assert list(df.columns) == HARMONIZATION_REPORT_COLUMNS
