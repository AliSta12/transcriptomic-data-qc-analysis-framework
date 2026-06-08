import pandas as pd

from src.data_cleaner.metadata_harmonizer import MetadataHarmonizer


def test_metadata_harmonizer_renames_pancan_columns():
    metadata_df = pd.DataFrame(
        {
            "Unnamed: 0": ["sample_0", "sample_1"],
            "Class": ["BRCA", "LUAD"],
        }
    )

    result = MetadataHarmonizer.harmonize_metadata(metadata_df)

    assert result.columns.tolist() == ["sample_id", "group"]
    assert result["sample_id"].tolist() == ["sample_0", "sample_1"]
    assert result["group"].tolist() == ["BRCA", "LUAD"]


def test_metadata_harmonizer_preserves_standard_columns():
    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["control", "tumor"],
        }
    )

    result = MetadataHarmonizer.harmonize_metadata(metadata_df)

    assert result.columns.tolist() == ["sample_id", "group"]


def test_metadata_harmonizer_requires_group_column():
    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "condition": ["control", "tumor"],
        }
    )

    try:
        MetadataHarmonizer.harmonize_metadata(metadata_df)
    except ValueError as error:
        assert "group" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")
