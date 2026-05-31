import pandas as pd
import pytest

from src.data_cleaner.harmonizer import Harmonizer
from src.data_cleaner.structure_detector import DataOrientation


def test_sample_x_gene_is_preserved():
    df = pd.DataFrame({
        "sample_id": ["S1", "S2"],
        "TP53": [5.2, 6.1],
        "KRAS": [7.1, 8.4],
    })

    result = Harmonizer.harmonize_expression_matrix(
        df,
        DataOrientation.SAMPLE_X_GENE,
    )

    assert result.shape == (2, 3)
    assert result.columns[0] == "sample_id"


def test_gene_x_sample_is_transposed():
    df = pd.DataFrame({
        "gene": ["TP53", "KRAS"],
        "S1": [5.2, 7.1],
        "S2": [6.1, 8.4],
    })

    result = Harmonizer.harmonize_expression_matrix(
        df,
        DataOrientation.GENE_X_SAMPLE,
    )

    assert result.columns[0] == "sample_id"

    assert list(result["sample_id"]) == [
        "S1",
        "S2",
    ]

    assert "TP53" in result.columns
    assert "KRAS" in result.columns


def test_unknown_orientation_raises_error():
    df = pd.DataFrame({
        "A": [1, 2],
        "B": [3, 4],
    })

    with pytest.raises(ValueError):
        Harmonizer.harmonize_expression_matrix(
            df,
            DataOrientation.UNKNOWN,
        )
