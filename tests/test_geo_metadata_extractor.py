from src.data_cleaner.geo_metadata_extractor import GeoMetadataExtractor


def test_geo_metadata_extractor_extracts_sample_ids_and_groups():
    lines = [
        '!Sample_title\t"Normal BC0043N"\t"Cancer BC0043T"\n',
        '!Sample_geo_accession\t"GSM398074"\t"GSM398075"\n',
    ]

    result = GeoMetadataExtractor.extract(lines)

    assert result.columns.tolist() == [
        "sample_id",
        "group",
        "sample_title",
    ]

    assert result["sample_id"].tolist() == [
        "GSM398074",
        "GSM398075",
    ]

    assert result["group"].tolist() == [
        "normal",
        "tumor",
    ]


def test_geo_metadata_extractor_raises_error_for_missing_titles():
    lines = [
        '!Sample_geo_accession\t"GSM398074"\t"GSM398075"\n',
    ]

    try:
        GeoMetadataExtractor.extract(lines)
    except ValueError as error:
        assert "sample titles" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_geo_metadata_extractor_raises_error_for_unknown_group():
    lines = [
        '!Sample_title\t"Unknown BC0043X"\n',
        '!Sample_geo_accession\t"GSM398074"\n',
    ]

    try:
        GeoMetadataExtractor.extract(lines)
    except ValueError as error:
        assert "Could not infer group" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")
