import pandas as pd

from src.analysis_engine.pca_analysis import PCAAnalysis


def test_pca_analysis_generates_plot_and_coordinates(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3", "S4"],
            "GENE1": [1.0, 2.0, 8.0, 9.0],
            "GENE2": [1.0, 2.0, 8.0, 9.0],
            "GENE3": [2.0, 3.0, 7.0, 8.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3", "S4"],
            "group": ["A", "A", "B", "B"],
        }
    )

    result = PCAAnalysis().generate(
        expression_df=expression_df,
        metadata_df=metadata_df,
        output_directory=str(tmp_path),
    )

    assert list(result.pca_dataframe.columns) == [
        "sample_id",
        "PC1",
        "PC2",
        "group",
    ]
    assert len(result.pca_dataframe) == 4
    assert len(result.explained_variance_ratio) == 2
    assert result.plot_path.endswith("pca_plot.png")
    assert (tmp_path / "pca_plot.png").exists()


def test_pca_analysis_requires_expression_sample_id(tmp_path):
    expression_df = pd.DataFrame(
        {
            "GENE1": [1.0, 2.0, 3.0],
            "GENE2": [2.0, 3.0, 4.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "group": ["A", "A", "B"],
        }
    )

    try:
        PCAAnalysis().generate(
            expression_df=expression_df,
            metadata_df=metadata_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "sample_id" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_pca_analysis_requires_metadata_group(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "GENE1": [1.0, 2.0, 3.0],
            "GENE2": [2.0, 3.0, 4.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
        }
    )

    try:
        PCAAnalysis().generate(
            expression_df=expression_df,
            metadata_df=metadata_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "group" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_pca_analysis_requires_two_samples(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1"],
            "GENE1": [1.0],
            "GENE2": [2.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1"],
            "group": ["A"],
        }
    )

    try:
        PCAAnalysis().generate(
            expression_df=expression_df,
            metadata_df=metadata_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "at least two samples" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_pca_analysis_requires_two_gene_columns(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "GENE1": [1.0, 2.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "group": ["A", "B"],
        }
    )

    try:
        PCAAnalysis().generate(
            expression_df=expression_df,
            metadata_df=metadata_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "at least two gene columns" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_pca_analysis_requires_numeric_gene_columns(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "GENE1": [1.0, 2.0, 3.0],
            "GENE2": ["low", "medium", "high"],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "group": ["A", "A", "B"],
        }
    )

    try:
        PCAAnalysis().generate(
            expression_df=expression_df,
            metadata_df=metadata_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "Non-numeric columns detected" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")
