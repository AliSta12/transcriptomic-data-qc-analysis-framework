import pandas as pd

from src.data_cleaner.structure_detector import (
    DataOrientation,
    DetectionConfidence,
    StructureDetector,
)


def test_detects_sample_x_gene_by_column_name():
    df = pd.DataFrame({
        "sample_id": ["S1", "S2"],
        "TP53": [5.2, 6.1],
        "KRAS": [7.1, 8.4],
    })

    result = StructureDetector.detect(df)

    assert result.orientation == DataOrientation.SAMPLE_X_GENE
    assert result.confidence == DetectionConfidence.HIGH


def test_detects_gene_x_sample_by_column_name():
    df = pd.DataFrame({
        "gene": ["TP53", "KRAS"],
        "S1": [5.2, 7.1],
        "S2": [6.1, 8.4],
    })

    result = StructureDetector.detect(df)

    assert result.orientation == DataOrientation.GENE_X_SAMPLE
    assert result.confidence == DetectionConfidence.HIGH


def test_detects_gene_x_sample_by_geo_like_probe_column():
    df = pd.DataFrame({
        "ID_REF": ["TP53", "KRAS", "EGFR"],
        "GSM001": [5.2, 7.1, 2.3],
        "GSM002": [6.1, 8.4, 1.9],
    })

    result = StructureDetector.detect(df)

    assert result.orientation == DataOrientation.GENE_X_SAMPLE
    assert result.confidence == DetectionConfidence.HIGH


def test_returns_unknown_for_empty_dataframe():
    df = pd.DataFrame()

    result = StructureDetector.detect(df)

    assert result.orientation == DataOrientation.UNKNOWN
    assert result.confidence == DetectionConfidence.LOW
