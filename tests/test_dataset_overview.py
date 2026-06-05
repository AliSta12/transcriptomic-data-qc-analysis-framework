import pandas as pd

from src.analysis_engine.dataset_overview import DatasetOverview


def test_generates_dataset_overview():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "TP53": [1.0, 2.0, 3.0],
            "EGFR": [4.0, 5.0, 6.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "group": ["A", "A", "B"],
        }
    )

    overview = DatasetOverview()

    result = overview.generate(expression_df, metadata_df)

    assert result.sample_count == 3
    assert result.gene_count == 2
    assert result.group_count == 2
    assert result.group_distribution == {"A": 2, "B": 1}
    assert result.min_expression == 1.0
    assert result.max_expression == 6.0


def test_requires_sample_id_in_expression():

    expression_df = pd.DataFrame(
        {
            "TP53": [1.0, 2.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    overview = DatasetOverview()

    try:
        overview.generate(expression_df, metadata_df)
        assert False
    except ValueError:
        assert True


def test_requires_group_column():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "TP53": [1.0, 2.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
        }
    )

    overview = DatasetOverview()

    try:
        overview.generate(expression_df, metadata_df)
        assert False
    except ValueError:
        assert True


def test_requires_gene_columns():

    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    overview = DatasetOverview()

    try:
        overview.generate(expression_df, metadata_df)
        assert False
    except ValueError:
        assert True
